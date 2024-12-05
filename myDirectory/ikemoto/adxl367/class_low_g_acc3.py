# -*- coding: utf-8 -*-
# 使用センサー: ADXL367
import smbus
import time
import math
import datetime
import codecs

import numpy as np


class LowGAcc3:
    def __init__(self, calibrated=False, offset_list = [[0 for _ in range(10)] for _ in range(3)], save_log_flag = False):
        self.calibrated = calibrated
        self.save_log_flag = save_log_flag
        self.offset_list = offset_list
        self.acc_x = 0
        self.acc_y = 0
        self.acc_z = 0

        self.ADDR = 0x1d
        self.i2c = smbus.SMBus(1)


        # センサーの所設定
        self.i2c.write_byte_data(self.ADDR, 0x2C, 0x03) # output data rate 100 Hz
        self.i2c.write_byte_data(self.ADDR, 0x2D, 0x02)


        if self.save_log_flag:
            # logの設定
            # csv log file ready
            fmt_name = "/home/pi/TANE2025/record/test/record/acc_logs_ADXL367_{0:%Y%m%d-%H%M%S}.csv".format(datetime.datetime.now())
            self.f_acc_logs = codecs.open(fmt_name, mode='w', encoding="utf-8")

            header_value = u"yyyy-mm-dd hh:mm:ss.mmmmmm,x[g],y[g],z[g],norm[g]"
            self.f_acc_logs.write(header_value+"\n")


        time.sleep(0.5)

    def apply_offset_list(offset_list, x, y, z):
        xyz_array = np.array([x, y, z])
        for i, offset in enumerate(offset_list):
            offset_array = np.array(offset)
            xyz_array[i] -= np.mean(offset_array)

        return tuple(xyz_array)
    
    def get_calibration_data(self):
        for _ in range(10):
            x, y, z = self.get_acc_raw()
            self.offset_list[0].append(x)
            self.offset_list[1].append(y)
            self.offset_list[2].append(z-1.0)
        
        print(self.offset_list)

        self.calibrated = True
    
    def get_acc_raw(self):
        # 単位はGです
        try:
            #データ読み込み
            xh = self.i2c.read_byte_data(self.ADDR, 0x0E)
            xl = self.i2c.read_byte_data(self.ADDR, 0x0F)
            yh = self.i2c.read_byte_data(self.ADDR, 0x10)
            yl = self.i2c.read_byte_data(self.ADDR, 0x11)
            zh = self.i2c.read_byte_data(self.ADDR, 0x12)
            zl = self.i2c.read_byte_data(self.ADDR, 0x13)
        
            #データ変換
            out_x = (xh << 6) | (xl >> 2)
            out_y = (yh << 8) | (yl >> 2)
            out_z = (zh << 8) | (zl >> 2)
        
            #極性判断
            if out_x >= 8192:
                out_x = out_x - 16384
        
            if out_y >= 8192:
                out_y = out_y - 16384
        
            if out_z >= 8192:
                out_z = out_z - 16384
        
            #物理量（加速度[g]）に変換
            out_x = out_x * 2 / 8191 # 2g設定
            out_y = out_y * 2 / 8191
            out_z = out_z * 2 / 8191

            if self.save_log_flag:
                # write log file
                now = datetime.datetime.now()
                self.f_acc_logs.write(f'{now}, {out_x}, {out_y}, {out_z}, {math.sqrt(out_x**2+out_y**2+out_z**2)}\n')
            
        except IOError as e:
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
        
        return out_x, out_y, out_z, math.sqrt(out_x**2+out_y**2+out_z**2)

    def get_acc_calibrated(self):
        if not self.calibrated:
            print("set calibration data!")
            return
        
        x, y, z = self.get_acc_raw()
        x, y, z = self.apply_offset_list(self.offset_list, x, y, z)

        return x, y, z, math.sqrt(x**2+y**2+z**2)

def main():
    low_g_acc = LowGAcc3(save_log_flag = True)
    
    try:
        while True:
            out_x, out_y, out_z, norm = low_g_acc.get_acc_raw()
            print(f"{out_x}, {out_y}, {out_z}, {norm}")
            time.sleep(0.1)
    except:
        low_g_acc.f_acc_logs.close()

def test_calib():
    low_g_acc = LowGAcc3(save_log_flag = True)
    low_g_acc.get_calibration_data()

    out_x, out_y, out_z, norm = low_g_acc.get_acc_calibrated()
    print(f"{out_x}, {out_y}, {out_z}, {norm}")
    print("offset_list:")
    print(low_g_acc.offset_list)


if __name__ == "__main__":
    main()