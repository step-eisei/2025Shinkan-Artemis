import sys

sys.path.append("/home/pi/TANE2025")
sys.path.append("/home/pi/TANE2025/module")
import datetime
import csv
import time
import math
from module import class_motor
from module import class_nicrom
from module import class_distance
from module import class_gps
from phase import subthread
from function.get_object_theta_and_proportion import get_object_theta_and_proportion


class Deploy:
    def __init__(self, motor=None, nicrom=None, dist_sens=None, gps=None, subth=None):
        if motor == None:
            self.motor = class_motor.Motor()
        else:
            self.motor = motor

        self.geomag = self.motor.geomag

        if nicrom == None:
            self.nicrom = class_nicrom.Nicrom()
        else:
            self.nicrom = nicrom

        if dist_sens == None:
            self.dist_sens = class_distance.Distance()
        else:
            self.dist_sens = dist_sens

        if gps == None:
            self.gps = class_gps.Gps()
        else:
            self.gps = gps

        if subth == None:
            self.subth = subthread.Subthread(distance=self.dist_sens, motor=self.motor)
            self.subth.run()
        else:
            self.subth = subth

        self.parachute_colour = [140, 170]

    def run(self, time_heat=3):
        self.subth.phase = 1

        print("heat start")
        self.nicrom.heat(t=time_heat)
        self.nicrom.end()
        print("end")

        time.sleep(1)

        for i in range(10):
            self.dist_sens.reading()
            if self.dist_sens.distance >= 20:
                print("capsule opened")
                self.subth.record(comment="open")
                break
            self.motor.changeduty(40, 40)
            self.subth.record(comment=f"duty-40-40")
            time.sleep(0.3)
            self.motor.changeduty(0, 0)
            self.subth.record(comment=f"duty-0-0")
        self.motor.changeduty(0, 0)
        self.subth.record(comment=f"duty-0-0")
        time.sleep(0.5)

        print("getup")
        self.motor.get_up()

        time.sleep(0.5)

        print("turn_to_goal")
        self.turn_to_goal()
        self.motor.get_up()

        phi = self.geomag.angle_to_gravity()
        try:
            angle, prop = get_object_theta_and_proportion(self.parachute_colour)
        except:
            angle = 0
            prop = 0
        if prop >= 2:
            print(f"detected parachute prop:{prop}, angle:{angle}")
            if phi <= 40:
                self.motor.rotate(90)
                self.subth.record(comment=f"rotate-{90}")
            else:
                print(f"upside down")
        else:
            print("did not detect parachute")

        self.motor.forward(50, 2)
        self.subth.record(comment=f"forward-50-2")
        self.turn_to_goal()

        self.subth.record(comment="deployment")
        print("deployment phase finish")

    def turn_to_goal(self):
        x, y = self.gps.calc_xy()
        theta_gps = math.atan2(y, x) * 180 / math.pi + 175

        print(f"goal_theta{theta_gps}")

        self.geomag.get_mag()
        self.theta_relative = self.motor.angle_difference(
            self.geomag.theta_absolute, theta_gps
        )
        print(f"theta_abslute{self.geomag.theta_absolute}")

        print(f"theta_relative{self.theta_relative}")

        self.motor.rotate(self.theta_relative * 0.8)
        self.subth.record(comment=f"rotate-{self.theta_relative * 0.8}")


def main():
    try:
        deploy_phase = Deploy()
        deploy_phase.run()
        deploy_phase.motor.end()
    except KeyboardInterrupt:
        deploy_phase.motor.end()
        print("\nInterrupted.")


if __name__ == "__main__":
    main()
