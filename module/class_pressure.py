from smbus import SMBus
import time


class Pressure:

    def __init__(self):  # 初期設定

        self.pressure = -1
        self.t_fine = 0.0
        self.bus_number = 1  # i2c0とi2c1ってのがあるので注意
        self.i2c_address = 0x76

        self.digT = []
        self.digP = []
        self.digH = []

        osrs_t = 1  # Temperature oversampling x 1
        osrs_p = 1  # Pressure oversampling x 1
        osrs_h = 1  # Humidity oversampling x 1
        mode = 3  # Normal mode
        t_sb = 3  # Tstandby 250ms
        filter = 0  # Filter off
        spi3w_en = 0  # 3-wire SPI Disable

        ctrl_meas_reg = (osrs_t << 5) | (osrs_p << 2) | mode
        config_reg = (t_sb << 5) | (filter << 2) | spi3w_en
        ctrl_hum_reg = osrs_h

        self.writeReg(0xF2, ctrl_hum_reg)
        self.writeReg(0xF4, ctrl_meas_reg)
        self.writeReg(0xF5, config_reg)
        self.get_calib_param()

    def writeReg(self, reg_address, data):
        self.bus = SMBus(self.bus_number)
        self.bus.write_byte_data(self.i2c_address, reg_address, data)

    def get_calib_param(self):
        calib = []
        self.bus = SMBus(self.bus_number)

        for i in range(0x88, 0x88 + 24):
            calib.append(self.bus.read_byte_data(self.i2c_address, i))
        calib.append(self.bus.read_byte_data(self.i2c_address, 0xA1))
        for i in range(0xE1, 0xE1 + 7):
            calib.append(self.bus.read_byte_data(self.i2c_address, i))

        self.digT.append((calib[1] << 8) | calib[0])
        self.digT.append((calib[3] << 8) | calib[2])
        self.digT.append((calib[5] << 8) | calib[4])
        self.digP.append((calib[7] << 8) | calib[6])
        self.digP.append((calib[9] << 8) | calib[8])
        self.digP.append((calib[11] << 8) | calib[10])
        self.digP.append((calib[13] << 8) | calib[12])
        self.digP.append((calib[15] << 8) | calib[14])
        self.digP.append((calib[17] << 8) | calib[16])
        self.digP.append((calib[19] << 8) | calib[18])
        self.digP.append((calib[21] << 8) | calib[20])
        self.digP.append((calib[23] << 8) | calib[22])
        self.digH.append(calib[24])
        self.digH.append((calib[26] << 8) | calib[25])
        self.digH.append(calib[27])
        self.digH.append((calib[28] << 4) | (0x0F & calib[29]))
        self.digH.append((calib[30] << 4) | ((calib[29] >> 4) & 0x0F))
        self.digH.append(calib[31])

        for i in range(1, 2):
            if self.digT[i] & 0x8000:
                self.digT[i] = (-self.digT[i] ^ 0xFFFF) + 1

        for i in range(1, 8):
            if self.digP[i] & 0x8000:
                self.digP[i] = (-self.digP[i] ^ 0xFFFF) + 1

        for i in range(0, 6):
            if self.digH[i] & 0x8000:
                self.digH[i] = (-self.digH[i] ^ 0xFFFF) + 1

    def readData(self):
        data = []
        for i in range(0xF7, 0xF7 + 8):
            data.append(self.bus.read_byte_data(self.i2c_address, i))
        pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)

        self.compensate_T(temp_raw)
        self.compensate_P(pres_raw)

    def compensate_P(self, adc_P):
        v1 = (self.t_fine / 2.0) - 64000.0
        v2 = (((v1 / 4.0) * (v1 / 4.0)) / 2048) * self.digP[5]
        v2 = v2 + ((v1 * self.digP[4]) * 2.0)
        v2 = (v2 / 4.0) + (self.digP[3] * 65536.0)
        v1 = (
            ((self.digP[2] * (((v1 / 4.0) * (v1 / 4.0)) / 8192)) / 8)
            + ((self.digP[1] * v1) / 2.0)
        ) / 262144
        v1 = ((32768 + v1) * self.digP[0]) / 32768

        self.pressure = ((1048576 - adc_P) - (v2 / 4096)) * 3125
        if self.pressure < 0x80000000:
            self.pressure = (self.pressure * 2.0) / v1
        else:
            self.pressure = (self.pressure / v1) * 2
        v1 = (
            self.digP[8] * (((self.pressure / 8.0) * (self.pressure / 8.0)) / 8192.0)
        ) / 4096
        v2 = ((self.pressure / 4.0) * self.digP[7]) / 8192.0
        self.pressure = self.pressure + ((v1 + v2 + self.digP[6]) / 16.0)
        self.pressure = self.pressure / 100

    def compensate_T(self, adc_T):
        v1 = (adc_T / 16384.0 - self.digT[0] / 1024.0) * self.digT[1]
        v2 = (
            (adc_T / 131072.0 - self.digT[0] / 8192.0)
            * (adc_T / 131072.0 - self.digT[0] / 8192.0)
            * self.digT[2]
        )
        self.t_fine = v1 + v2  # t_fineの更新

    def read(self):
        try:
            self.readData()  # pressureの値更新
        except KeyboardInterrupt:
            pass


def main():
    result_pressure = Pressure()  # classからできたインスタンス
    for i in range(10):
        result_pressure.read()  # Pressureクラスのread()呼出⇒pressureが計算される
        print(result_pressure.pressure)
        time.sleep(1.5)


if __name__ == "__main__":
    main()
