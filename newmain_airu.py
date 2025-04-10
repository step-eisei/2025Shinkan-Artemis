import sys
sys.path.append("/home/pi/2025Shinkan-Artemis/phase/")
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
#from phase.gps_phase        import GpsPhase
from phase.camera_phase     import CameraPhase
from phase.distance_phase   import DistancePhase
# others
from phase.subthread import Subthread

import time


def main():
    GPIO.setmode(GPIO.BOARD)
    goal = False

    camera =         CameraPhase(motor=motor, yolo=yolo, distance=distance, subth=subth)
    dist_phase =     DistancePhase(motor=motor, distance=distance, subth=subth)
    motor =          Motor()


    while True:
        try:
            camera.run()
            print("end camera phase")
        except KeyboardInterrupt:
                print("Keyboard Interrupt")
                print("SKIP camera phase")
                print("proceed to distance phase")
        except Exception:
            print("ERROR: camera phase")
            print("proceed to distance phase")

        if return_camera == True:
            try:
                dist_phase.run()

            except KeyboardInterrupt:
                print("\nInterrupted.")
                motor.end()
                print("GPIO closed.")

        if goal == True:
            print("GOAL!")
            break

if __name__ == "__main__":
    main()
