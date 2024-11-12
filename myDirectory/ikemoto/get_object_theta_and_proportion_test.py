from get_object_theta_and_proportion import get_object_theta_and_proportion
import cv2

colour_range = [160, 10]

data = get_object_theta_and_proportion(colour_range=colour_range, img=cv2.imread('yolo_image_sample.jpg'))
print('prop:{}'.format(data[1]))
print('theta:{}'.format(data[0]))