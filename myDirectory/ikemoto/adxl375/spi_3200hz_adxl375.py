import spidev
import time
import datetime
import codecs
import math

# utility
def hosuu_to_normal(num):
    if num > 32768:
        num -= 65536
    return num

def check_out_range( x, y, z):
    return x >= 200 or x <= -200 or y >= 200 or y <= -200 or z >= 200 or z <= -200

# 初期設定
spi = spidev.SpiDev()
spi.open(0,0)
spi.mode = 3  # このデバイスはSPI mode3で動作
spi.max_speed_hz = 5000000

#spi.xfer2([0x2C, 0x0F]) # output data rate 3200 Hz
spi.xfer2([0x31, 0x0B])
spi.xfer2([0x2C, 0x0F])
spi.xfer2([0x2D, 0x08]) # 測定スタート

# offset
OFFSET_ADJUST = False

def avg_offset_list(offset_list):
    res = 0
    for offset_list_ele in offset_list:
        res += offset_list_ele
    return res/len(offset_list)

offset_count = 10
offset_x = []
offset_y = []
offset_z = []

# file output
fmt_name = "record/acc_logs_ADXL_test_200g_{0:%Y%m%d-%H%M%S}.csv".format(datetime.datetime.now())
f_acc_logs = codecs.open(fmt_name, mode='w', encoding="utf-8")

header_value = u"yyyy-mm-dd hh:mm:ss.mmmmmm,x[g],y[g],z[g],norm[g]"
f_acc_logs.write(header_value+"\n")

# temporary variable
max_value = 0

try:
    while True:
        # x,y,z方向の加速度を取得(2の補数表現)
        x_data_list = spi.xfer2([0xc0|0x32, 0x00, 0x00])
        y_data_list = spi.xfer2([0xc0|0x34, 0x00, 0x00])
        z_data_list = spi.xfer2([0xc0|0x36, 0x00, 0x00])
        x_data = x_data_list[1] | (x_data_list[2] << 8)
        y_data = y_data_list[1] | (y_data_list[2] << 8)
        z_data = z_data_list[1] | (z_data_list[2] << 8)
        # 2の補数を10進に変換
        x_data = hosuu_to_normal(x_data)
        y_data = hosuu_to_normal(y_data)
        z_data = hosuu_to_normal(z_data)
        # 加速度に変換（Dレンジ ±200g）
        x_data = x_data * 200 / 0xFFF
        y_data = y_data * 200 / 0xFFF
        z_data = z_data * 200 / 0xFFF

        if check_out_range(x_data, y_data, z_data):
            continue

        if OFFSET_ADJUST:
            if offset_count >= 0 :
                offset_count -= 1
                offset_x.append(x_data)
                offset_y.append(y_data)
                offset_z.append(z_data-(+1)) # z軸方向に重力があるように
                continue

            x_data -= avg_offset_list(offset_x)
            y_data -= avg_offset_list(offset_y)
            z_data -= avg_offset_list(offset_z)

        # write log file
        now = datetime.datetime.now()
        f_acc_logs.write(f'{now},{x_data},{y_data},{z_data},{math.sqrt(x_data**2+y_data**2+z_data**2)}\n')
        if math.sqrt(x_data**2+y_data**2+z_data**2) > max_value:
            max_value = math.sqrt(x_data**2+y_data**2+z_data**2)
            print(max_value)
        # print('x: {:4.2f}, y: {:4.2f}, z: {:4.2f} [G]'.format(x_data, y_data, z_data))
        # time.sleep(0.1)

except KeyboardInterrupt:
    print('Ctrl-C FINISH!')
    f_acc_logs.close()
