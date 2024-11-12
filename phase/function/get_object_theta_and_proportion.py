import sys
import time
import numpy as np
import cv2

def take_photo():
    camera = cv2.VideoCapture(-1, cv2.CAP_V4L2)
    camera.set(cv2.CAP_PROP_EXPOSURE, 1)

    sleep_time = 1
    rep = 100
    for _ in range(rep):
        time.sleep(sleep_time/rep)
        success, image = camera.read()
        
    success, image = camera.read()
    if not success:
        print("Failed 0n0")
        return -1
    image = cv2.flip(image, -1)
    camera.release()
    return image


def hls_binary(img_hls, colour_range):
    saturation_min = 100 # TODO: 変更しやすいように
    v_min = 60
    if colour_range[0] < colour_range[1]:
        img_hls = cv2.inRange(img_hls, (colour_range[0], saturation_min, v_min), (colour_range[1], 250, 250))
    else:
        mask1 = cv2.inRange(img_hls, (colour_range[0], saturation_min, v_min), (180, 250, 250))
        mask2 = cv2.inRange(img_hls, (0, saturation_min, v_min), (colour_range[1], 250, 250))
        img_hls = cv2.bitwise_or(mask1, mask2)

    return img_hls


def scantheta(img_th):
    camera_horizontal_FoV = 62.2 # degrees
    theta_row_sum_10 = 0
    theta_row_mo_10 = 0

    # 行列サイズ
    # img_th[縦,横,色]
    width=img_th.shape[1] # 横の長さ
    # hight=img_th.shape[1]
    
    # 列の和
    im_thx=np.sum(img_th,axis=0)
    print(im_thx.shape)
    #　高い順にソート(インデックスを返す)
    theta_row_sub = np.argsort(im_thx)[::-1]
    print(theta_row_sub.shape)
    
    #　上位1%を
    for i in range(int(width/100)): # 1280から画像中の赤コーンが占める割合からまあどれくらいで割るか決める
        theta_row_sum_10 += im_thx[theta_row_sub[i]] 
        theta_row_mo_10 += theta_row_sub[i]*im_thx[theta_row_sub[i]] 
    # 重心の計算
    print(theta_row_sum_10)
    if theta_row_sum_10 == 0:
        im_thx_maru = 0
    else:
        im_thx_maru = int(theta_row_mo_10 / theta_row_sum_10)
    

    theta=-(im_thx_maru/width*camera_horizontal_FoV-camera_horizontal_FoV/2)
   
    # print('重心：{}, 角度：{}'.format(im_thx_maru, theta)

    return theta


def scanprop(img_th):
    # パラシュートの色の割合を計算する
    width=img_th.shape[1]
    height=img_th.shape[0]
    size=width*height

    red_area=np.count_nonzero(img_th)

    prop=(red_area/size)*100

    return prop


def get_object_theta_and_proportion(colour_range, img=None):
    # 読み込み
    if img is None:
        print("take photo")
        img = take_photo()
    # cv2.imwrite("/home/pi/TANE2025/image/"+"colour_scan.jpg", img)
    
    img_hls = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    img_th = hls_binary(img_hls, colour_range) # 条件を満たす要素を255，それ以外を0とする配列
    # cv2.imwrite("/home/pi/TANE2025/image/"+"scan.jpg", img_th)
    
    theta = scantheta(img_th)
    prop=scanprop(img_th)

    # カメラ試験用の出力
    print('theta = {}, prop = {}'.format(theta, prop))

    return theta, prop


if __name__ == "__main__":
    args = sys.argv
    for i in range(3):
        time.sleep(3-i)
    colour = [int(args[1]), int(args[2])]
    data = get_object_theta_and_proportion(colour)
    print('prop:{}'.format(data[1]))
    print('theta:{}'.format(data[0]))
