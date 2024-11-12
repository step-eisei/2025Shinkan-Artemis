import time
import csv
import numpy as np
import sys
sys.path.append('/home/stepeisei/TANE2025/module/')
import class_gps

GPS = class_gps.Gps()

try:
    print("===== gps data update =====")
    while True:
        latitude = GPS.latitude  #class_GPS内で更新されたlatitudeを代入
        longitude = GPS.longitude  #class_GPS内で更新されたlongitudeを代入
        print(f"latitude = {latitude:10.6f},longitude = {longitude:10.6f}")
        time.sleep(1.0)

except KeyboardInterrupt:
    print("===== save goal poit =====")
    # 10個のデータの平均値をゴール座標とする．
    sum_latitude = 0
    sum_longitude = 0

    for i in range(10):
        latitude = GPS.latitude  #class_GPS内で更新されたlatitudeを代入
        longitude = GPS.longitude  #class_GPS内で更新されたlongitudeを代入
        print(f"{i+1:2}:latitude = {latitude:10.6f},longitude = {longitude:10.6f}")
        sum_latitude += latitude
        sum_longitude += longitude
        time.sleep(2)
    
    goal_latitude = sum_latitude/10
    goal_longitude = sum_longitude/10

    print(f"setting goal {goal_latitude}, {goal_longitude}")

    with open('/home/pi/TANE2025/prep/goal.csv',mode='w',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["goal_latitude", "goal_longitude"])

    with open('/home/pi/TANE2025/prep/goal.csv',mode='a',newline='') as f:
            writer = csv.writer(f)
            writer.writerow([goal_latitude, goal_longitude]) 
