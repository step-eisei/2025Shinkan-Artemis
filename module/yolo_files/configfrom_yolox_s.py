#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Copyright (c) Megvii, Inc. and its affiliates.

import os

from yolox.exp import Exp as MyExp


class Exp(MyExp):
    def __init__(self):
        super(Exp, self).__init__()
        self.depth = 0.33
        self.width = 0.50
        self.exp_name = os.path.split(os.path.realpath(__file__))[1].split(".")[0]
        self.data_dir = "/content/drive/MyDrive/YOLOX_STEP/datasets"
        self.train_ann = "train.json"#"train.json"
        self.val_ann = "valid.json"#"valid.json"
        self.num_classes = 1
