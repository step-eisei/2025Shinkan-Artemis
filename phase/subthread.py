# サブスレッド処理
import sys
sys.path.append("/home/pi/TANE2025")
from module import class_pressure
from module import class_gps
from module import class_distance
from module import class_motor
import datetime
import time
import threading
import csv
import serial
from struct import *

class Subthread:
    
    def __init__(self, pressure=None, gps=None, distance=None, motor=None, old_goal_or_new_goal="old_goal"):
        if pressure == None: self.pressure = class_pressure.Pressure()
        else:                self.pressure = pressure
        if motor == None:    self.motor  = class_motor.Motor()
        else:                self.motor = motor
        self.geomag = self.motor.geomag
        if gps == None:      self.gps = class_gps.Gps()
        else:                self.gps = gps
        if distance == None: self.distance = class_distance.Distance()
        else:                self.distance = distance

        self.time_start = time.time()
        self.phase = 0
        self.phaselist = ["land", "deployment", "gps", "camera", "distance"]
        if old_goal_or_new_goal == "new_goal":
            self.phaselist = ["land", "deployment", "gps", "camera", "ball", "goal"]
        
        DIFF_JST_FROM_UTC = 9
        jp_time = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        self.recordname = '/home/pi/TANE2025/record/record_' + str(jp_time).replace(' ', '_').replace(':', '-').replace('.', '_') + '.csv'
        with open(self.recordname, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["comment", "time", "phase", "baro", "latitude", "longitude", "duty_R", "duty_L", "theta", "cornangle", "distance"])
    
    def record(self, loop=False, comment="threading", coneangle=None):
        if(loop):
            COM = '/dev/serial0'
            self.ser = serial.Serial(COM, 9600) 
        while(True):
            time_now = time.time()
            with open(self.recordname, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([comment, time_now-self.time_start, self.phaselist[self.phase], self.pressure.pressure, self.gps.latitude, self.gps.longitude, self.motor.duty_R_now, self.motor.duty_L_now, self.geomag.theta_absolute, coneangle, self.distance.distance])
            #print("regularly record.")
            print(f"{self.gps.latitude:12.9f}, {self.gps.longitude:12.9f}") #GPSデータダウンリンク試験とかで，機体が送信した情報を見せるため

            
            
            if(loop): 
                data=str(self.gps.latitude)+","+str(self.gps.longitude)
                data = data.encode()
                data = data + b'\n'
                self.ser.write(data)
                # time.sleep(3)
            else:
                break
            
        if(loop):self.ser.close()
    
    def run(self):
        self.thread = threading.Thread(target=self.record, args={True})
        self.thread.setDaemon(True)
        print("threading start.")
        self.thread.start()

def main():
    try:
        subthread = Subthread()
        subthread.run()
        while True:
            print("processing...")
            time.sleep(10)
    except KeyboardInterrupt:
        subthread.motor.end()
        print("\nInterrupted.")

if __name__ == "__main__":
    main()
