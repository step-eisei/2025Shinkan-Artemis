# 2024/11/26 Conta™ BM1422GMV 3軸地磁気センサモジュール
from smbus import SMBus
import time
import numpy as np
import math
import csv

class Mag3:

# レジスタアドレス
    REG_WIA = 0x0F  # Who am I レジスタ
    REG_CNTL1 = 0x1B  # 制御レジスタ1
    REG_CNTL2 = 0x1C  # 制御レジスタ2
    REG_CNTL3 = 0x1D  # 制御レジスタ3
    REG_CNTL4 = 0x5C  # 制御レジスタ4
    REG_CNTL5 = 0x5D  # 制御レジスタ5
    REG_DATAX = 0x10  # X軸データレジスタ（下位ビット）

    def __init__(self, calibrated=False, rads=[1.0, 1.0, 1.0], aves=[0.0, 0.0, 0.0]):
        self.theta=-1
        self.theta_absolute=-1
        self.calibrated = calibrated
        self.rads = rads
        self.aves = aves
        self.mag_x = 0
        self.mag_y = 0
        self.mag_z = 0

        # I2Cのアドレス指定
        self.MAG_ADDR = 0x0E
        self.MAG_R_ADDR = 0x1D
        self.i2c = SMBus(1)

        # mag_data_setup : 地磁気値をセットアップ
        data = self.i2c.read_byte_data(self.MAG_ADDR, self.REG_WIA)
        if(data == 0):
                self.i2c.write_byte_data(self.MAG_ADDR, 0x4B, 0x83)
                time.sleep(0.5)
        self.i2c.write_byte_data(self.MAG_ADDR, self.REG_CNTL1, 0x80)
        self.i2c.write_byte_data(self.MAG_ADDR, self.REG_CNTL4, 0x00)
        self.i2c.write_byte_data(self.MAG_ADDR, self.REG_CNTL5, 0x00)
        self.i2c.write_byte_data(self.MAG_ADDR, self.REG_CNTL2, 0x08)
        self.i2c.write_byte_data(self.MAG_ADDR, self.REG_CNTL3, 0x40)

        time.sleep(0.5)

    def mag_value(self):
            try:
                    data = self.i2c.read_i2c_block_data(self.MAG_ADDR, self.REG_DATAX, 6)
                    x = (data[1] << 8) | data[0]
                    y = (data[3] << 8) | data[2]
                    z = (data[5] << 8) | data[4]
                    
                    if x >= 32768:
                            x -= 65536
                    if y >= 32768:
                            y -= 65536
                    if z >= 32768:
                            z -= 65536
                    mag_data = [x, y, z]

    
                    
            except IOError as e:
                    print("I/O error({0}): {1}".format(e.errno, e.strerror))
                    mag_data = [0, 0, 0]
            #print(mag_data)
            return mag_data


    def get_mag(self):
        while True:
            try:
                mag = self.mag_value()
                self.mag_x = mag[0]
                self.mag_y = -1*mag[1]
                self.mag_z = mag[2]
                break
            except:
                time.sleep(0.1)
                print("get_mag error")


        if self.calibrated:
            self.normalize()
            self.theta_absolute = 180 - math.atan2(self.mag_y, self.mag_x)*180/math.pi

        ###
        self.theta_absolute -= 90
        if(self.theta_absolute <= 0):
            self.theta_absolute += 360
        ###

        self.theta = self.theta_absolute
    
    def normalize(self):
        self.mag_x = (self.mag_x - self.aves[0]) / self.rads[0]
        self.mag_y = (self.mag_y - self.aves[1]) / self.rads[1]
        self.mag_z = (self.mag_z - self.aves[2]) / self.rads[2]

def main():
    with open ('/home/pi/TANE2025/prep/calibration_geomag.csv', 'r') as f :# goal座標取得プログラムより取得
        reader = csv.reader(f)
        line = [row for row in reader]
        rads = [float(line[1][i]) for i in range(3)]
        aves = [float(line[2][i]) for i in range(3)]
        f.close()
    mag3 = Mag3(calibrated=True, rads=rads,aves=aves)
    while True:
        mag3.get_mag()
        print(f"mag_x:{mag3.mag_x},mag_y:{mag3.mag_y},mag_z:{mag3.mag_z}")
        print(f"theta_absolute:{mag3.theta_absolute}")
        print(f"theta:{mag3.theta}")
        time.sleep(0.5)


if __name__ == "__main__":
    main()

