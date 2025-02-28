# **function**
関数をまとめたファイルを管理するディレクトリです．
関係の深い関数を一つのファイルにまとめて管理してください．

### 関数
- **barometerFunction.py**
    - getPressure()
        - argument：None
        - return value：pressure[hPa]
      
      
- **gpsFunction.py**
    - getGPS()
        - argument：None
        - return value：latitude, longitude
    - getXY(）
        - argument：latitude_goal, longitude_goal, latitude, longitude
        - return value：x[m], y[m]
   
   
- **nineaxisFunction**
    - getMag()
        - argument：dis_x, dis_y
        - return value：mag_x, mag_y
    - getAccl()
        - argument：dis_x, dis_y, dis_z
        - return value：acc_x, acc_y, acc_z
     
     
- **motorFunction.py**
    - goForward()
        - argument：duty_r, duty_l, time
        - return value：None
    - goBackward()
        - argument：duty_r, duty_l, time
        - return value：None
    - rotateRight()
        - argument：duty_r, duty_l, time
        - return value： None
    - rotateLeft()
        - argument：duty_r, duty_l, time
        - return value：None
