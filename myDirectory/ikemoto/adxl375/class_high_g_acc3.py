# -*- coding: utf-8 -*-
# 使用センサー: ADXL375
import codecs
from collections import deque
import csv

import datetime
import math
import time

import numpy as np
import spidev
import threading


class HighGAcc3:
    def __init__(self, calibrated=False, offset_list = [[0 for _ in range(10)] for _ in range(3)]):
        self.calibrated = calibrated
        self.offset_list = offset_list
        self.acc_x = 0
        self.acc_y = 0
        self.acc_z = 0
        self.acc_norm = 0

        # 初期設定
        self.spi = spidev.SpiDev()
        self.spi.open(0,0)
        self.spi.mode = 3  # このデバイスはSPI mode3で動作
        self.spi.max_speed_hz = 5000000

        # self.spi.xfer2([0x2C, 0x0F]) # output data rate 3200 Hz
        self.spi.xfer2([0x31, 0x0B])
        self.spi.xfer2([0x2C, 0x0F])
        self.spi.xfer2([0x2D, 0x08]) # 測定スタート

        time.sleep(0.5)

        high_g_thread = threading.Thread(target=self.record_high_g)
        high_g_thread.daemon = True
        high_g_thread.start()

    def apply_offset_list(self, offset_list, x, y, z):
        xyz_array = np.array([x, y, z])
        for i, offset in enumerate(offset_list):
            offset_array = np.array(offset)
            xyz_array[i] -= np.mean(offset_array)

        return tuple(xyz_array)
    
    def get_calibration_data(self):
        calibration_iter = 10
        for _ in range(calibration_iter):
            x, y, z = self.get_acc_raw()
            self.offset_list[0].append(x)
            self.offset_list[1].append(y)
            self.offset_list[2].append(z-1.0)
        
        print(self.offset_list)

        self.calibrated = True

    def hosuu_to_normal(self, num):
        if num > 32768:
            num -= 65536
        return num
    
    def check_out_range(self, x, y, z):
        return x >= 200 or x <= -200 or y >= 200 or y <= -200 or z >= 200 or z <= -200
    
    def get_acc_raw(self):
        # 単位はGです
        try:
            #データ読み込み
            x_data_list = self.spi.xfer2([0xc0|0x32, 0x00, 0x00])
            y_data_list = self.spi.xfer2([0xc0|0x34, 0x00, 0x00])
            z_data_list = self.spi.xfer2([0xc0|0x36, 0x00, 0x00])
            x_data = x_data_list[1] | (x_data_list[2] << 8)
            y_data = y_data_list[1] | (y_data_list[2] << 8)
            z_data = z_data_list[1] | (z_data_list[2] << 8)
        
            # 2の補数を10進に変換
            x_data = self.hosuu_to_normal(x_data)
            y_data = self.hosuu_to_normal(y_data)
            z_data = self.hosuu_to_normal(z_data)

            # 加速度に変換（Dレンジ ±200g）
            x_data = x_data * 200 / 0xFFF
            y_data = y_data * 200 / 0xFFF
            z_data = z_data * 200 / 0xFFF
    
            self.acc_x = x_data
            self.acc_y = y_data
            self.acc_z = z_data
            self.acc_norm = math.sqrt(x_data**2 + y_data**2 + z_data**2)
            
        except IOError as e:
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
        
        return x_data, y_data, z_data, math.sqrt(x_data**2+y_data**2+z_data**2)

    def get_acc_calibrated(self):
        if not self.calibrated:
            print("set calibration data!")
            return
        
        x, y, z = self.get_acc_raw()
        x, y, z = self.apply_offset_list(self.offset_list, x, y, z)

        self.acc_x = x
        self.acc_y = y
        self.acc_z = z
        self.acc_norm = math.sqrt(x**2 + y**2 + z**2)

        return x, y, z, math.sqrt(x**2 + y**2 + z**2)
    
    def record_high_g(self):
        HIGH_G_THRESHOLD = 50
        QUEUE_SIZE = 50
        time_acc_queue = deque(maxlen=QUEUE_SIZE)
        high_g_detected_index = None  # HIGH_G検出位置

        def log_high_g_event(queue):
            now = datetime.datetime.now()
            filename = "/home/pi/TANE2025/record/high_g_log_{0:%Y%m%d-%H%M%S}.csv".format(now)
            with open(filename, "w", newline="") as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow(["time", "acc_x", "acc_y", "acc_z", "acc_norm"])
                for time_acc in queue:
                    csv_writer.writerow(time_acc)
                    print(time_acc)

        while True:
            acc_x, acc_y, acc_z, acc_norm = self.get_acc_raw()
            if self.check_out_range(acc_x, acc_y, acc_z):
                continue
            now = datetime.datetime.now()
            time_acc_queue.append([now, acc_x, acc_y, acc_z, acc_norm])

            # 高G検出でインデックスを記録
            if acc_norm > HIGH_G_THRESHOLD and high_g_detected_index is None:
                print("High G detected!")
                high_g_detected_index = len(time_acc_queue) - 1

            # 中心に高Gデータが来るように待機する
            if high_g_detected_index is not None and len(time_acc_queue) == QUEUE_SIZE:
                center_index = QUEUE_SIZE // 2
                if high_g_detected_index == center_index:
                    log_high_g_event(time_acc_queue)
                    high_g_detected_index = None  # リセット
                else:
                    high_g_detected_index -= 1  # センターシフトのためインデックス修正


def main():
    # logの設定
    # csv log file ready
    fmt_name = "/home/pi/TANE2025/record/test/acc_logs_ADXL375_{0:%Y%m%d-%H%M%S}.csv".format(datetime.datetime.now())
    f_acc_logs = codecs.open(fmt_name, mode='w', encoding="utf-8")

    header_value = u"yyyy-mm-dd hh:mm:ss.mmmmmm,x[g],y[g],z[g],norm[g]"
    f_acc_logs.write(header_value+"\n")
    
    low_g_acc = HighGAcc3()
    
    try:
        while True:
            out_x, out_y, out_z, norm = low_g_acc.get_acc_raw()
            if low_g_acc.check_out_range(out_x, out_y, out_z):
                continue
            now = datetime.datetime.now()
            f_acc_logs.write(f'{now},{out_x},{out_y},{out_z},{math.sqrt(out_x**2 + out_y**2 + out_z**2)}\n')
            print(f"{out_x}, {out_y}, {out_z}, {norm}")
            time.sleep(0.1)
    except:
        f_acc_logs.close()

def test_calib():
    low_g_acc = HighGAcc3(save_log_flag = True)
    low_g_acc.get_calibration_data()

    out_x, out_y, out_z, norm = low_g_acc.get_acc_calibrated()
    print(f"{out_x}, {out_y}, {out_z}, {norm}")
    print("offset_list:")
    print(low_g_acc.offset_list)


if __name__ == "__main__":
    main()