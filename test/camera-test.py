import time
import cv2
def take_photo():
    camera = cv2.VideoCapture(-1, cv2.CAP_V4L2)
    camera.set(cv2.CAP_PROP_EXPOSURE, 5)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    for i in range(100):
        success, _ = camera.read()
        if success:
            break
        time.sleep(0.1)
        print("waiting camera.................")
    success, _ = camera.read()
    if success:
        print("camera.read success")
    else:
        print("0n0")

take_photo()
