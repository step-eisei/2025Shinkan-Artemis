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

camera = CameraPhase()
dist_phase =     DistancePhase()


def main():
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
