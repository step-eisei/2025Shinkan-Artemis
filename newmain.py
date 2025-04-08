import sys
sys.path.append("/home/pi/TANE2024/phase/")

import RPi.GPIO as GPIO

from module.class_motor    import Motor
from phase.camera_phase     import CameraPhase
from phase.distance_phase   import DistancePhase
# others
#from phase.subthread import Subthread

import time


def main():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(29, GPIO.OUT)
    GPIO.output(29, False)
    
    camera =         CameraPhase()
    dist_phase =     DistancePhase()
    motor =    Motor()


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

    try:
        dist_phase.run()

    except KeyboardInterrupt:
        print("\nInterrupted.")
        motor.end()
        print("GPIO closed.")

if __name__ == "__main__":
    main()
