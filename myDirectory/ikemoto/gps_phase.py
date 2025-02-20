import math
import numpy as np
import sys
import csv

sys.path.append("/home/pi/TANE2025")
import time
import threading
from module import class_low_g_acc3
from module import class_motor
from module import class_gps
from phase import subthread


class GpsPhase:
    def __init__(self, low_g_acc3=None, motor=None, gps=None, subth=None):
        self.x, self.y = 100, 100
        self.last_x, self.last_y = 100, 100
        self.distance = 0
        self.stack_distance = 1
        self.stack_acc_diff = (
            170 * (10 ** (-6)) * math.sqrt(100) * 5
        )  # ADXL367: Low noise to 170 µg/√Hz, low_g_acc3_output_rate = 100 Hz, 調整用の係数を掛けている
        self.theta_nineaxis = 0
        self.theta_goal = 0
        self.theta_modify_past = 0
        self.theta_modify_sum = 0
        self.speed = 50
        self.speed_high = 50
        self.speed_low = 40
        self.duty_R = 0
        self.duty_L = 0
        self.turn_direction = "right"
        self.stack = False

        if low_g_acc3 == None:
            self.LowGAcc3 = class_low_g_acc3.LowGAcc3()  # class_low_g_acc3のインスタンスを生成
        else:
            self.LowGAcc3 = low_g_acc3.LowGAcc3()

        if motor == None:
            self.Motor = class_motor.Motor()  # class_motorのインスタンスを生成
        else:
            self.Motor = motor

        self.Nineaxis = self.Motor.geomag  # class_9axisのインスタンスを作成

        if gps == None:
            self.Gps = (
                class_gps.Gps()
            )  # class_GPSのインスタンスを生成（＆GPS取得し続けるサブスレッドを起動）
        else:
            self.Gps = gps

        self.latitude_goal = (
            self.Gps.goal_lati
        )  # class_gpsでcsvファイルから取得したゴール地点のGPS情報
        self.longitude_goal = self.Gps.goal_longi

        if subth == None:
            self.subth = subthread.Subthread(
                gps=self.Gps, motor=self.Motor
            )  # subthreadのインスタンスを作成
            self.subth.run()
        else:
            self.subth = subth

    def update_status(self):  # 各情報の更新
        self.x, self.y = self.Gps.getXY()  # xy座標
        self.distance = math.sqrt(self.x**2 + self.y**2)  # ゴールまでの距離
        self.Nineaxis.get_mag()  # 現在角度
        self.theta_nineaxis = self.Nineaxis.theta_absolute
        self.theta_goal = math.atan2(self.y, self.x) * 180 / math.pi + 180  # ゴール角度
        if self.theta_goal > 360:
            self.theta_goal = self.theta_goal - 360
        if self.theta_goal < 0:
            self.theta_goal = self.theta_goal + 360

    def duty(self, theta_target):  # 修正角度を計算
        Kp = 0.1
        Kd = 0.1
        Ki = 0.03
        duty_limit = 70

        self.update_status()

        if self.distance <= 6:
            self.speed = self.speed_low
        else:
            self.speed = self.speed_high

        theta_modify = theta_target - self.theta_nineaxis  # 比例項
        theta_modify_diff = theta_modify - self.theta_modify_past  # 微分項
        self.theta_modify_sum += theta_modify  # 積分項
        self.theta_modify_past = theta_modify

        if theta_modify > 180:
            theta_modify = theta_modify - 360
        elif theta_modify < -180:
            theta_modify = theta_modify + 360

        if self.theta_modify_sum > duty_limit:  # 積分項が吹っ飛ばないように
            self.theta_modify_sum = duty_limit
        elif self.theta_modify_sum < -duty_limit:
            self.theta_modify_sum = -duty_limit

        duty_diff = (
            Kp * theta_modify + Kd * theta_modify_diff + Ki * self.theta_modify_sum
        )
        duty_diff = min(max(duty_diff, -(100 - self.speed - 1)), 100 - self.speed - 1)
        self.duty_R, self.duty_L = self.speed + duty_diff, self.speed - duty_diff

        return self.duty_R, self.duty_L

    def reset_Ki(self):  # 積分項リセット
        self.theta_modify_sum = 0

    def run_main(self):
        self.duty(self.theta_goal)
        self.Motor.changeduty(self.duty_L, self.duty_R)

    def detect_stack(self):  # スタック判定
        self.stack_state = 0  # 判定用
        self.stack_state_acc = 0  # 判定用
        self.last_acc_x = self.LowGAcc3.acc_x
        self.last_acc_y = self.LowGAcc3.acc_y
        self.last_acc_z = self.LowGAcc3.acc_z

        while True:
            self.update_status()

            if (
                math.sqrt((self.x - self.last_x) ** 2 + (self.y - self.last_y) ** 2)
                <= self.stack_distance
            ):  # 動けてなかったらカウント
                self.stack_state += 1
            else:
                self.stack_state = 0
            if self.stack_state == 0:
                self.last_x, self.last_y = self.x, self.y
            elif self.stack_state >= 5:  # カウントが5以上ならスタック判定
                print("detect stack")
                self.stack = True

            # 加速度センサーの値をもとにスタック検知
            if (
                math.fabs(self.LowGAcc3.acc_x - self.last_acc_x) <= self.stack_acc_diff
                and math.fabs(self.LowGAcc3.acc_y - self.last_acc_y)
                <= self.stack_acc_diff
                and math.fabs(self.LowGAcc3.acc_z - self.last_acc_z)
                <= self.stack_acc_diff
            ):
                self.stack_state_acc += 1
            else:
                self.stack_state_acc = 0
            if self.stack_state_acc == 0:
                self.last_acc_x = self.LowGAcc3.acc_x
                self.last_acc_y = self.LowGAcc3.acc_y
                self.last_acc_z = self.LowGAcc3.acc_z
            elif self.stack_state_acc >= 5:
                print("detect stack from acc")
                self.stack = True

            time.sleep(2)  # 2秒ごとに判定

    def run_stack(self):
        self.reset_Ki()
        self.update_status()
        before_x, before_y = self.x, self.y

        while (
            math.sqrt((self.x - before_x) ** 2 + (self.y - before_y) ** 2)
            <= self.stack_distance
        ):
            if self.turn_direction == "right":
                print("escape to right")
                self.Motor.rotate(angle=100)
            elif self.turn_direction == "left":
                print("escape to left")
                self.Motor.rotate(angle=-100)

            self.update_status()
            before_x, before_y = self.x, self.y
            theta_straight = self.theta_nineaxis
            time_start = time.time()
            while (time.time() - time_start) < 1.5:
                self.duty(theta_straight)
                self.Motor.changeduty(self.duty_R, self.duty_L)
                time.sleep(0.1)
            self.Motor.changeduty(20, 20)
            time.sleep(1)
            self.Motor.changeduty(0, 0)

            if self.turn_direction == "right":
                self.turn_direction = "left"
            elif self.turn_direction == "left":
                self.turn_direction = "right"
            self.update_status()
            print(
                f"position ({before_x:5.2f}, {before_y:5.2f}) → ({self.x:5.2f}, {self.y:5.2f}) : distance = {(math.sqrt((self.x - before_x)**2 + (self.y - before_y)**2)):5.2f}"
            )

    def detect_goal(self, count):  # ゴール判定
        if count == 0:  # ゆっくり止まる
            print("maybe goal ({count}/3)")
            self.Motor.changeduty(35, 35)
            time.sleep(0.5)
            self.Motor.changeduty(20, 20)
            time.sleep(0.5)
            self.Motor.changeduty(0, 0)

        self.update_status()
        if self.distance < 2:  # ゴールまでの距離が2m以内なら
            print("maybe goal ({count}/3)")
            if count >= 3:  # かつ3回カウント済みならTrue
                print("detect goal")
                return True
            time.sleep(1)
            return self.detect_goal(count + 1)  # カウントを増やして再帰
        print("restart run")
        return False  # 3回カウントできなかったらFalse

    def run(self):
        self.subth.phase = 2

        thread = threading.Thread(target=self.detect_stack)
        thread.daemon = True
        thread.start()

        while True:
            time.sleep(0.1)
            self.run_main()

            self.update_status()
            if self.distance <= 3:
                if self.detect_goal(0):
                    return True
                self.stack = False  # ゴール判定のためにしばらく立ち止まるのでスタック判定されてしまうのを防ぐ

            if self.stack:  # detect_stackよりスタック判定
                self.Motor.changeduty(35, 35)
                time.sleep(0.5)
                self.Motor.changeduty(20, 20)
                time.sleep(0.5)
                self.Motor.changeduty(0, 0)
                self.run_stack()
                self.stack = False
                self.stack_state = 0

            print(
                f"x,y=({self.x:7.2f}, {self.y:7.2f}), stack_state = {self.stack_state}/5 , {self.stack}  \nmy_direc={self.theta_nineaxis:5.1f},  goal_direc={self.theta_goal:5.1f},  dutyL,R=({self.duty_L:5.1f}, {self.duty_R:5.1f})\n"
            )
            # print(f"lat,longi=({self.Gps.latitude:9.2f},{self.Gps.longitude:9.2f})\n")


def main():
    GPSPhase = GpsPhase()
    try:
        GPSPhase.run()  # PIDを開始
        GPSPhase.Motor.end()
    except KeyboardInterrupt:
        GPSPhase.Motor.changeduty(0, 0)
        GPSPhase.Motor.end()
        print("motor end")


if __name__ == "__main__":
    main()  # PIDを開始
