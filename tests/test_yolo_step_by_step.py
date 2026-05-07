"""
Step-by-step YOLO Crowd Counting Test
Tests YOLO model on images and videos with clear output.
"""
import os
import sys
from pathlib import Path
import numpy as np
import cv2
import torch

# Setup paths
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# Model and test file paths
YOLO_WEIGHTS = ROOT / "yolo-crowd.pt"
TEST_IMAGE = ROOT / "data/images/zidane.jpg"
TEST_VIDEO = ROOT / "static/15765176_720_1280_60fps.mp4"


def test_yolo_image():
    """Test YOLO on a single image."""
    from models.common import DetectMultiBackend
    from utils.datasets import letterbox
    from utils.general import non_max_suppression
    from utils.torch_utils import select_device

    print("\n" + "="*60)
    print("TEST 1: YOLO Image Inference")
    print("="*60)

    # Load model
    device = select_device('')
    model = DetectMultiBackend(str(YOLO_WEIGHTS), device=device, dnn=False)
    stride = model.stride
    names = model.names

    print(f"\nModel loaded: YOLO-CROWD")
    print(f"Device: {device}")
    print(f"Input image: {TEST_IMAGE}")

    # Read image
    img0 = cv2.imread(str(TEST_IMAGE))
    if img0 is None:
        print(f"ERROR: Could not read image {TEST_IMAGE}")
        return None

    print(f"Image shape: {img0.shape}")

    # Preprocess
    img = letterbox(img0, 640, stride=stride, auto=False)[0]
    img = img.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
    img = np.ascontiguousarray(img)
    img = torch.from_numpy(img).to(device)
    img = img.float() / 255.0
    if len(img.shape) == 3:
        img = img[None]

    # Warmup
    model.warmup(imgsz=(1, 3, 640, 640))

    # Inference
    pred = model(img)

    # NMS
    pred = non_max_suppression(pred[0], conf_thres=0.25, iou_thres=0.45)

    # Count detections (class 0 = person in COCO)
    n = 0
    for i, det in enumerate(pred):
        if len(det):
            n = (det[:, 5] == 0).sum()
            print(f"\nDetections found: {len(det)}")
            # Show per-class counts
            for c in det[:, 5].unique():
                count = (det[:, 5] == c).sum()
                print(f"  Class {int(c)} ({names[int(c)]}): {count}")

    count = n.item() if torch.is_tensor(n) else n

    print(f"\n*** Total People Count: {count} ***")

    # Save result image with bounding boxes
    annotator = Annotator(img0, line_width=2, example=str(names))
    if len(pred[0]):
        det[:, :4] = scale_boxes(img.shape[2:], det[:, :4], img0.shape).round()
        for *xyxy, conf, cls in reversed(pred[0]):
            c = int(cls)
            label = f'{names[c]} {conf:.2f}'
            annotator.box_label(xyxy, label, color=(0, 255, 0))

    result_img = annotator.result()
    output_path = ROOT / "static/yolo_result.jpg"
    cv2.imwrite(str(output_path), result_img)
    print(f"Result saved to: {output_path}")

    return count


