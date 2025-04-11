#!/usr/bin/env python3
import sys
import tty
import termios
import time
import random
import math
import csv

# 既存のモジュール読み込み（使用している環境に合わせてパスを設定）
sys.path.append("/home/pi/2025Shinkan-Artemis/module")
import RPi.GPIO as GPIO
import class_mag3
from class_mag3 import Mag3

# Motorクラス（元のコードをそのまま使用、必要に応じて調整）
class Motor:
    def __init__(self, pwm=100, rightIN1=36, rightIN2=38, leftIN1=40, leftIN2=37, geomag=None):
        self.rightIN1 = rightIN1
        self.rightIN2 = rightIN2
        self.leftIN1 = leftIN1
        self.leftIN2 = leftIN2
        
        if geomag is None:
            try:
                with open("/home/pi/2025Shinkan-Artemis/prep/calibration_geomag.csv", "r") as f:
                    reader = csv.reader(f)
                    line = [row for row in reader]
                    rads = [float(line[1][i]) for i in range(3)]
                    aves = [float(line[2][i]) for i in range(3)]
            except:
                rads = [1.0, 1.0, 1.0]
                aves = [0.0, 0.0, 0.0]
            self.geomag = class_mag3.Mag3(True, rads, aves)
        else:
            self.geomag = geomag
        self.geomag.calibrated = True
        
        self.duty_R_now = -1
        self.duty_L_now = -1

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.rightIN1, GPIO.OUT)
        GPIO.setup(self.rightIN2, GPIO.OUT)
        GPIO.setup(self.leftIN1, GPIO.OUT)
        GPIO.setup(self.leftIN2, GPIO.OUT)
        self.pwms = {}
        self.pwms["rightIN1"] = GPIO.PWM(self.rightIN1, pwm)
        self.pwms["rightIN2"] = GPIO.PWM(self.rightIN2, pwm)
        self.pwms["leftIN1"] = GPIO.PWM(self.leftIN1, pwm)
        self.pwms["leftIN2"] = GPIO.PWM(self.leftIN2, pwm)

        self.pwms["rightIN1"].start(0)
        self.pwms["rightIN2"].start(0)
        self.pwms["leftIN1"].start(0)
        self.pwms["leftIN2"].start(0)

    def changeduty(self, duty_R, duty_L):
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

# キーボード入力を1文字取得するための関数（rawモード）
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def main():
    # Motorクラスのインスタンス作成
    motor = Motor()
    print("リモコンモード開始")
    print("操作方法:")
    print("  w : 前進")
    print("  s : 後進")
    print("  a : 左旋回")
    print("  d : 右旋回")
    print("  Space: 停止")
    print("  q : 終了")

    # ここではPWMの duty 値をあらかじめ指定（必要に応じて調整可能）
    duty_value = 20

    try:
        while True:
            key = getch()  # キー入力を1文字取得
            # 各キーに対応したモーター操作を実施
            if key == "w":
                print("前進")
                motor.changeduty(duty_R=duty_value, duty_L=duty_value)
            elif key == "s":
                print("後進")
                motor.changeduty(duty_R=-duty_value, duty_L=-duty_value)
            elif key == "a":
                print("左旋回")
                motor.changeduty(duty_R=-duty_value, duty_L=duty_value)
            elif key == "d":
                print("右旋回")
                motor.changeduty(duty_R=duty_value, duty_L=-duty_value)
            elif key == " ":
                print("停止")
                motor.changeduty(duty_R=0, duty_L=0)
            #elif key == "q":
            #    print("終了します")
            #    break

            # 小休止を入れて入力ループを安定させる
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt")
    finally:
        motor.changeduty(0, 0)
        motor.end()
        print("モーターを停止しました")

if __name__ == "__main__":
    main()
