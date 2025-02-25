# class import
from module.class_pressure import Pressure
from module.class_nicrom   import Nicrom
from module.class_motor    import Motor
from module.class_distance import Distance
from module.class_gps      import Gps
from module.class_yolo     import CornDetect
# phase import
from phase.land_phase       import Land
from phase.deployment_phase import Deploy
from phase.gps_phase        import GpsPhase
from phase.camera_phase     import CameraPhase
from phase.distance_phase   import DistancePhase
# others
from phase.subthread import Subthread

import time

def main():
    GPIO.output(29, False)
    goal = False

    pressure = Pressure()
    nicrom =   Nicrom()
    motor =    Motor()
    distance = Distance()
    gps =      Gps()
    yolo =     CornDetect()

    subth =          Subthread(pressure=pressure, gps=gps, distance=distance, motor=motor)
    land =           Land(get_pressure=pressure, subth=subth)
    deployment =     Deploy(motor=motor, nicrom=nicrom, dist_sens=distance, gps=gps, subth=subth)
    gps_phase =      GpsPhase(motor=motor, gps=gps, subth=subth)
    camera =         CameraPhase(motor=motor, yolo=yolo, distance=distance, subth=subth)
    dist_phase =     DistancePhase(motor=motor, distance=distance, subth=subth)

    try:
        subth.run()
        
        try:
            land.run()
        except KeyboardInterrupt:
            print("Keyboard Interrupt")
            print("SKIP land phase")
            print("proceed to deployment phase")
        except Exception:
            print("ERROR: land phase")
            print("proceed to deployment phase")  
        
        sleep_time = 5
        try:
            for t in range(sleep_time):
                time.sleep(1)
                print(f"{t}秒経過")
        except KeyboardInterrupt: 
            print("deployment start")
        
        deployment.run()

        while True:
            gps_phase.run()

            try:
                return_camera = False
                return_camera = camera.run()
            except Exception:
                print("ERROR: camera phase")
                print("proceed to distance phase")
            
            if return_camera == True:
                try:
                    goal = dist_phase.run()
                except Exception:
                    print("ERROR: distance phase")
                    print("proceed to gps phase")
            
            if goal == True:
                print("GOAL!")
                break

    except KeyboardInterrupt:
        print("\nInterrupted.")
        subth.record(comment="end main")
        motor.end()
        print("GPIO closed.")

if __name__ == "__main__":
    main()
