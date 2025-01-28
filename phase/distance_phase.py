# 距離フェーズ
import sys
sys.path.append("/home/pi/TANE2025/")
from module import class_distance
from module import class_motor
from function.get_object_theta_and_proportion import get_object_theta_and_proportion
from phase import subthread
import time
import math
import numpy as np
import cv2

class DistancePhase:
    
    def __init__(self, distance=None, motor=None, subth=None):
        if distance == None: self.distance = class_distance.Distance()
        else:                self.distance = distance

        if motor == None:    self.motor = class_motor.Motor()
        else:                self.motor = motor
        
        if subth == None:
            self.subth = subthread.Subthread(distance=self.distance, motor=self.motor)
            self.subth.run()
        else:                self.subth = subth

        self.cone_colour = [160, 20]


    def run(self):
        self.subth.phase = 4
        duty = 50
        i = 0
        
        self.camera = cv2.VideoCapture(-1, cv2.CAP_V4L2)
        self.camera.set(cv2.CAP_PROP_EXPOSURE, 5)
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        success = False
        for i in range(100):
            success, _ = self.camera.read()
            if success: break
            time.sleep(0.1)
            print("waiting camera..........\n")
        
        success, _ = self.camera.read()
        if not success:
            print("camera.read fail")
            return False

        while True:
            print("read")
            self.distance.reading()
            distance = self.distance.distance # get distance
            print(f"distance:{distance}")
            for m in range(20):
                _, image = self.camera.read()
            image = cv2.flip(image, -1)
            _, prop = get_object_theta_and_proportion(self.cone_colour, image)

            if(distance > 2 and distance < 200 and prop > 10):
                i = 0
                print("detected")
                if(distance < 20 and prop > 20): 
                    self.motor.forward(duty_target=30, t=0.8)
                    self.subth.record(comment="distanceend", coneangle=0)
                    print("finished")
                    self.camera.release()
                    return True
                else: 
                    print("forward")
                    self.subth.record(comment="approachtocone", coneangle=0)
                    self.motor.forward(duty_target=duty, t=distance/30)#距離に応じて前進
                    self.motor.changeduty(0,0)
            else:
                if(i <= 19):#その場で旋回してコーンを探す
                    print("rotate")
                    angle = 18*(i+1)
                    self.subth.record(comment="rotateforcone")
                    if angle > 180:
                        angle = angle - 360
                    if(i%2 == 0):
                        self.motor.rotate(angle) # 左に旋回
                    else: 
                        self.motor.rotate(-angle) # 右に旋回
                    i += 1
                else:# 現在位置から直進して離れてフェーズを離れる
                    self.motor.forward(duty_target=40, t=5)
                    self.subth.record(comment="notdistancephase")
                    time.sleep(5)
                    self.motor.changeduty(0,0)
                    self.camera.release()
                    return False

def main():
    try:
        distance = class_distance.Distance()
        motor = class_motor.Motor()
        subth = subthread.Subthread(distance=distance, motor=motor)
        subth.run()
        distance_phase = DistancePhase(distance=distance,motor=motor,subth=subth)
        distance_phase.run()
        distance_phase.motor.end()
    except KeyboardInterrupt:
        distance_phase.motor.end()
        distance_phase.camera.release()
        print("\nInterrupted.")
    
if __name__ == "__main__":
    main()