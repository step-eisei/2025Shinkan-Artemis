import sys

sys.path.append("/home/pi/TANE2025/")

from module.class_pressure import Pressure
from module.class_low_g_acc3 import LowGAcc3

import math
import time
import datetime
import csv

# ファイル名
filename = "/home/pi/TANE2025/record/test/fall_val_test_{0:%Y%m%d-%H%M%S}.csv".format(
    datetime.datetime.now()
)
with open(filename, "a") as f:
    writer = csv.writer(f)
    writer.writerow(
        ["time[s]", "pressure[hPa]", "acc_x[g]", "acc_y[g]", "acc_z[g]", "acc_norm[g]"]
    )

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
        time_list.append(time.time() - first_time)
        pressure_data_list.append(pressure_data)
        low_g_acc3_data_list.append(low_g_acc3_data)

        # データ出力
        with open(filename, "a") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    time.time() - first_time,
                    pressure_data,
                    low_g_acc3_data[0],
                    low_g_acc3_data[1],
                    low_g_acc3_data[2],
                    low_g_acc3_data[3],
                ]
            )

        # インターバル  0.1秒
        time.sleep(interval)
    except KeyboardInterrupt:
        break
    except:
        pass

# culc fall velocity from pressure data
fall_velocity_from_pressure_file_name = "/home/pi/TANE2025/record/test/fall_velocity_from_pressure_{0:%Y%m%d-%H%M%S}.csv".format(
    datetime.datetime.now()
)
with open(fall_velocity_from_pressure_file_name, "w") as f:
    writer = csv.writer(f)
    writer.writerow(["time", "pressure[hPa]", "fall_velocity[m/s]"])
    for i in range(len(time_list) - 1):
        hight = (pressure_data_list[i + 1] - pressure_data_list[i]) * 10
        fall_velocity = hight / (time_list[i + 1] - time_list[i])
        writer.writerow([time_list[i], pressure_data_list[i], fall_velocity])

# culc fall velocity from low_g_acc3 data
fall_velocity_from_low_g_acc3_file_name = "/home/pi/TANE2025/record/test/fall_velocity_from_low_g_acc3_{0:%Y%m%d-%H%M%S}.csv".format(
    datetime.datetime.now()
)
with open(fall_velocity_from_low_g_acc3_file_name, "w") as f:
    writer = csv.writer(f)
    writer.writerow(
        [
            "time",
            "acc_x[g]",
            "acc_y[g]",
            "acc_z[g]",
            "acc_norm[g]",
            "fall_velocity_x[m/s]",
            "fall_velocity_y[m/s]",
            "fall_velocity_z[m/s]",
            "fall_velocity_norm[m/s]",
        ]
    )

    fall_velocity_from_acc = [0, 0, 0]

    for i in range(len(time_list) - 1):
        for j in range(3):
            # 台形積分による数値積分
            if j == 2:
                fall_velocity_from_acc[i] += (
                    (
                        (low_g_acc3_data_list[i + 1][j] - 1)
                        + (low_g_acc3_data_list[i][j] - 1)
                    )
                    / 2
                    * 9.8
                    * (time_list[i + 1] - time_list[i])
                )
            else:
                fall_velocity_from_acc[i] += (
                    ((low_g_acc3_data_list[i + 1][j]) + (low_g_acc3_data_list[i][j]))
                    / 2
                    * 9.8
                    * (time_list[i + 1] - time_list[i])
                )

        writer.writerow(
            [
                time_list[i],
                low_g_acc3_data_list[i][0],
                low_g_acc3_data_list[i][1],
                low_g_acc3_data_list[i][2],
                low_g_acc3_data_list[i][3],
                fall_velocity_from_acc[i][0],
                fall_velocity_from_acc[i][1],
                fall_velocity_from_acc[i][2],
                math.sqrt(
                    fall_velocity_from_acc[i][0] ** 2
                    + fall_velocity_from_acc[i][1] ** 2
                    + fall_velocity_from_acc[i][2] ** 2
                ),
            ]
        )
