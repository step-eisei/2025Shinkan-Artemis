import sys
sys.path.append("/home/pi/TANE2024/phase/")
# class import
import RPi.GPIO as GPIO
from module.class_pressure import Pressure
from module.class_nicrom   import Nicrom
from module.class_motor    import Motor
from module.class_distance import Distance
#from module.class_gps      import Gps
from module.class_yolo     import CornDetect
# phase import
from phase.land_phase       import Land
from phase.deployment_phase import Deploy
from phase.gps_phase        import GpsPhase
from phase.camera_phase     import CameraPhase
from phase.distance_phase   import DistancePhase
# others
#from phase.subthread import Subthread

import time


def main():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(29, GPIO.OUT)
    GPIO.output(29, False)
    goal = False

    pressure = Pressure()
    nicrom =   Nicrom()
    motor =    Motor()
    distance = Distance()
    #gps =      Gps()
    yolo =     CornDetect()

    subth =          Subthread(pressure=pressure, gps=gps, distance=distance, motor=motor)
    land =           Land(get_pressure=pressure)
    deployment =     Deploy(motor=motor, nicrom=nicrom, dist_sens=distance, gps=gps)
    #gps_phase =      GpsPhase(motor=motor, gps=gps, subth=subth)
    camera =         CameraPhase(motor=motor, yolo=yolo, distance=distance)
    dist_phase =     DistancePhase(motor=motor, distance=distance)

    try:
        camera.main()
    except KeyboardInterrupt:
            print("Keyboard Interrupt")
            print("SKIP camera phase")
            print("proceed to distance phase")
    except Exception:
        print("ERROR: camera phase")
        print("proceed to distance phase")  

    try:
        dist_phase.main()

    except KeyboardInterrupt:
        print("\nInterrupted.")
        #subth.record(comment="end main")
        motor.end()
        print("GPIO closed.")

if __name__ == "__main__":
    main()
