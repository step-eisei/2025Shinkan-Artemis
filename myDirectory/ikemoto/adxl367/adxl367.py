import smbus
import time
import math
import datetime
import codecs

def avg_offset_list(offset_list):
    res = 0
    for offset_list_ele in offset_list:
        res += offset_list_ele
    return res/len(offset_list)

#I2C設定
i2c = smbus.SMBus(1)
address = 0x1d

#センサーの設定
ret = i2c.write_byte_data(address, 0x2C, 0x03) # output data rate 100 Hz
ret = i2c.write_byte_data(address, 0x2D, 0x02)

offset_count = 10
offset_x = []
offset_y = []
offset_z = []

# csv log file ready
fmt_name = "record/acc_logs_ADXL_test_4g_{0:%Y%m%d-%H%M%S}.csv".format(datetime.datetime.now())
f_acc_logs = codecs.open(fmt_name, mode='w', encoding="utf-8")

header_value = u"yyyy-mm-dd hh:mm:ss.mmmmmm,x[g],y[g],z[g],norm[g]"
f_acc_logs.write(header_value+"\n")

max_value = 0
try:
    while True:
        #データ読み込み
        xh = i2c.read_byte_data(address, 0x0E)
        xl = i2c.read_byte_data(address, 0x0F)
        yh = i2c.read_byte_data(address, 0x10)
        yl = i2c.read_byte_data(address, 0x11)
        zh = i2c.read_byte_data(address, 0x12)
        zl = i2c.read_byte_data(address, 0x13)
    
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
        out_x = out_x * 2 / 8192
        out_y = out_y * 2 / 8192
        out_z = out_z * 2 / 8192


        if offset_count >= 0 :
            offset_count -= 1
            offset_x.append(out_x)
            offset_y.append(out_y)
            offset_z.append(out_z-(+1)) # z軸方向に重力があるように
            continue
    
        # # offset x, y, z
        out_x -= avg_offset_list(offset_x)
        out_y -= avg_offset_list(offset_y)
        out_z -= avg_offset_list(offset_z)
        #表示
        print('X: ' + str(out_x))
        print('Y: ' + str(out_y))
        print('Z: ' + str(out_z))
        print('acc_size: ' + str(math.sqrt(out_x**2+out_y**2+out_z**2)))

        # write log file
        now = datetime.datetime.now()
        f_acc_logs.write(f'{now}, {out_x}, {out_y}, {out_z}, {math.sqrt(out_x**2+out_y**2+out_z**2)}\n')
        if math.sqrt(out_x**2+out_y**2+out_z**2) > max_value:
            max_value = math.sqrt(out_x**2+out_y**2+out_z**2)
            print(max_value)
        #一時停止
        time.sleep(0.1)
except:
    f_acc_logs.close()

