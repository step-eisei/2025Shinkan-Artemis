import cv2
import numpy as np
import csv

# HSVの範囲の初期値
hue_lower = 0
hue_upper = 180
sat_lower = 0
sat_upper = 255
val_lower = 0
val_upper = 255


# コールバック関数（スライダー用）
def nothing(x):
    pass


# ウィンドウの作成
cv2.namedWindow("HSV Range Detector")

# HSVの範囲を調整するスライダーの作成
cv2.createTrackbar("Hue Lower", "HSV Range Detector", hue_lower, 180, nothing)
cv2.createTrackbar("Hue Upper", "HSV Range Detector", hue_upper, 180, nothing)
cv2.createTrackbar("Saturation Lower", "HSV Range Detector", sat_lower, 255, nothing)
cv2.createTrackbar("Saturation Upper", "HSV Range Detector", sat_upper, 255, nothing)
cv2.createTrackbar("Value Lower", "HSV Range Detector", val_lower, 255, nothing)
cv2.createTrackbar("Value Upper", "HSV Range Detector", val_upper, 255, nothing)

# カメラのキャプチャ
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # BGRからHSVに変換
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # スライダーからのHSV範囲の取得
    h_lower = cv2.getTrackbarPos("Hue Lower", "HSV Range Detector")
    h_upper = cv2.getTrackbarPos("Hue Upper", "HSV Range Detector")
    s_lower = cv2.getTrackbarPos("Saturation Lower", "HSV Range Detector")
    s_upper = cv2.getTrackbarPos("Saturation Upper", "HSV Range Detector")
    v_lower = cv2.getTrackbarPos("Value Lower", "HSV Range Detector")
    v_upper = cv2.getTrackbarPos("Value Upper", "HSV Range Detector")

    # 二値化マスクの作成
    lower_hsv = np.array([h_lower, s_lower, v_lower])  # HSVの順序
    upper_hsv = np.array([h_upper, s_upper, v_upper])
    mask = cv2.inRange(hsv_frame, lower_hsv, upper_hsv)

    # 結果の表示
    cv2.imshow("Original Frame", frame)
    cv2.imshow("HSV Mask", mask)

    # 'q'キーで終了
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# スライダーの値を取得
h_lower = cv2.getTrackbarPos("Hue Lower", "HSV Range Detector")
h_upper = cv2.getTrackbarPos("Hue Upper", "HSV Range Detector")
s_lower = cv2.getTrackbarPos("Saturation Lower", "HSV Range Detector")
s_upper = cv2.getTrackbarPos("Saturation Upper", "HSV Range Detector")
v_lower = cv2.getTrackbarPos("Value Lower", "HSV Range Detector")
v_upper = cv2.getTrackbarPos("Value Upper", "HSV Range Detector")

# スライダーの値をCSV形式でファイルに出力
with open("HSV_slider_values.csv", "w", newline="") as csvfile:
    csvwriter = csv.writer(csvfile)
    # ヘッダーの書き込み
    csvwriter.writerow(["Parameter", "Lower", "Upper"])
    # 値の書き込み
    csvwriter.writerow(["Hue", h_lower, h_upper])
    csvwriter.writerow(["Saturation", s_lower, s_upper])
    csvwriter.writerow(["Value", v_lower, v_upper])

# リソースの解放
cap.release()
cv2.destroyAllWindows()
