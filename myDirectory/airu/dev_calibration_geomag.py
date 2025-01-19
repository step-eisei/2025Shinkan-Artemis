
import sys

import time
import datetime
import csv

from class_mag3 import Mag3
from class_motor import Motor

def percentpick(listdata, p):
        n = int(len(listdata) *p/100)
        listdata = sorted(listdata) # 昇順
        min = listdata[n-1]
        max = listdata[len(listdata)-n]
        return max, min

motor = Motor(geomag=Mag3())

duty = 15
p = 5
time_all = 10
duration = 0.01

t = 0
mag_list = []
motor.changeduty(-duty, duty)
while t <= time_all:
    try:
        motor.geomag.get_mag()
        mag_list.append((motor.geomag.mag_x, motor.geomag.mag_y, motor.geomag.mag_z))
        print('Magnetometer (gauss): ({0:10.3f}, {1:10.3f}, {2:10.3f})'.format(motor.geomag.mag_x, motor.geomag.mag_y, motor.geomag.mag_z) + f"t:{t}")
        print('')
    except:
         print("error") 
    time.sleep(duration)
    t+=duration

motor.changeduty(0,0)
motor.end()

magxs = [mag_list[i][0] for i in range(len(mag_list))]
magys = [mag_list[i][1] for i in range(len(mag_list))]
magzs = [mag_list[i][2] for i in range(len(mag_list))]

# csv save
DIFF_JST_FROM_UTC = 9
jp_time = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
recordname = 'mag/mag_' + str(jp_time).replace(' ', '_').replace(':', '-').replace('.', '_') + '.csv'
with open(recordname, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["magx", "magy", "magz"])
    writer.writerows(mag_list)

# 最大値，最小値の算出
Xmax, Xmin = percentpick(magxs, p)
Ymax, Ymin = percentpick(magys, p)
Zmax, Zmin = percentpick(magzs, p)

maxs = [Xmax, Ymax, Zmax]
mins = [Xmin, Ymin, Zmin]

motor.geomag.rads = [(maxs[i] - mins[i])/2 for i in range(3)]
motor.geomag.aves = [(maxs[i] + mins[i])/2 for i in range(3)]

motor.geomag.calibrated = True

print(f"rads:{motor.geomag.rads}")
print(f"aves:{motor.geomag.aves}")

with open('/home/pi/TANE2025/myDirectory/airu/calibration_geomag.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(["x, y, z"])
    writer.writerows([motor.geomag.rads, motor.geomag.aves])

mag = Mag3(True, motor.geomag.rads, motor.geomag.aves)
maglist = []

while True:
    try:
        mag.get_mag()
        maglist.append([mag.mag_x, mag.mag_y, mag.mag_z])
        print('Magnetometer (gauss): ({0:10.3f}, {1:10.3f}, {2:10.3f})'.format(mag.mag_x, mag.mag_y, mag.mag_z))
        print(mag.theta_absolute)
        time.sleep(0.1)
    except KeyboardInterrupt:
        print(f"\nrads:{motor.geomag.rads}")
        print(f"aves:{motor.geomag.aves}")
        break
