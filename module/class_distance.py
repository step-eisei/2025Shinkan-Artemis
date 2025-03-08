#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import RPi.GPIO as GPIO
import numpy as np

class Distance:
    
    def __init__(self,TRIG=11,ECHO=13):
        self.TRIG = TRIG
        self.ECHO = ECHO
        self.distance = -1

    def reading(self):

        distance_data = []

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)

        #データ取得 5回値を取ってその平均を取る
        cycle=1
        error=0
        error_count = 0
        while(cycle<6):
            error = 0
            GPIO.setup(self.TRIG,GPIO.OUT)
            GPIO.setup(self.ECHO,GPIO.IN)
            GPIO.output(self.TRIG, GPIO.LOW)
            time.sleep(0.3)
            GPIO.output(self.TRIG, True)
            time.sleep(0.00001)
            GPIO.output(self.TRIG, False)
            debugtime = time.time()
            signaloff = time.time()
            while GPIO.input(self.ECHO) == 0:
                signaloff = time.time()
                if(signaloff-debugtime>1):
                    GPIO.output(self.TRIG, False)
                    print("Error. timepass is too long.")
                    error=1
                    error_count+=1
                    break
            if(error==0):
                while GPIO.input(self.ECHO) == 1:
                    signalon = time.time()
                timepassed = signalon - signaloff
                distance = timepassed * 17000
                distance_data.append(distance)
                cycle+=1
            if(error_count == 5):
                self.distance = 10000
                return -1


        #外れ値を除外
        #print("")
        #print(distance_data)
        ave = np.mean(distance_data)
        max = 0
        num = 0
        for i in range(len(distance_data)):
            if((ave-distance_data[i])**2 > max):
                num = i
                max = (ave-distance_data[i])**2
        distance_data = np.delete(distance_data, num)
        #print(distance_data)
        self.distance = np.mean(distance_data)
        print(distance)
        
        GPIO.cleanup([self.TRIG, self.ECHO])


def main():
    try:
        while(True):
            distance = Distance()
            distance.reading()
            print(distance.distance)
            time.sleep(1)
        
    except KeyboardInterrupt:
            GPIO.output(distance.TRIG, False)
            GPIO.cleanup()

if __name__ == "__main__":
    main()
