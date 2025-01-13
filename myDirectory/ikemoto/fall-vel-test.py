import sys
sys.path.append("/home/pi/TANE2025/")

from module.class_pressure import Pressure
from module.class_low_g_acc3 import LowGAcc3

import time
import datetime
import csv

# ファイル名
filename = "/home/pi/TANE2025/record/test/fall_val_test_{0:%Y%m%d-%H%M%S}.csv".format(datetime.datetime.now())

# データ取得間隔
interval = 0.1

pressure = Pressure()
pressure_data_list = []
low_g_acc3 = LowGAcc3()
low_g_acc3_data_list = []

first_time = time.time()
time_list = []

while True:
    try:
        # データ取得
        pressure.read()
        pressure_data = pressure.pressure
        low_g_acc3_data = low_g_acc3.get_acc_raw()

        # データ保存
        time_list.append(time.time()-first_time)
        pressure_data_list.append(pressure_data)
        low_g_acc3_data_list.append(low_g_acc3_data)

        # データ出力
        with open(filename, "a") as f:
            writer = csv.writer(f)
            writer.writerow([time.time()-first_time, pressure_data, low_g_acc3_data])

        # インターバル  0.1秒
        time.sleep(interval)
    except KeyboardInterrupt:
        break
    except:
        pass

# culc fall velocity from pressure data
fall_velocity_from_pressure_file_name = "/home/pi/TANE2025/record/test/fall_velocity_from_pressure_{0:%Y%m%d-%H%M%S}.csv".format(datetime.datetime.now())
with open(fall_velocity_from_pressure_file_name, "w") as f:
    writer = csv.writer(f)
    writer.writerow(["time", "pressure", "fall_velocity[m/s]"])
    for i in range(len(time_list)-1):
        hight = (pressure_data_list[i+1] - pressure_data_list[i]) * 10
        fall_velocity = hight / (time_list[i+1] - time_list[i])
        writer.writerow([time_list[i], pressure_data_list[i], fall_velocity])

# culc fall velocity from low_g_acc3 data
fall_velocity_from_low_g_acc3_file_name = "/home/pi/TANE2025/record/test/fall_velocity_from_low_g_acc3_{0:%Y%m%d-%H%M%S}.csv".format(datetime.datetime.now())
with open(fall_velocity_from_low_g_acc3_file_name, "w") as f:
    writer = csv.writer(f)
    writer.writerow(["time", "low_g_acc3", "fall_velocity[m/s]"])

    fall_velocity_from_acc = 0
    for i in range(len(time_list)-1):
        fall_velocity_from_acc += ((low_g_acc3_data_list[i+1][3]-1)+(low_g_acc3_data_list[i][3]-1))/2 * 9.8 * (time_list[i+1] - time_list[i])
        writer.writerow([time_list[i], low_g_acc3_data_list[i], fall_velocity_from_acc])