import sys
sys.path.append("/home/pi/TANE2025/module")
import RPi.GPIO as GPIO
import time
import random
import math
#import class_mag3
import class_mag3
import csv
# right = A, left = B

class Motor():
    def __init__(self, pwm=100, rightIN1=16, rightIN2=18, leftIN1=19, leftIN2=21, geomag=None):#19 21 16 18
        self.rightIN1 = rightIN1
        self.rightIN2 = rightIN2
        self.leftIN1 = leftIN1
        self.leftIN2 = leftIN2
        if geomag == None:
            with open ('/home/pi/TANE2025/prep/calibration_geomag.csv', 'r') as f :# goal座標取得プログラムより取得
                reader = csv.reader(f)
                line = [row for row in reader]
                rads = [float(line[1][i]) for i in range(3)]
                aves = [float(line[2][i]) for i in range(3)]
            f.close()
            self.geomag = class_mag3.Nineaxis(True, rads, aves)
        else: self.geomag = geomag
        self.geomag.calibrated = True
        self.duty_R_now = -1
        self.duty_L_now = -1
        
        GPIO.setmode(GPIO.BOARD) # GPIOnを指定するように設定
        GPIO.setup(self.rightIN1, GPIO.OUT)
        GPIO.setup(self.rightIN2, GPIO.OUT)
        GPIO.setup(self.leftIN1, GPIO.OUT)
        GPIO.setup(self.leftIN2, GPIO.OUT)
        self.pwms = {}
        self.pwms["rightIN1"] = GPIO.PWM(self.rightIN1, pwm) # pin, Hz
        self.pwms["rightIN2"] = GPIO.PWM(self.rightIN2, pwm) # pin, Hz
        self.pwms["leftIN1"] = GPIO.PWM(self.leftIN1, pwm) # pin, Hz
        self.pwms["leftIN2"] = GPIO.PWM(self.leftIN2, pwm) # pin, Hz
        
        self.pwms["rightIN1"].start(0)
        self.pwms["rightIN2"].start(0)
        self.pwms["leftIN1"].start(0)
        self.pwms["leftIN2"].start(0)
    
    def changeduty(self, duty_R, duty_L):
        #duty_R = duty_R * 1.2
        if duty_R > 0:
            self.pwms["rightIN1"].ChangeDutyCycle(abs(duty_R))
            self.pwms["rightIN2"].ChangeDutyCycle(0)
        elif duty_R < 0:
            self.pwms["rightIN1"].ChangeDutyCycle(0)
            self.pwms["rightIN2"].ChangeDutyCycle(abs(duty_R))
        else:
            self.pwms["rightIN1"].ChangeDutyCycle(0)
            self.pwms["rightIN2"].ChangeDutyCycle(0)

        if duty_L > 0:
            self.pwms["leftIN1"].ChangeDutyCycle(abs(duty_L))
            self.pwms["leftIN2"].ChangeDutyCycle(0)
        elif duty_L < 0:
            self.pwms["leftIN1"].ChangeDutyCycle(0)
            self.pwms["leftIN2"].ChangeDutyCycle(abs(duty_L))
        else:
            self.pwms["leftIN1"].ChangeDutyCycle(0)
            self.pwms["leftIN2"].ChangeDutyCycle(0)
        self.duty_R_now = duty_R
        self.duty_L_now = duty_L

    def currentblock(self, duty_R, duty_L):
        # prevent Overcurrent
        if(duty_R != 0 and self.duty_R_now == 0): duty_R = 5
        else: duty_R = self.duty_R_now
        if(duty_L != 0 and self.duty_L_now == 0): duty_L = 5
        else: duty_L = self.duty_L_now
        self.changeduty(duty_R, duty_L)
        time.sleep(1)

    def forward(self, duty_target, t, duty_R=-1, duty_L=-1, duty_increment=5, time_sleep_per_loop=0.1):
        if duty_R != -1:
            duty_target = (duty_R + duty_L) /2
        else:
            duty_R = duty_target
            duty_L = duty_target
        epoch = int(abs(duty_target) / duty_increment)
        for i in range(epoch):
            r = int(duty_R * (i+1)/epoch)
            l = r = int(duty_L * (i+1)/epoch)
            self.changeduty(r, l)
            time.sleep(time_sleep_per_loop)
        
        self.changeduty(duty_R, duty_L)

        time.sleep(t)

        for i in range(epoch):
            r = int(duty_R * (epoch - i - 1) / epoch)
            l = int(duty_L * (epoch - i - 1) / epoch)
            self.changeduty(r, l)
            time.sleep(time_sleep_per_loop)
        
        self.changeduty(0, 0)

    def angle_difference(self, from_angle, to_angle):
        angle = to_angle-from_angle
        if(angle<-180): return angle+360
        elif(angle>180): return angle-360
        return angle
    
    def rotate(self, angle, duty=28, threshold=3.0):
        self.geomag.get_mag()
        angle_new = self.geomag.theta
        if angle_new > 180: angle_new -=360
        if(angle<-180): return angle+360
        elif(angle>180): return angle-360
        angle_diff = angle
        angle_target = angle_new + angle
        if angle_target > 180:
            angle_target -= 360
        elif angle_target < -180:
            angle_target += 360
        
        time_const = 0.008
        total = 10

        print(f"target:{angle_target}")

        try:
            for i in range(total):
                if angle_diff > 0:
                    self.changeduty(duty_R=-duty, duty_L=duty)
                else:
                    self.changeduty(duty_R=duty, duty_L=-duty)
                
                sleep_time = time_const * min(abs(angle_diff),20)

                time.sleep(sleep_time)
                self.changeduty(0,0)
                time.sleep(0.5)

                angle_old = angle_new
                self.geomag.get_mag()
                angle_new = self.geomag.theta
                if angle_new > 180: angle_new -=360

                angle_changed = self.angle_difference(angle_old, angle_new)
                angle_diff = self.angle_difference(angle_new, angle_target)
                
                overshoot = abs(angle_changed)-abs(angle_diff)
                duty = duty - int(overshoot/10)
                duty = min(max(duty, 10),50)
                print(f"now:{angle_new}")
                print(f"diff:{angle_diff}")
                print("")

                if -threshold < angle_diff < threshold:
                    break
            print(f"now   :{angle_new}")
            print(f"diff  :{angle_diff}")
        except KeyboardInterrupt:
            self.changeduty(0,0)
            print("\nKeyboardInterrupt")
        
        print(f"count :{i}")
        self.changeduty(0,0)
    
    def rotate_pid(self, angle, threshold=3.0):
        P = 0.1
        I = 0.08
        D = 0.5

        self.geomag.get_mag()
        angle_new = self.geomag.theta
        if angle_new > 180: angle_new -=360
        angle_diff = angle
        angle_target = angle_new + angle
        if angle_target > 180:
            angle_target -= 360
        elif angle_target < -180:
            angle_target += 360

        duty = (P * angle)
    
    def stack(self, duty_R=30, duty_L=30):
        self.geomag.get_mag()
        theta_stack = self.geomag.theta
        while True:
            self.geomag.get_mag()
            theta_past = self.geomag.theta
            self.rotate(90, threshold=20)
            self.forward(duty_R=random.randint(int(duty_R/2), duty_R), duty_L=random.randint(int(duty_L/2), duty_L), time_sleep=0.05, tick_dutymax=5)
            time.sleep(2)
            self.changeduty(0, 0)
            time.sleep(0.5)
            self.geomag.get_mag()
            theta_now = self.geomag.theta
            if (self.angle_difference(theta_past, theta_now)<10): print("stack")
            else: break
        self.geomag.get_mag()
        self.rotate(self.angle_difference(self.geomag.theta,theta_stack)+90)
    
    def get_up(self):
        duty = 40

        for i in range(100):
            angle = self.geomag.angle_to_gravity()
            if angle >= 20:
                duty = int(angle*0.8)
                if angle <= 40:
                    duty = int(angle*0.5)
                duty = max(min(duty, 50),10)
                self.changeduty(duty, duty)
                time.sleep(0.01)
            else:
                break
        
        self.changeduty(5, 5)
        time.sleep(0.5)
        self.changeduty(0, 0)
        time.sleep(1)
        #self.changeduty(10, 10)
        #time.sleep(0.5)

    def end(self):
        self.pwms["rightIN1"].stop()
        self.pwms["rightIN2"].stop()
        self.pwms["leftIN1"].stop()
        self.pwms["leftIN2"].stop()
        GPIO.output(self.rightIN1, False)
        GPIO.output(self.rightIN2, False)
        GPIO.output(self.leftIN1, False)
        GPIO.output(self.leftIN2, False)
        GPIO.cleanup()


def main():
    t = 3
    duty = 30
    try:
        print("setup")
        motor = Motor()

        # motor.rotate(40, threshold=1.0)
        # return 

        
        args = sys.argv
        duty = 50
        t = 8
        if len(args) >= 2:
            duty = int(args[1])
            if len(args) >= 3:
                t = int(args[2])
        motor.forward(duty, t)
        print("stop")
        motor.changeduty(0, 0)
        

        # print("forward fin.\nreverse start")
        # motor.forward(-duty, -duty, 0.05, tick_dutymax=5)
        # time.sleep(t)
        
        # print("stop")
        # motor.changeduty(0, 0)
        # time.sleep(t)
        # print("reverse fin.")
        
        #motor.rotate(angle=90)
        # モータ初期化
        motor.end()
        print("finish")

    except KeyboardInterrupt:
        motor.end()
        print("\nInterrupted")

if __name__ == "__main__":
    print("main")
    main()
