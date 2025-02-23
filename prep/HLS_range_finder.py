import cv2
import numpy as np
import csv  # 追加

# HLSの範囲の初期値
hue_lower = 0
hue_upper = 180
sat_lower = 0
sat_upper = 255
light_lower = 0
light_upper = 255


# コールバック関数（スライダー用）
def nothing(x):
    pass


# ウィンドウの作成
cv2.namedWindow("HLS Range Detector")

# HLSの範囲を調整するスライダーの作成
cv2.createTrackbar("Hue Lower", "HLS Range Detector", hue_lower, 180, nothing)
cv2.createTrackbar("Hue Upper", "HLS Range Detector", hue_upper, 180, nothing)
cv2.createTrackbar("Saturation Lower", "HLS Range Detector", sat_lower, 255, nothing)
cv2.createTrackbar("Saturation Upper", "HLS Range Detector", sat_upper, 255, nothing)
cv2.createTrackbar("Lightness Lower", "HLS Range Detector", light_lower, 255, nothing)
cv2.createTrackbar("Lightness Upper", "HLS Range Detector", light_upper, 255, nothing)

# カメラのキャプチャ
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # BGRからHLSに変換
    hls_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HLS)

    # スライダーからのHLS範囲の取得
    h_lower = cv2.getTrackbarPos("Hue Lower", "HLS Range Detector")
    h_upper = cv2.getTrackbarPos("Hue Upper", "HLS Range Detector")
    s_lower = cv2.getTrackbarPos("Saturation Lower", "HLS Range Detector")
    s_upper = cv2.getTrackbarPos("Saturation Upper", "HLS Range Detector")
    l_lower = cv2.getTrackbarPos("Lightness Lower", "HLS Range Detector")
    l_upper = cv2.getTrackbarPos("Lightness Upper", "HLS Range Detector")

    # 二値化マスクの作成
    lower_hls = np.array([h_lower, l_lower, s_lower])  # HLSの順序
    upper_hls = np.array([h_upper, l_upper, s_upper])
    mask = cv2.inRange(hls_frame, lower_hls, upper_hls)

    # 結果の表示
    cv2.imshow("Original Frame", frame)
    cv2.imshow("HLS Mask", mask)

    # 'q'キーで終了
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# スライダーの値を取得
h_lower = cv2.getTrackbarPos("Hue Lower", "HLS Range Detector")
h_upper = cv2.getTrackbarPos("Hue Upper", "HLS Range Detector")
s_lower = cv2.getTrackbarPos("Saturation Lower", "HLS Range Detector")
s_upper = cv2.getTrackbarPos("Saturation Upper", "HLS Range Detector")
l_lower = cv2.getTrackbarPos("Lightness Lower", "HLS Range Detector")
l_upper = cv2.getTrackbarPos("Lightness Upper", "HLS Range Detector")

# スライダーの値をCSV形式でファイルに出力
with open("HLS_slider_values.csv", "w", newline="") as csvfile:
    csvwriter = csv.writer(csvfile)
    # ヘッダーの書き込み
    csvwriter.writerow(["Parameter", "Lower", "Upper"])
    # 値の書き込み
    csvwriter.writerow(["Hue", h_lower, h_upper])
    csvwriter.writerow(["Lightness", l_lower, l_upper])
    csvwriter.writerow(["Saturation", s_lower, s_upper])

# リソースの解放
cap.release()
cv2.destroyAllWindows()