def test_yolo_video():
    """Test YOLO on first 5 frames of video."""
    from models.common import DetectMultiBackend
    from utils.datasets import letterbox
    from utils.general import non_max_suppression
    from utils.torch_utils import select_device

    print("\n" + "="*60)
    print("TEST 2: YOLO Video Inference")
    print("="*60)

    # Load model
    device = select_device('')
    model = DetectMultiBackend(str(YOLO_WEIGHTS), device=device, dnn=False)
    stride = model.stride
    names = model.names

    print(f"\nModel loaded: YOLO-CROWD")
    print(f"Device: {device}")
    print(f"Input video: {TEST_VIDEO}")

    # Open video
    cap = cv2.VideoCapture(str(TEST_VIDEO))
    if not cap.isOpened():
        print(f"ERROR: Could not open video {TEST_VIDEO}")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Video info: {width}x{height} @ {fps}fps")

    # Process 5 frames
    frame_counts = []
    for frame_idx in range(5):
        ret, frame = cap.read()
        if not ret:
            print(f"Failed to read frame {frame_idx}")
            break

        # Preprocess
        img = letterbox(frame, 640, stride=stride, auto=False)[0]
        img = img.transpose((2, 0, 1))[::-1]
        img = np.ascontiguousarray(img)
        img = torch.from_numpy(img).to(device)
        img = img.float() / 255.0
        if len(img.shape) == 3:
            img = img[None]

        # Inference
        pred = model(img)
        pred = non_max_suppression(pred[0], conf_thres=0.25, iou_thres=0.45)

        # Count
        n = 0
        for det in pred:
            if len(det):
                n = (det[:, 5] == 0).sum()

        count = n.item() if torch.is_tensor(n) else n
        frame_counts.append(count)
        print(f"  Frame {frame_idx + 1}: {count} people")

    cap.release()

    print(f"\n*** Frame counts: {frame_counts} ***")
    print(f"*** Average: {np.mean(frame_counts):.1f} people/frame ***")

    return frame_counts


def scale_boxes(img1_shape, coords, img0_shape, ratio_pad=None):
    """Rescale boxes from img1_shape to img0_shape."""
    if ratio_pad is None:
        gain = min(img1_shape[0] / img0_shape[0], img1_shape[1] / img0_shape[1])
        pad = ((img1_shape[1] - img0_shape[1] * gain) / 2, (img1_shape[0] - img0_shape[0] * gain) / 2)
    else:
        gain = ratio_pad[0][0]
        pad = ratio_pad[1]
    coords[:, [0, 2]] -= pad[0]
    coords[:, [1, 3]] -= pad[1]
    coords[:, :4] /= gain
    coords[:, 0].clamp_(0, img0_shape[1])
    coords[:, 1].clamp_(0, img0_shape[0])
    coords[:, 2].clamp_(0, img0_shape[1])
    coords[:, 3].clamp_(0, img0_shape[0])
    return coords


class Annotator:
    def __init__(self, img, line_width=None, font_size=None, example=None):
        self.im = img.copy()
        self.line_width = line_width or 2

    def box_label(self, box, label=None, color=(0, 255, 0)):
        p1 = (int(box[0]), int(box[1]))
        p2 = (int(box[2]), int(box[3]))
        cv2.rectangle(self.im, p1, p2, color, thickness=self.line_width)
        if label:
            tf = max(self.line_width - 1, 1)
            w, h = cv2.getTextSize(label, 0, fontScale=self.line_width / 3, thickness=tf)[0]
            outside = p1[1] - h >= 3
            p2_label = (p1[0] + w, p1[1] - h - 3 if outside else p1[1] + h + 3)
            cv2.rectangle(self.im, p1, p2_label, color, -1, cv2.LINE_AA)
            cv2.putText(self.im, label, (p1[0], p1[1] - 2 if outside else p1[1] + h + 2),
                        0, self.line_width / 3, (255, 255, 255), thickness=tf, lineType=cv2.LINE_AA)

    def result(self):
        return self.im


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# YOLO CROWD COUNTING - STEP BY STEP TEST")
    print("#"*60)

    # Check files exist
    print("\nChecking files...")
    print(f"  YOLO weights exists: {YOLO_WEIGHTS.exists()}")
    print(f"  Test image exists: {TEST_IMAGE.exists()}")
    print(f"  Test video exists: {TEST_VIDEO.exists()}")

    # Run tests
    try:
        image_count = test_yolo_image()
        video_counts = test_yolo_video()

        print("\n" + "#"*60)
        print("# SUMMARY")
        print("#"*60)
        print(f"  Image test (zidane.jpg): {image_count} people detected")
        print(f"  Video test (first 5 frames): {video_counts}")
        if video_counts:
            print(f"  Video average: {np.mean(video_counts):.1f} people/frame")
        print("#"*60)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
