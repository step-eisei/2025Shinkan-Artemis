import sys
sys.path.append("/home/pi/TANE2024/phase/")


from phase.camera_phase     import CameraPhase
from phase.distance_phase   import DistancePhase
# others
#from phase.subthread import Subthread

import time


def main():



    distance = Distance()
    #gps =      Gps()
    yolo =     CornDetect()

  
    camera =         CameraPhase()
    dist_phase =     DistancePhase()

    try:
        camera.main()
        print("end camera phase")
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
        motor.end()
        print("GPIO closed.")

if __name__ == "__main__":
    main()
