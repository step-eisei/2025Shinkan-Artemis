import cv2

img = cv2.imread('yolo_image_sample.jpg')
img_hls = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

colour_range = [160, 10]
saturation_min = 100
v_min = 60
if colour_range[0] < colour_range[1]:
    img_th = cv2.inRange(img_hls, (colour_range[0], saturation_min, v_min), (colour_range[1], 250, 250))
else:
    mask1 = cv2.inRange(img_hls, (colour_range[0], saturation_min, v_min), (180, 250, 250))
    mask2 = cv2.inRange(img_hls, (0, saturation_min, v_min), (colour_range[1], 250, 250))
    img_th = cv2.bitwise_or(mask1, mask2)

print(img_th)
print(img_th.shape[1])

cv2.imwrite('output.jpg', img_th)
