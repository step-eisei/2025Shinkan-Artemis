import time
import json
from smbus2 import SMBus, i2c_msg
import logging 
import threading
import numpy as np
import math
import csv
import melopero_ubx as ubx

NMEA_CLASS = 0xf0
GGA_ID = 0x00

class Gps:
  def __init__(self, debug=False):
    self.debug = debug

    self.bus = None
    self.address = 0x42
    self.gpsReadInterval = 0.01
    self.log = logging.getLogger()
    self.x, self.y = 0, 0

    # GUIDE
    # http://ava.upuaut.net/?p=768

    self.GPSDAT = {
        'strType': None,
        'fixTime': None,
        'lat': None,
        'latDir': None,
        'lon': None,
        'lonDir': None,
        'fixQual': None,
        'numSat': None,
        'horDil': None,
        'alt': None,
        'altUnit': None,
        'galt': None,
        'galtUnit': None,
        'DPGS_updt': None,
        'DPGS_ID': None
    }

    self.GNS = {
       "xxGNS": None,
       "time": None,
       "lat": None,
       "NS": None,
       "lon": None,
       "EW": None,
       "posMode": None,
       "numSV": None,
       "HDOP": None,
       "alt": None,
       "sep": None,
       "diffAge": None,
       "diffStation": None,
       "navStatus": None
    }

    self.latitude = 0.0
    self.longitude = 0.0

    self.connectBus()

    self.config()

    print("connecting GPS")
    while (self.longitude == 0 and self.latitude == 0):
       self.readGPS()
       time.sleep(self.gpsReadInterval)
    print("GPS connected!")
    
    #ゴールの座標の取得
    try:
      with open ('/home/pi/TANE2025/prep/goal.csv', 'r') as f :# goal座標取得プログラムより取得
        reader = csv.reader(f)
        line = [row for row in reader]
        self.goal_lati = float(line[ 1 ] [ 0 ])
        self.goal_longi = float(line[ 1 ] [ 1 ])
      print("read goal.csv")
    except:
      self.goal_lati = 0
      self.goal_longi = 0
      print("could not read goal.csv")

    gpsthread = threading.Thread(target=self.run, args=()) 
    gpsthread.daemon = True
    gpsthread.start()
  
  def config(self):
         #https://content.u-blox.com/sites/default/files/u-blox%20M10-SPG-5.00_InterfaceDescription_UBX-20053845.pdf
    #u-center
    
    #msg = [181,98,6,138,10,0,1,1,0,0,1,0,33,48,100,0,82,195]#CFG-RATE-MEAS rate 10Hz
    msg = [181,98,6,138,10,0,1,1,0,0,1,0,33,48,244,1,227,228]#CFG-RATE-MEAS rate 2Hz
    self.write_message(msg)
    self.wait_for_acknowledge(ubx.CFG_CLASS, ubx.CFG_PRT)
    
    #msg = [181,98,6,138,9,0,1,1,0,0,186,0,145,32,0,6,207]#CFG-MSGOUT-NMEA_ID_GGA_I2C 0Hz
    msg = [181,98,6,138,9,0,1,1,0,0,186,0,145,32,1,7,208]#CFG-MSGOUT-NMEA_ID_GGA_I2C 1 per epoch
    #msg = [181,98,6,138,9,0,1,1,0,0,186,0,145,32,2,8,209]#CFG-MSGOUT-NMEA_ID_GGA_I2C 2 per epoch
    self.write_message(msg)
    self.wait_for_acknowledge(ubx.CFG_CLASS, ubx.CFG_PRT)

    msg = [181,98,6,138,9,0,1,1,0,0,201,0,145,32,0,21,26]#CFG-MSGOUT-NMEA_ID_GLL_I2C 0Hz
    #msg = [181,98,6,138,9,0,1,1,0,0,201,0,145,32,1,22,27]
    self.write_message(msg)
    self.wait_for_acknowledge(ubx.CFG_CLASS, ubx.CFG_PRT)

    msg = [181,98,6,138,9,0,1,1,0,0,191,0,145,32,0,11,232]#CFG-MSGOUT-NMEA_ID_GSA_I2C 0Hz
    self.write_message(msg)
    self.wait_for_acknowledge(ubx.CFG_CLASS, ubx.CFG_PRT)

    msg = [181,98,6,138,9,0,1,1,0,0,196,0,145,32,0,16,1]#CFG-MSGOUT-NMEA_ID_GSV_I2C 0Hz
    self.write_message(msg)
    self.wait_for_acknowledge(ubx.CFG_CLASS, ubx.CFG_PRT)

    msg = [181,98,6,138,9,0,1,1,0,0,171,0,145,32,0,247,132]#CFG-MSGOUT-NMEA_ID_RMC_I2C 0Hz
    self.write_message(msg)
    self.wait_for_acknowledge(ubx.CFG_CLASS, ubx.CFG_PRT)

    msg = [181,98,6,138,9,0,1,1,0,0,176,0,145,32,0,252,157]#CFG-MSGOUT-NMEA_ID_VTG_I2C 0Hz
    self.write_message(msg)
    self.wait_for_acknowledge(ubx.CFG_CLASS, ubx.CFG_PRT)

    msg = [181,98,6,138,9,0,1,1,0,0,181,0,145,32,1,2,183]#CFG-MSGOUT-NMEA_ID_GNS_I2C 1 per epoch
    #msg = [181,98,6,138,9,0,1,1,0,0,181,0,145,32,0,1,182]#CFG-MSGOUT-NMEA_ID_GNS_I2C 0 per epoch
    self.write_message(msg)
    self.wait_for_acknowledge(ubx.CFG_CLASS, ubx.CFG_PRT)

    msg = [181, 98, 6, 138, 9, 0, 1, 1, 0, 0, 7, 0, 147, 32, 1, 86, 87]#CFG-NMEA-SVNUMBERING EXTENDED
    #self.write_message(msg)
    #self.wait_for_acknowledge(ubx.CFG_CLASS, ubx.CFG_PRT)

    msg = [181, 98, 6, 138, 9, 0, 1, 1, 0, 0, 5, 0, 55, 16, 1, 232, 25]#CFG-QZSS-USE_SLAS_DGNSS True
    #self.write_message(msg)
    #self.wait_for_acknowledge(ubx.CFG_CLASS, ubx.CFG_PRT)

    msg = [181, 98, 6, 138, 9, 0, 1, 1, 0, 0, 181, 0, 145, 32, 1, 2, 183]#CFG-MSGOUT-NMEA_ID_GNS_I2C 1
    #self.write_message(msg)
    #self.wait_for_acknowledge(ubx.CFG_CLASS, ubx.CFG_PRT)

    msg = [181, 98, 6, 138, 9, 0, 1, 1, 0, 0, 34, 0, 49, 16, 1, 255, 152]#CFG-SIGNAL-BDS_ENA
    #self.write_message(msg)
    #self.wait_for_acknowledge(ubx.CFG_CLASS, ubx.CFG_PRT)

    msg = [181, 98, 6, 138, 9, 0, 1, 1, 0, 0, 15, 0, 49, 16, 1, 236, 57]#CFG-SIGNAL-BDS_B1_ENA
    #self.write_message(msg)
    #self.wait_for_acknowledge(ubx.CFG_CLASS, ubx.CFG_PRT)

    #msg = [181, 98, 6, 138, 9, 0, 1, 1, 0, 0, 37, 0, 49, 16, 1, 2, 167]#CFG-SIGNAL-GLO_ENA
    #self.write_message(msg)
    #self.wait_for_acknowledge(ubx.CFG_CLASS, ubx.CFG_PRT)

    #msg = [181, 98, 6, 138, 9, 0, 1, 1, 0, 0, 20, 0, 49, 16, 1, 241, 82]#CFG-SIGNAL-QZSS_L1S_ENA
    #self.write_message(msg)
    #self.wait_for_acknowledge(ubx.CFG_CLASS, ubx.CFG_PRT)

  def connectBus(self):
      self.bus = SMBus(1)
      
  def available_bytes(self):
      """ returns the number of bytes available if a timeout is specified it
      tries to read the number of bytes for the given amount of millis"""
      msb = self.bus.read_byte_data(self.address, 0xFD)
      #time.sleep(0.01)
      lsb = self.bus.read_byte_data(self.address, 0xFE)
      #time.sleep(0.01)
      return msb << 8 | lsb

  def write_message(self, buffer):
      msg_out = i2c_msg.write(self.address, buffer)
      self.bus.i2c_rdwr(msg_out)
      time.sleep(0.01)

  #@timeout_decorator.timeout(0.3)
  def read_message(self):
      msg_length = self.available_bytes()
      msg = []
      if msg_length > ubx.MAX_MESSAGE_LENGTH:
          return msg
      print(msg_length)
      
      for _ in range(msg_length):
          msg.append(self.bus.read_byte_data(self.address, 0xFF))
          #time.sleep(0.001)
      #print(chr(msg[0]))
      return msg

  def wait_for_message(self, time_out_s=0.1, interval_s=0.01, msg_cls=None, msg_id=None):
    """ waits for a message of a given class and id.\n
    time_out_s :
        the maximum amount of time to wait for the message to arrive in seconds.
    interval_s :
        the interval in seconds between a two readings.
    msg_cls :
        the class of the message to wait for.
    msg_id :
        the id of the message to wait for."""
    start_time = time.time()
    to_compare = [ubx.SYNC_CHAR_1, ubx.SYNC_CHAR_2]
    if msg_cls:
        to_compare.append(msg_cls)
    if msg_id:
        to_compare.append(msg_id)

    #while time.time() - start_time < time_out_s:
    msg = self.read_message()
    if len(msg) >= len(to_compare):
        if msg[:len(to_compare)] == to_compare:
            return msg
    time.sleep(interval_s)
    return None

  def wait_for_acknowledge(self, msg_class, msg_id, verbose=True):
      """ An acknowledge message (or a Not Acknowledge message) is sent everytime
      after a configuration message is sent."""
      ack = False
      msg = self.wait_for_message(msg_cls=ubx.ACK_CLASS)
      if msg is None:
          print("No ACK/NAK Message received")
          time.sleep(0.01)
          return ack

      if msg[3] == ubx.ACK_ACK and msg_class == msg[6] and msg_id == msg[7]:
          ack = True

      if verbose:
          print(" A message of class : {} and id : {} was {}acknowledged".format(
              ubx.msg_class_to_string(msg[6]), msg[7], (not (msg[3] == ubx.ACK_ACK)) * "not "))
          
      time.sleep(0.01)
      return ack
  def poll_message(self, msg_cls, msg_id):
      msg = ubx.compose_message(msg_cls, msg_id, 0)
      self.write_message(msg)
      return self.wait_for_message(msg_cls=msg_cls, msg_id=msg_id)
  
  def parseResponse(self, gpsLine):
      self.lastLocation = None
      gpsChars = ''.join(chr(c) for c in gpsLine)
      if "*" not in gpsChars:
          return False

      gpsStr, chkSum = gpsChars.split('*')    
      gpsComponents = gpsStr.split(',')
      gpsStart = gpsComponents[0]

      if(self.debug):
         print(gpsChars)

      if (gpsStart == "$GNGGA"):
          chkVal = 0
          for ch in gpsStr[1:]: # Remove the $
              chkVal ^= ord(ch)
          if (chkVal == int(chkSum, 16)):
              valid = True
              for i, k in enumerate(
                ['strType', 'fixTime', 
                'lat', 'latDir', 'lon', 'lonDir',
                'fixQual', 'numSat', 'horDil', 
                'alt', 'altUnit', 'galt', 'galtUnit',
                'DPGS_updt', 'DPGS_ID']):
                  self.GPSDAT[k] = gpsComponents[i]
                  
              lat = self.GPSDAT["lat"]
              lon = self.GPSDAT["lon"]
              if(lat!='' and lon!='' and lat!=None and lon!=None):
                self.latitude = int(lat[0:2]) + float(lat[2:]) / 60
                self.longitude = int(lon[0:3]) + float(lon[3:]) / 60

              if(self.debug):
                 #print(gpsChars)
                 #print(json.dumps(self.GPSDAT, indent=2))
                 pass

      elif (gpsStart == "$GNGNS"):
         chkVal = 0
         for ch in gpsStr[1:]: # Remove the $
          chkVal ^= ord(ch)
          if (chkVal == int(chkSum, 16)):
            for i, k in enumerate(
                  ["xxGNS","time","lat","NS","lon","EW",
                   "posMode","numSV","HDOP","alt","sep",
                   "diffAge","diffStation","navStatus"]):
                self.GNS[k] = gpsComponents[i]

            lat = self.GNS["lat"]
            lon = self.GNS["lon"]
            if(lat!='' and lon!='' and lat!=None and lon!=None):
              self.latitude = int(lat[0:2]) + float(lat[2:]) / 60
              self.longitude = int(lon[0:3]) + float(lon[3:]) / 60

            if(self.debug):
              #print(gpsChars)
              print(json.dumps(self.GNS, indent=2))
      

  def readGPS(self):
      c = None
      response = []
      error = False
      try:
          if error: 
            self.config()
            error = False
          while True: # Newline, or bad char.
              c = self.bus.read_byte(self.address)
              if c == 255:
                  pass
                  #return False
              elif c == 10:
                  break
              else:
                  response.append(c)
              #time.sleep(0.001)
          #print(response)
          self.parseResponse(response)
          lat = self.GNS["lat"]
          lon = self.GNS["lon"]
          if(lat!='' and lon!='' and lat!=None and lon!=None):
            self.latitude = int(lat[0:2]) + float(lat[2:]) / 60
            self.longitude = int(lon[0:3]) + float(lon[3:]) / 60
      except IOError:
          time.sleep(0.5)
          if(self.debug):
             print("IOError reconnect")
          self.connectBus()
          error = True
      except Exception as e:
          time.sleep(0.5)
          print(f"Exception:{e}")
          self.log.error(e)
          self.connectBus()
          error = True
  
  def run(self):
      self.connectBus()
      i = 0
      while True:
        i += 1
        self.readGPS()
        self.getXY()
        self.getTheta()
        if(self.debug and i % 10 == 0):
          print(f"x:{self.x}, y:{self.y}, theta:{self.theta_goal}")
        #if(i%1000 == 0):
           #self.config()
        time.sleep(self.gpsReadInterval)

  def getXY(self):
    self.x, self.y = self.calc_xy()
    return self.x, self.y
  
  def getTheta(self):
    self.theta_goal = (math.atan2(self.y, self.x) * 180/math.pi) + 180
    return self.theta_goal
  
  # gpsからゴール基準で自己位置を求める関数(国土地理院より)
  def calc_xy(self):
    """ 
      緯度経度を平面直角座標に変換する
        - input:
        (gps_latitude, gps_longitude): 変換したい緯度・経度[度]（分・秒でなく小数であることに注意）
        (goal_latitude, goal_longitude): 平面直角座標系原点の緯度・経度[度]（分・秒でなく小数であることに注意）
        - output:
        x: 変換後の平面直角座標[m]
        y: 変換後の平面直角座標[m]
    """
      # 緯度経度・平面直角座標系原点をラジアンに直す
    phi_rad = np.deg2rad(self.latitude)
    lambda_rad = np.deg2rad(self.longitude)
    phi0_rad = np.deg2rad(self.goal_lati)
    lambda0_rad = np.deg2rad(self.goal_longi)

    # 補助関数
    def A_array(n):
      A0 = 1 + (n**2)/4. + (n**4)/64.
      A1 = -     (3./2)*( n - (n**3)/8. - (n**5)/64. )
      A2 =     (15./16)*( n**2 - (n**4)/4. )
      A3 = -   (35./48)*( n**3 - (5./16)*(n**5) )
      A4 =   (315./512)*( n**4 )
      A5 = -(693./1280)*( n**5 )
      return np.array([A0, A1, A2, A3, A4, A5])

    def alpha_array(n):
      a0 = np.nan # dummy
      a1 = (1./2)*n - (2./3)*(n**2) + (5./16)*(n**3) + (41./180)*(n**4) - (127./288)*(n**5)
      a2 = (13./48)*(n**2) - (3./5)*(n**3) + (557./1440)*(n**4) + (281./630)*(n**5)
      a3 = (61./240)*(n**3) - (103./140)*(n**4) + (15061./26880)*(n**5)
      a4 = (49561./161280)*(n**4) - (179./168)*(n**5)
      a5 = (34729./80640)*(n**5)
      return np.array([a0, a1, a2, a3, a4, a5])

    # 定数 (a, F: 世界測地系-測地基準系1980（GRS80）楕円体)
    m0 = 0.9999
    a = 6378137.
    F = 298.257222101

    # (1) n, A_i, alpha_iの計算
    n = 1. / (2*F - 1)
    A_array = A_array(n)
    alpha_array = alpha_array(n)

    # (2), S, Aの計算
    A_ = ( (m0*a)/(1.+n) )*A_array[0] # [m]
    S_ = ( (m0*a)/(1.+n) )*( A_array[0]*phi0_rad + np.dot(A_array[1:], np.sin(2*phi0_rad*np.arange(1,6))) ) # [m]

    # ここまで定数．今後はA_，　S_，　alpha_arrayのみを利用
      
    # (3) lambda_c, lambda_sの計算
    lambda_c = np.cos(lambda_rad - lambda0_rad)
    lambda_s = np.sin(lambda_rad - lambda0_rad)

    # (4) t, t_の計算
    t = np.sinh( np.arctanh(np.sin(phi_rad)) - ((2*np.sqrt(n)) / (1+n))*np.arctanh(((2*np.sqrt(n)) / (1+n)) * np.sin(phi_rad)) )
    t_ = np.sqrt(1 + t*t)

    # (5) xi', eta'の計算
    xi2  = np.arctan(t / lambda_c) # [rad]
    eta2 = np.arctanh(lambda_s / t_)

    # (6) x, yの計算
    X = A_ * (xi2 + np.sum(np.multiply(alpha_array[1:],
                                        np.multiply(np.sin(2*xi2*np.arange(1,6)),
                                                    np.cosh(2*eta2*np.arange(1,6)))))) - S_ # [m]
    Y = A_ * (eta2 + np.sum(np.multiply(alpha_array[1:],
                                            np.multiply(np.cos(2*xi2*np.arange(1,6)),
                                                        np.sinh(2*eta2*np.arange(1,6)))))) # [m]
        
    # return
    x = Y
    y = X # [m]，(x_now, y_now)で，軸が反転している．

    return x, y

if __name__ == "__main__":
  gps = Gps(debug=True)
  while True:
    print(f"lat,lon=({gps.latitude:9.6f},{gps.longitude:9.6f})\n")
    print(f"x,y=({gps.x:9.6f},{gps.y:9.6f})\n")
    time.sleep(0.1)
