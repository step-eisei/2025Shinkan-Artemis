#2024/11/26 Conta™ BM1422GMV 3軸地磁気センサモジュール
import smbus2
import time

# I²Cバス番号（Raspberry Piでは通常1）
I2C_BUS = 1
# BM1422GMVのI²Cアドレス（デフォルトは0x0E）
BM1422GMV_ADDRESS = 0x0E

# レジスタアドレス
REG_WIA = 0x0F  # Who am I レジスタ
REG_CNTL1 = 0x1B  # 制御レジスタ1
REG_CNTL2 = 0x1C  # 制御レジスタ2
REG_CNTL3 = 0x1D  # 制御レジスタ3
REG_CNTL4 = 0x5C  # 制御レジスタ4
REG_CNTL5 = 0x5D  # 制御レジスタ5
REG_DATAX = 0x10  # X軸データレジスタ（下位ビット）

# センサの初期化
def init_sensor(bus):
    # Who am I レジスタの読み取り
    who_am_i = bus.read_byte_data(BM1422GMV_ADDRESS, REG_WIA)
    if who_am_i != 0x41:
        raise Exception("BM1422GMVが見つかりません。")

    # 制御レジスタの設定
    bus.write_byte_data(BM1422GMV_ADDRESS, REG_CNTL1, 0x80)  # リセット
    time.sleep(0.1)
    bus.write_byte_data(BM1422GMV_ADDRESS, REG_CNTL4, 0x00)  # リセット解除
    bus.write_byte_data(BM1422GMV_ADDRESS, REG_CNTL5, 0x00)
    time.sleep(0.1)
    bus.write_byte_data(BM1422GMV_ADDRESS, REG_CNTL2, 0x08)  # 測定モード設定
    time.sleep(0.1)
    bus.write_byte_data(BM1422GMV_ADDRESS, REG_CNTL3, 0x40)  # 測定開始

# データの読み取り
def read_data(bus):
    data = bus.read_i2c_block_data(BM1422GMV_ADDRESS, REG_DATAX, 6)
    x = (data[1] << 8) | data[0]
    y = (data[3] << 8) | data[2]
    z = (data[5] << 8) | data[4]

    # 負の値の処理
    if x >= 32768:
        x -= 65536
    if y >= 32768:
        y -= 65536
    if z >= 32768:
        z -= 65536

    return x, y, z

def main():
    bus = smbus2.SMBus(I2C_BUS)
    try:
        init_sensor(bus)
        while True:
            x, y, z = read_data(bus)
            print(f"X: {x}, Y: {y}, Z: {z}")
            time.sleep(1)
    except Exception as e:
        print(e)
    finally:
        bus.close()

if __name__ == "__main__":
    main()
