import sys
import time
import numpy as np
import cv2
import csv


def take_photo():
    camera = cv2.VideoCapture(-1, cv2.CAP_V4L2)
    camera.set(cv2.CAP_PROP_EXPOSURE, 1)

    sleep_time = 1
    rep = 100
    for _ in range(rep):
        time.sleep(sleep_time / rep)
        success, image = camera.read()

    success, image = camera.read()
    if not success:
        print("Failed 0n0")
        return -1
    image = cv2.flip(image, -1)
    camera.release()
    return image


def read_hsv_thresholds(filename):
    lower_thresholds = {}
    upper_thresholds = {}
    with open(filename, "r") as f:
        reader = csv.reader(f)
        header = next(reader)  # ヘッダーをスキップ

        for row in reader:
            parameter = row[0]
            lower = int(row[1])
            upper = int(row[2])
            lower_thresholds[parameter] = lower
            upper_thresholds[parameter] = upper

    return lower_thresholds, upper_thresholds


def hsv_binary(img_hsv, lower_bound, upper_bound):
    # Hue の値が円環状になっている場合の処理
    if lower_bound[0] <= upper_bound[0]:
        # 通常の範囲
        img_th = cv2.inRange(img_hsv, lower_bound, upper_bound)
    else:
        # Hue の値が 180 を超えてループする場合
        lower1 = np.array([lower_bound[0], lower_bound[1], lower_bound[2]])
        upper1 = np.array([179, upper_bound[1], upper_bound[2]])
        lower2 = np.array([0, lower_bound[1], lower_bound[2]])
        upper2 = np.array([upper_bound[0], upper_bound[1], upper_bound[2]])
        mask1 = cv2.inRange(img_hsv, lower1, upper1)
        mask2 = cv2.inRange(img_hsv, lower2, upper2)
        img_th = cv2.bitwise_or(mask1, mask2)
    return img_th


def scantheta(img_th):
    camera_horizontal_FoV = 62.2  # degrees
    theta_row_sum_10 = 0
    theta_row_mo_10 = 0

    # 行列サイズ
    width = img_th.shape[1]  # 横の長さ

    # 列の和
    im_thx = np.sum(img_th, axis=0)
    # 高い順にソート(インデックスを返す)
    theta_row_sub = np.argsort(im_thx)[::-1]

    # 上位1%を使用
    for i in range(int(width / 100)):
        theta_row_sum_10 += im_thx[theta_row_sub[i]]
        theta_row_mo_10 += theta_row_sub[i] * im_thx[theta_row_sub[i]]
    # 重心の計算
    if theta_row_sum_10 == 0:
        im_thx_maru = 0
    else:
        im_thx_maru = int(theta_row_mo_10 / theta_row_sum_10)

    theta = -(im_thx_maru / width * camera_horizontal_FoV - camera_horizontal_FoV / 2)

    return theta


def scanprop(img_th):
    # 特定の色の割合を計算する
    width = img_th.shape[1]
    height = img_th.shape[0]
    size = width * height

    color_area = np.count_nonzero(img_th)

    prop = (color_area / size) * 100

    return prop


def get_object_theta_and_proportion(colour_range, img=None):
    # CSV ファイルから閾値を読み込む
    lower_thresholds, upper_thresholds = read_hsv_thresholds(
        "/home/pi/TANE2025/prep/HSV_slider_values.csv"
    )
    lower_bound = np.array(
        [colour_range[0], lower_thresholds["Saturation"], lower_thresholds["Value"]]
    )
    upper_bound = np.array(
        [colour_range[1], upper_thresholds["Saturation"], upper_thresholds["Value"]]
    )

    # 読み込み
    if img is None:
        print("take photo")
        img = take_photo()
    # cv2.imwrite("colour_scan.jpg", img)

    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)  # HSV カラー空間に変換

    img_th = hsv_binary(img_hsv, lower_bound, upper_bound)
    # cv2.imwrite("scan.jpg", img_th)

    theta = scantheta(img_th)
    prop = scanprop(img_th)

    # カメラ試験用の出力
    print("theta = {}, prop = {}".format(theta, prop))

    return theta, prop


if __name__ == "__main__":
    # コマンドライン引数の処理を削除
    data = get_object_theta_and_proportion()
    print("prop:{}".format(data[1]))
    print("theta:{}".format(data[0]))
