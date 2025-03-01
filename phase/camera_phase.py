import sys

sys.path.append("/home/pi/TANE2025/")
sys.path.append("/home/pi/TANE2025/module/")
from module import class_yolo
from module import class_motor
from module import class_distance
from phase import subthread
from function.get_object_theta_and_proportion import get_object_theta_and_proportion
from const import CONE_COLOUR
import time
import math
import cv2
import numpy as np


class CameraPhase:
    def __init__(self, motor=None, yolo=None, distance=None, subth=None):
        if yolo == None:
            self.yolo = class_yolo.CornDetect()
        else:
            self.yolo = yolo

        if motor == None:
            self.motor = class_motor.Motor()
        else:
            self.motor = motor
        self.motor.geomag.calibrated = True
        self.geomag = self.motor.geomag

        if distance == None:
            self.distance = class_distance.Distance()
        else:
            self.distance = distance

        if subth == None:
            self.subth = subthread.Subthread(distance=self.distance, motor=self.motor)
            self.subth.run()
        else:
            self.subth = subth

        # const
        self.angle_thres = 15
        self.image_size = [640, 480]
        self.cone_colour = CONE_COLOUR
        #####
        self.ratio = 0.55
        #####

    # calculate angle from photo
    def calc_angle(self, c1, c2):
        if c1 == [-1, -1]:
            return 180
        x1, x2 = c1[0], c2[0]  # コーンの左と右のx座標

        x_med = (x1 + x2) / 2  # コーンの中央が画像のどの位置にいるか
        x_dist = (
            -2 * (x_med - self.image_size[0] / 2) / self.image_size[0]
        )  # 中央からx方向にどれくらい離れてるか -1~1まで取る
        # print(f"x_dist:{x_dist}")

        c = 1 / math.sqrt(3)  # 調整用の定数 画角60度
        angle = math.degrees(
            math.atan(c * x_dist)
        )  # コーンに向くまでの角度を計算 c=1の場合 -45~45度
        print(f"angle:{angle}")
        return angle

    # check distance between body and red cone
    def check_distance(self):
        self.distance.reading()

        return self.distance.distance

    def angle_difference(self, from_angle, to_angle):
        angle = to_angle - from_angle
        if angle < -180:
            return angle + 360
        elif angle > 180:
            return angle - 360
        return angle

    def forward(self, forward_time):
        print("\nforward method")
        self.geomag.get_mag()
        angle_before = self.geomag.theta_absolute

        self.motor.forward(duty_target=60, t=forward_time)
        self.subth.record(comment=f"duty-60-60")
        time.sleep(0.5)

        self.geomag.get_mag()
        angle_after = self.geomag.theta_absolute
        angle_diff = self.angle_difference(angle_before, angle_after)
        if angle_diff > 180:
            angle_diff -= 360
        print(f"before angle    :{angle_before}")
        print(f"after angle     :{angle_after}")
        print(f"difference angle:{angle_diff}")

        if abs(angle_after - angle_before) >= 30:
            print(f"rotate angle    :{-angle_diff}")
            self.motor.rotate(-angle_diff * 0.8)
        self.geomag.get_mag()
        angle_now = self.geomag.theta_absolute
        print(f"angle{angle_now}")
        print("")

    def run(self):
        self.subth.phase = 3
        i = 0  # コーンが見つからずその場で回転した回数
        j = 0  # 写真の番号

        self.prepare_camera()

        self.find_cone()

        while True:
            self.motor.get_up()

            print("take photo")
            for m in range(60):
                _, im = self.camera.read()
            image = cv2.flip(im, -1)
            #####
            # red_channel = np.clip(image[:, :, 2] *self.ratio, 0, 255)
            # red_channel = 255 / (1 + np.exp(-10 * (red_channel - 128) / 255))
            # image[:, :, 2] = red_channel
            # print("aaaaaaaa")
            #####
            _, prop = get_object_theta_and_proportion(self.cone_colour, img=image)

            dist = self.check_distance()  # 距離を測る
            print(f"dist:{dist}")

            if dist <= 60 and prop > 5:  # distance of red cone is within 60cm
                print("cone is very close")
                self.camera.release()
                return True

            # take a photo and image-processing
            c1, c2, yolo_image = self.yolo.estimate(image)
            cv2.imshow("Processed Image", yolo_image)
            cv2.waitKey(1)
            j += 1
            cv2.imwrite(f"/home/pi/TANE2025/image/yolo_image{j}.jpg", yolo_image)
            self.subth.record(comment=f"took photo saved as image/yolo_image{j}.jpg")
            print(c1, c2)  # print the coordinates of the cone
            if c1 != [-1, -1] and c2 != [-1, -1]:
                roi = image[c1[1] : c2[1], c1[0] : c2[0]]
                _, prop_cone = get_object_theta_and_proportion(
                    self.cone_colour, img=roi
                )
                print(f"c1 = {c1}, c2 = {c2}")
                print(f"prop{prop_cone}")
                if prop_cone <= 20:
                    c1 = [-1, -1]
                    c2 = [-1, -1]

            if (
                abs(self.calc_angle(c1, c2)) <= self.angle_thres
            ):  # red cone in the center of image
                print("cone is in the centre")
                self.subth.record(comment=f"cone is in the centre")
                # angle = self.calc_angle(c1, c2)
                # self.motor.rotate(angle*0.8)
                print("forward")
                i = 0

                # cone_size = c2[0] - c1[0]
                # dist_from_camera = math.tan(math.pi/3) / 2 * 0.38 * self.image_size[0] / cone_size
                # print(f"distance estimated from yolo{dist_from_camera}")

                # forward_time = min(dist_from_camera * 0.4, 4)
                self.subth.record(comment="[camera] approach cone", coneangle=0)
                # self.forward(forward_time)
                self.track_cone(image, c1, c2)

            else:  # red cone is NOT in the center of image
                if c1 != [-1, -1] and c2 != [-1, -1]:  # red cone is in the image
                    print("cone is detected")
                    i = 0
                    angle = self.calc_angle(c1, c2)
                    print(f"angle{angle}")
                    self.subth.record(comment=f"cone is in the image", coneangle=angle)
                    self.subth.record(comment="rotate for cone")
                    self.motor.rotate(angle)

                else:  # red cone is NOT in the image
                    print("cone is NOT in the image")
                    self.subth.record(comment=f"cone is NOT in the image")
                    if (
                        dist < 100 and prop > 20
                    ):  # コーンがカメラで見つからなくても、距離センサが反応して、画像が十分に赤ければ前進
                        i = 0
                        print("cone is close")
                        self.subth.record(comment=f"dist sens detected", coneangle=0)
                        print("forward")
                        # self.motor.forward(30, 30, 0.05, tick_dutymax=5)#距離に応じて前進
                        # time.sleep(dist/30)
                        self.subth.record(comment="[dist] approach cone")
                        self.forward(dist / 150)
                        self.motor.changeduty(0, 0)
                        self.subth.record(comment=f"duty-0-0")

                    elif i < 12:  # その場で回転
                        i += 1
                        self.subth.record(comment="can not find cone rotate")
                        if i <= 6:
                            if i % 2 == 1:
                                self.motor.rotate(30 * i)
                            else:
                                self.motor.rotate(-30 * i)
                        else:
                            self.motor.rotate(-30)

                    else:  # back to phase_GPS
                        self.forward(2)
                        self.subth.record(comment="back to gps phase")
                        print("back to phase_gps")
                        self.camera.release()
                        return False

    def prepare_camera(self):
        self.camera = cv2.VideoCapture(-1, cv2.CAP_V4L2)
        self.camera.set(cv2.CAP_PROP_EXPOSURE, 5)
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        success = False
        for i in range(100):
            success, _ = self.camera.read()
            if success:
                break
            time.sleep(0.1)
            print("waiting camera..........\n")

        success, _ = self.camera.read()
        if success:
            print("camera.read success")
            return True
        else:
            print("camera.read fail")
            return False

    def find_cone(self):
        max_prop = 0
        self.geomag.get_mag()
        cone_angle = self.geomag.theta_absolute

        for i in range(12):
            self.motor.get_up()

            self.motor.rotate(30)
            self.geomag.get_mag()
            new_angle = self.geomag.theta_absolute

            print("take photo")
            for m in range(60):
                _, im = self.camera.read()
            image = cv2.flip(im, -1)
            #####
            red_channel = np.clip(image[:, :, 2] * self.ratio, 0, 255)
            red_channel = 255 / (1 + np.exp(-10 * (red_channel - 128) / 255))
            image[:, :, 2] = red_channel
            #####
            _, prop = get_object_theta_and_proportion(self.cone_colour, img=image)

            if prop > max_prop:
                max_prop = prop
                cone_angle = new_angle

        print(f"cone_angle:{cone_angle}, prop:{max_prop}")
        self.geomag.get_mag()
        now_angle = self.geomag.theta_absolute
        diff_angle = self.motor.angle_difference(now_angle, cone_angle)
        self.motor.rotate(diff_angle)

    def track_cone(self, frame, c1, c2):
        video_flag = True
        if video_flag:
            fps = int(self.camera.get(cv2.CAP_PROP_FPS))  # カメラのFPSを取得
            w = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))  # カメラの横幅を取得
            h = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))  # カメラの縦幅を取得
            fourcc = cv2.VideoWriter_fourcc(
                "m", "p", "4", "v"
            )  # 動画保存時のfourcc設定（mp4用）
            video = cv2.VideoWriter(
                "/home/pi/TANE2025/image/video.mp4", fourcc, fps, (w, h)
            )

        BUFFER = 3
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, BUFFER)

        cone_size = c2[0] - c1[0]
        dist_from_camera = (
            math.tan(math.pi / 3) / 2 * 0.1 * self.image_size[0] / cone_size
        )
        print(f"distance estimated from yolo{dist_from_camera}")
        dist_from_camera = min(max(dist_from_camera, 1.2), 5.0)
        time_run = dist_from_camera * 1.2

        # setup initial location of window
        c, r = c1
        h = c2[1] - c1[1]
        w = c2[0] - c1[0]
        track_window = (c, r, w, h)

        # set up the ROI for tracking
        roi = frame[r : r + h, c : c + w]
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(
            hsv_roi, np.array((0.0, 60.0, 32.0)), np.array((180.0, 255.0, 255.0))
        )
        roi_hist = cv2.calcHist([hsv_roi], [0], mask, [180], [0, 180])
        cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)

        # Setup the termination criteria, either 10 iteration or move by atleast 1 pt
        term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)

        angle_past = None
        time_start = time.time()
        time_now = time_start
        while (time_now - time_start) < time_run:

            for i in range(BUFFER - 1):
                _, frame = self.camera.read()
                frame = cv2.flip(frame, -1)
                #####
                red_channel = np.clip(frame[:, :, 2] * self.ratio, 0, 255)
                red_channel = 255 / (1 + np.exp(-10 * (red_channel - 128) / 255))
                frame[:, :, 2] = red_channel
                #####
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                dst = cv2.calcBackProject([hsv], [0], roi_hist, [0, 180], 1)

                # apply meanshift to get the new location
                _, track_window = cv2.meanShift(dst, track_window, term_crit)

                # Draw it on image
                x, y, w, h = track_window
                img2 = cv2.rectangle(frame, (x, y), (x + w, y + h), 255, 2)
                cv2.imshow("img2", img2)
                if video_flag:
                    video.write(img2)

            # move towards cone
            angle = self.calc_angle([x, y], [x + w, y + h])
            if angle_past == None:
                angle_past = angle
            angle_diff = angle - angle_past

            P = 0.5
            D = 0.1
            duty = 50

            if abs(angle) < 20:
                pd = P * angle + D * angle_diff
                duty_R = duty - pd
                duty_L = duty + pd
                self.motor.changeduty(duty_R, duty_L)
                self.subth.record(comment=f"duty-{self.duty_R}-{self.duty_L}")
            else:
                break

            angle_past = angle
            cv2.waitKey(1)
            time_now = time.time()

        for i in range(10):
            self.motor.changeduty(30 - i * 3, 30 - i * 3)
            self.subth.record(comment=f"duty-{30 - i * 3}-{30 - i * 3}")
        self.motor.changeduty(5, 5)
        self.subth.record(comment=f"duty-5-5")
        time.sleep(1)
        self.motor.changeduty(0, 0)
        self.subth.record(comment=f"duty-0-0")
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cv2.destroyAllWindows()


def main():
    try:
        phase_camera = CameraPhase()
        phase_camera.run()
        phase_camera.motor.end()
    except KeyboardInterrupt:
        phase_camera.motor.end()
        phase_camera.camera.release()
        print("\nInterrupted.")


if __name__ == "__main__":
    main()
