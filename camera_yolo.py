import argparse
import os
import platform
import sys
from pathlib import Path

import random
import torch
import numpy as np
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from models.common import DetectMultiBackend
# from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadScreenshots, LoadStreams
from utils.general import (check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression as real_nms, strip_optimizer, xyxy2xywh)

# Stub for scale_coords/scale_boxes
def scale_coords(img1_shape, coords, img0_shape, ratio_pad=None):
    return coords

def scale_boxes(img1_shape, coords, img0_shape, ratio_pad=None):
    """Rescale coords (xyxy) from img1_shape to img0_shape."""
    if ratio_pad is None:
        gain = min(img1_shape[0] / img0_shape[0], img1_shape[1] / img0_shape[1])
        pad = ((img1_shape[1] - img0_shape[1] * gain) / 2, (img1_shape[0] - img0_shape[0] * gain) / 2)
    else:
        gain = ratio_pad[0][0]
        pad = ratio_pad[1]
    coords[:, [0, 2]] -= pad[0]  # x padding
    coords[:, [1, 3]] -= pad[1]  # y padding
    coords[:, :4] /= gain
    # Clip to image bounds
    coords[:, 0].clamp_(0, img0_shape[1])  # x1
    coords[:, 1].clamp_(0, img0_shape[0])  # y1
    coords[:, 2].clamp_(0, img0_shape[1])  # x2
    coords[:, 3].clamp_(0, img0_shape[0])  # y2
    return coords

# Stub for Annotator
class Annotator:
    def __init__(self, img, line_width=None, font_size=None, example=None):
        self.img = img
        self.line_width = line_width
    def box_label(self, box, label=None, color=None):
        pass
    def result(self):
        return self.img
    def result(self):
        return self.img

# Stub for colors
def colors(c, validate=True):
    return (0, 255, 0)  # green

# Define stubs for missing utilities
LOGGER = None
class Profile:
    def __init__(self):
        self.dt = [0, 0, 0]
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
from utils.torch_utils import select_device

# smart_inference_mode stub
def smart_inference_mode():
    def decorator(fn):
        return fn
    return decorator
import glob
import hashlib
import json
import math
import os
import random
import shutil
import time
from itertools import repeat
from multiprocessing.pool import Pool, ThreadPool
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

import numpy as np
import psutil
import torch
import torch.nn.functional as F
import torchvision
import yaml
from PIL import ExifTags, Image, ImageOps
from torch.utils.data import DataLoader, Dataset, dataloader, distributed
from tqdm import tqdm

from utils.datasets import letterbox
from utils.general import cv2
from numpy import random

def segments2boxes(segments):
    return np.zeros((len(segments), 4))

def xyn2xy(x, w=640, h=640, padw=0, padh=0):
    return x

def xywh2xyxy(x):
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[:, 0] = x[:, 0] - x[:, 2] / 2
    y[:, 1] = x[:, 1] - x[:, 3] / 2
    y[:, 2] = x[:, 0] + x[:, 2] / 2
    y[:, 3] = x[:, 1] + x[:, 3] / 2
    return y

def xywhn2xyxy(x, w=640, h=640, padw=0, padh=0):
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[:, 0] = x[:, 0] * w + padw
    y[:, 1] = x[:, 1] * h + padh
    y[:, 2] = x[:, 2] * w + padw
    y[:, 3] = x[:, 3] * h + padh
    return y

def xyxy2xywhn(x, w=640, h=640, padw=0, padh=0):
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[:, 0] = (x[:, 0] - padw) / w
    y[:, 1] = (x[:, 1] - padh) / h
    y[:, 2] = (x[:, 2] - padw) / w
    y[:, 3] = (x[:, 3] - padh) / h
    return y

def xyxy2xywh(x):
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[:, 0] = (x[:, 0] + x[:, 2]) / 2
    y[:, 1] = (x[:, 1] + x[:, 3]) / 2
    y[:, 2] = x[:, 2] - x[:, 0]
    y[:, 3] = x[:, 3] - x[:, 1]
    return y

def non_max_suppression(prediction, conf_thres=0.25, iou_thres=0.45, classes=None, agnostic=False, multi_label=False,
                        labels=(), max_det=1000):
    return real_nms(prediction, conf_thres, iou_thres)

device = select_device('')
weights='./yolo-crowd.pt'
model = DetectMultiBackend(weights, device=device, dnn=False, data=ROOT /'data/coco128.yaml', fp16=False)


