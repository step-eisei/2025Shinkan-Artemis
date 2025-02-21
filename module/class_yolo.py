#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Copyright (c) Megvii, Inc. and its affiliates.
# TANE2025用class_yolo. NSE2023と同じようなインターフェースにしたつもり

import random
# from loguru import logger

import cv2
import numpy as np
import sys

import torch

sys.path.append("/home/pi/TANE2025/module/YOLOX/")
from yolox.data.data_augment import ValTransform
from yolox.data.datasets import COCO_CLASSES
from yolox.exp import get_exp
from yolox.utils import fuse_model, get_model_info, postprocess, vis

IMAGE_EXT = [".jpg", ".jpeg", ".webp", ".bmp", ".png"]

# Take photo
def take_photo(camera):
    ratio = 0.55
    # camera = cv2.VideoCapture(1, cv2.CAP_V4L2)
    camera.set(cv2.CAP_PROP_EXPOSURE, 1)

    success, image = camera.read()
    if not success:
        print("Failed 0n0")
        return -1
    # remove buffer
    for m in range(20):
        _, image = camera.read()
    image = cv2.flip(image, -1)

    #####
    # red_channel = np.clip(image[:, :, 2] *ratio, 0, 255)
    # red_channel = 255 / (1 + np.exp(-10 * (red_channel - 128) / 255))
    # image[:, :, 2] = red_channel
    #####
    return image

def clip_x(value):
    return max(min(int(value),640),0)

def clip_y(value):
    return max(min(int(value),480),0)


class CornDetect:
    def __init__(
            self,
            exp=get_exp('/home/pi/TANE2025/module/yolo_files/configfrom_yolox_s.py'),
            weights='/home/pi/TANE2025/module/yolo_files/cone/best_ckpt.pth',
            cls_names=COCO_CLASSES,
            decoder=None,
            device="cpu",
    ):
        self.weight = weights
        self.cls_names = cls_names
        self.decoder = decoder
        self.num_classes = exp.num_classes
        self.confthre = exp.test_conf
        self.nmsthre= exp.nmsthre
        self.test_size = exp.test_size
        self.device = device
        self.preproc = ValTransform(legacy=False)

        exp = get_exp('/home/pi/TANE2025/module/yolo_files/configfrom_yolox_s.py')
        exp.test_conf = 0.25
        exp.nmsthre = 0.45
        exp.test_size = (640, 640)
        self.model = exp.get_model()
        self.model.eval()
        ckpt = torch.load(weights, map_location="cpu")
        # load the model state dict
        self.model.load_state_dict(ckpt["model"])

        # Get names and colors
        self.names = ['person']
        self.colors = [[random.randint(0, 255) for _ in range(3)] for _ in self.names]
        self.count = 0

    # Start to estimate
    def estimate(self, img):
        # Initialize
        c1, c2 = [-1, -1], [-1, -1]
        temp_c1, temp_c2 = c1, c2
        tensor_img, _ = self.preproc(img, None, self.test_size)
        tensor_img = torch.from_numpy(tensor_img).unsqueeze(0)
        tensor_img = tensor_img.float()

        # Inference
        with torch.no_grad():
            outputs = self.model(tensor_img)
            print(outputs.shape)
            if self.decoder is not None:
                outputs = self.decoder(outputs, dtype=outputs.type())
            outputs = postprocess(
                outputs, self.num_classes, self.confthre,
                self.nmsthre, class_agnostic=True
            )

            # Process detections
            ratio = min(self.test_size[0] / img.shape[0], self.test_size[1] / img.shape[1])
            # print(outputs)
            max_score = 0
            max_score_idx = 0
            output = outputs[0]
            for i in range(len(output)):
                score = output[i][4] * output[i][5]
                print(f"{score=}")
                if score > max_score:
                    max_score = score
                    max_score_idx = i

            print(f"{max_score=}, {max_score_idx=}")
            output = outputs[0]
            if output is None:
                return c1, c2, img
            output = output.cpu()

            bboxes = output[:, 0:4]

            # preprocessing: resize
            bboxes /= ratio
            print(f"bboxes {bboxes}")
            c1 = [clip_x(bboxes[max_score_idx][0]), clip_y(bboxes[max_score_idx][1])]
            c2 = [clip_x(bboxes[max_score_idx][2]), clip_y(bboxes[max_score_idx][3])]
            cls = output[:, 6]
            scores = output[:, 4] * output[:, 5]

            img_res = vis(img, bboxes, scores, cls, 0.35, self.cls_names)

            return c1, c2, img_res
    
    def save_image(self, img, count):
        cv2.imwrite(f'output_{count}.jpg', img)


def main():
    exp = get_exp('/home/pi/TANE2025/module/yolo_files/configfrom_yolox_s.py')
    exp.test_conf = 0.25
    exp.nmsthre = 0.45
    exp.test_size = (640, 640)

    test = CornDetect(exp=exp)

    camera = cv2.VideoCapture(0)
    count = 0
    while True:
        image = take_photo(camera)
        #image = cv2.imread("Cone_0001.JPG")
        #image = cv2.imread('Cone_0002.JPG')
        c1, c2, estimated_image = test.estimate(img=image)
        print(c1, c2)
        #cv2.namedWindow('estimated_image', cv2.WINDOW_NORMAL)
        cv2.imshow('estimated_image', estimated_image)
        test.save_image(estimated_image, count)
        count += 1

        if cv2.waitKey(1) & 0xFF == ord('1'):
            break
        #key = cv2.waitKey(0)
        #cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