class VideoCamera(object):
    weights='./yolo-crowd.pt'  # model path or triton URL
    source=ROOT / 'data/images'  # file/dir/URL/glob/screen/0(webcam)
    data=ROOT / 'data/coco128.yaml'  # dataset.yaml path
    imgsz=(640, 640)  # inference size (height, width)
    conf_thres=0.25  # confidence threshold
    iou_thres=0.45  # NMS IOU threshold
    max_det=1000  # maximum detections per image
    device=''  # cuda device, i.e. 0 or 0,1,2,3 or cpu
    view_img=False  # show results
    save_txt=False  # save results to *.txt
    save_conf=False  # save confidences in --save-txt labels
    save_crop=False  # save cropped prediction boxes
    nosave=False  # do not save images/videos
    classes=None  # filter by class: --class 0, or --class 0 2 3
    agnostic_nms=False  # class-agnostic NMS
    augment=False  # augmented inference
    visualize=False  # visualize features
    update=False  # update all models
    project=ROOT / 'runs/detect'  # save results to project/name
    name='exp'  # save results to project/name
    exist_ok=False  # existing project/name ok, do not increment
    line_thickness=3  # bounding box thickness (pixels)
    hide_labels=False  # hide labels
    hide_conf=False  # hide confidences
    half=False  # use FP16 half-precision inference
    dnn=False  # use OpenCV DNN for ONNX inference
    vid_stride=1  # video frame-rate stride
    def __init__(self,fileName):
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        if (fileName ==''):
            self.video = cv2.VideoCapture(0)
        else:  
            self.video = cv2.VideoCapture(fileName)
            self.video.set(cv2.CAP_PROP_BUFFERSIZE, 1)
#        self.video = cv2.resize(self.video,(840,640))
        # If you decide to use video.mp4, you must have this file in the folder
        # as the main.py.
        # self.video = cv2.VideoCapture('video.mp4')
    
    def __del__(self):
        self.video.release()

    def release(self):
        self.video.release()

    def get_frame(self):
        
        cap =self.video 
      
      
      
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
    #fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')

    #cap = cv2.VideoCapture(args.video_path)
    #cap= cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
 
        ret, frame = cap.read()
        print(frame.shape)

        '''out video'''
        width = frame.shape[1] #output size
        height = frame.shape[0] #output size
        out = cv2.VideoWriter('./demo.avi', fourcc, 30, (width, height))

        

    
        
        stride, names, pt = 32, model.names, model.pt
        imgsz = check_img_size(640, s=stride)  # returns integer (e.g., 640)
        imgsz = (imgsz, imgsz)  # convert to tuple for warmup and letterbox

        
        
            

        while True:
            try:
                ret, frame = cap.read()

                scale_factor = 0.5
                frame = cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor)
                ori_img = frame.copy()
            except:
                print("test end")
                cap.release()
                break
            frame = frame.copy()
            source = str(frame)

            bs = 1  # batch_size

            with torch.no_grad():

                # Run inference
                model.warmup(imgsz=(1 if pt or model.triton else bs, 3, *imgsz))  # warmup
                seen, windows, dt = 0, [], (Profile(), Profile(), Profile())
                with dt[0]:
                    im = letterbox(frame, 640, stride=32, auto=False)[0]  # padded resize to square
                    im = im.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
                    im = np.ascontiguousarray(im)
                    im = torch.from_numpy(im).to(model.device)
                    im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
                    im /= 255  # 0 - 255 to 0.0 - 1.0
                    if len(im.shape) == 3:
                        im = im[None]  # expand for batch dim

                    # Inference
                with dt[1]:
                    pred = model(im, augment=False)

                    # NMS
                with dt[2]:
                    pred = non_max_suppression(pred[0], 0.25, 0.45, None, False, max_det=1000)

                    # Second-stage classifier (optional)
                    # pred = utils.general.apply_classifier(pred, classifier_model, im, im0s)

                    # Process predictions
                for i, det in enumerate(pred):  # per image
                    seen += 1
                    #p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)

                    #p = Path(p)  # to Path
                    #s += '%gx%g ' % im.shape[2:]  # print string
                    gn = torch.tensor(frame.shape)[[1, 0, 1, 0]]  # normalization gain whwh
                    annotator = Annotator(frame, line_width=1,font_size=1, example=str(names))
                    n=0
                    if len(det):
                        # Rescale boxes from img_size to im0 size
                        det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], frame.shape).round()

                        # Print results
                        for c in det[:, 5].unique():
                            n = (det[:, 5] == c).sum()  # detections per class
                            #s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string
                        for *xyxy, conf, cls in reversed(det):
                            c = int(cls.item())  # integer class
                            label = f'{names[c]} {conf.item():.02f}'
                            annotator.box_label(xyxy, label, color=colors(c, True))

                                
                    # Stream results
                    im0 = annotator.result()
                    if torch.is_tensor(n):
                        prediction = n.item()
                    else:
                        prediction = n
                    
                    try:
                        from drishti.backend.count_ws import update_latest_count
                        # Run event loop execution to properly evaluate the alert asynchronously
                        # Wait, update_latest_count is sync, but the alert_manager is async
                        # Actually, we just need to pass the raw count. The stream routing is separate.
                        # Wait, `count_ws.update_latest_count` doesn't do async alerts directly, we can just push the count.
                        update_latest_count(int(prediction), "yolo", None, "stream")
                    except ImportError:
                        pass
                    except Exception as e:
                        print("Failed to emit live count:", e)

                    img_to_draw = cv2.resize(im0, (1500,720))
                    cv2.putText(img_to_draw, 'Number of people=' + str(prediction), (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                    res = img_to_draw
                    im0 = annotator.result()
                    if torch.is_tensor(n):
                        prediction = n.item()
                    else:
                        prediction = n
                        
                    res = img_to_draw

                        # We are using Motion JPEG, but OpenCV defaults to capture raw images,
        # so we must encode it into JPEG in order to correctly display the
        # video stream.
                ret, jpeg = cv2.imencode('.jpg', res)
        
        
        
                return jpeg.tobytes()


                

                
 
     
        
