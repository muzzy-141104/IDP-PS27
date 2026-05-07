"""
Unit tests for CSRNet and YOLO crowd counting models on images and videos.
"""
import os
import sys
import unittest
import tempfile
import shutil
import numpy as np
from pathlib import Path

# Add project root to path
FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]  # Go up two levels: tests -> project root
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# Test fixtures paths
TEST_IMAGE = ROOT / "ShanghaiTech/part_A/test_data/images/IMG_1.jpg"
TEST_VIDEO = ROOT / "static/15765176_720_1280_60fps.mp4"
YOLO_WEIGHTS = ROOT / "yolo-crowd.pt"
CSRNET_WEIGHTS = ROOT / "modelCRNet.pt"


class TestCSRNetInference(unittest.TestCase):
    """Test CSRNet model inference on images and videos."""

    @classmethod
    def setUpClass(cls):
        """Load model once for all tests."""
        import torch
        from pythonModel import CSRNet
        from torchvision import transforms

        # Use load_weights=True to skip broken vgg16 pretrained loading
        cls.model = CSRNet(load_weights=True)
        cls.model.eval()
        # Load trained weights separately (with weights_only=True for safety)
        state_dict = torch.load(str(CSRNET_WEIGHTS), map_location='cpu', weights_only=True)
        cls.model.load_state_dict(state_dict)
        cls.model.eval()
        cls.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def test_csrnet_image_inference(self):
        """Test CSRNet inference on a single image."""
        from PIL import Image
        import torch

        self.assertTrue(TEST_IMAGE.exists(), f"Test image not found: {TEST_IMAGE}")

        img = Image.open(TEST_IMAGE).convert('RGB')
        img_tensor = self.transform(img)

        with torch.no_grad():
            output = self.model(img_tensor.unsqueeze(0))

        prediction = int(output.detach().cpu().sum().numpy())

        self.assertIsInstance(prediction, int)
        self.assertGreaterEqual(prediction, 0)
        print(f"\n[CSRNet Image] Prediction count: {prediction}")

    def test_csrnet_video_frame_inference(self):
        """Test CSRNet inference on a single frame from video."""
        import cv2
        import torch

        self.assertTrue(TEST_VIDEO.exists(), f"Test video not found: {TEST_VIDEO}")

        cap = cv2.VideoCapture(str(TEST_VIDEO))
        ret, frame = cap.read()
        cap.release()

        self.assertTrue(ret, "Failed to read frame from video")

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_tensor = self.transform(frame_rgb)

        with torch.no_grad():
            output = self.model(img_tensor.unsqueeze(0))

        prediction = int(output.detach().cpu().sum().numpy())

        self.assertIsInstance(prediction, int)
        self.assertGreaterEqual(prediction, 0)
        print(f"\n[CSRNet Video Frame] Prediction count: {prediction}")

    def test_csrnet_multiple_frames(self):
        """Test CSRNet on multiple consecutive frames from video."""
        import cv2
        import torch

        self.assertTrue(TEST_VIDEO.exists(), f"Test video not found: {TEST_VIDEO}")

        cap = cv2.VideoCapture(str(TEST_VIDEO))
        frame_counts = []

        for _ in range(5):
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_tensor = self.transform(frame_rgb)

            with torch.no_grad():
                output = self.model(img_tensor.unsqueeze(0))

            prediction = int(output.detach().cpu().sum().numpy())
            frame_counts.append(prediction)

        cap.release()

        self.assertEqual(len(frame_counts), 5)
        for count in frame_counts:
            self.assertIsInstance(count, int)
            self.assertGreaterEqual(count, 0)

        print(f"\n[CSRNet Multiple Frames] Counts: {frame_counts}")


class TestYOLOInference(unittest.TestCase):
    """Test YOLO model inference on images and videos."""

    @classmethod
    def setUpClass(cls):
        """Load model once for all tests."""
        from models.common import DetectMultiBackend
        from utils.torch_utils import select_device

        cls.device = select_device('')
        cls.model = DetectMultiBackend(
            str(YOLO_WEIGHTS),
            device=cls.device,
            dnn=False,
            data=str(ROOT / 'data/coco128.yaml'),
            fp16=False
        )
        cls.stride = cls.model.stride
        cls.names = cls.model.names
        cls.pt = cls.model.pt

    def test_yolo_image_inference(self):
        """Test YOLO inference on a single image."""
        import torch
        import cv2
        from utils.datasets import letterbox
        from utils.general import non_max_suppression

        self.assertTrue(TEST_IMAGE.exists(), f"Test image not found: {TEST_IMAGE}")

        frame = cv2.imread(str(TEST_IMAGE))
        self.assertIsNotNone(frame, "Failed to read image")

        # Preprocess
        im = letterbox(frame, 640, stride=self.stride, auto=False)[0]
        im = im.transpose((2, 0, 1))[::-1]
        im = np.ascontiguousarray(im)
        im = torch.from_numpy(im).to(self.device)
        im = im.float()
        im /= 255
        if len(im.shape) == 3:
            im = im[None]

        # Inference
        with torch.no_grad():
            pred = self.model(im)

        # NMS
        pred = non_max_suppression(pred[0], conf_thres=0.25, iou_thres=0.45)

        # Count detections
        n = 0
        for i, det in enumerate(pred):
            if len(det):
                n = (det[:, 5] == 0).sum()  # class 0 is person in COCO

        prediction = n.item() if torch.is_tensor(n) else n

        self.assertIsInstance(prediction, int)
        self.assertGreaterEqual(prediction, 0)
        print(f"\n[YOLO Image] Detection count: {prediction}")

    def test_yolo_video_frame_inference(self):
        """Test YOLO inference on a single frame from video."""
        import torch
        import cv2
        from utils.datasets import letterbox
        from utils.general import non_max_suppression

        self.assertTrue(TEST_VIDEO.exists(), f"Test video not found: {TEST_VIDEO}")

        cap = cv2.VideoCapture(str(TEST_VIDEO))
        ret, frame = cap.read()
        cap.release()

        self.assertTrue(ret, "Failed to read frame from video")

        # Preprocess
        im = letterbox(frame, 640, stride=self.stride, auto=False)[0]
        im = im.transpose((2, 0, 1))[::-1]
        im = np.ascontiguousarray(im)
        im = torch.from_numpy(im).to(self.device)
        im = im.float()
        im /= 255
        if len(im.shape) == 3:
            im = im[None]

        # Inference
        with torch.no_grad():
            pred = self.model(im)

        # NMS
        pred = non_max_suppression(pred[0], conf_thres=0.25, iou_thres=0.45)

        # Count detections
        n = 0
        for i, det in enumerate(pred):
            if len(det):
                n = (det[:, 5] == 0).sum()

        prediction = n.item() if torch.is_tensor(n) else n

        self.assertIsInstance(prediction, int)
        self.assertGreaterEqual(prediction, 0)
        print(f"\n[YOLO Video Frame] Detection count: {prediction}")

    def test_yolo_multiple_frames(self):
        """Test YOLO on multiple consecutive frames from video."""
        import torch
        import cv2
        from utils.datasets import letterbox
        from utils.general import non_max_suppression

        self.assertTrue(TEST_VIDEO.exists(), f"Test video not found: {TEST_VIDEO}")

        cap = cv2.VideoCapture(str(TEST_VIDEO))
        frame_counts = []

        for _ in range(5):
            ret, frame = cap.read()
            if not ret:
                break

            # Preprocess
            im = letterbox(frame, 640, stride=self.stride, auto=False)[0]
            im = im.transpose((2, 0, 1))[::-1]
            im = np.ascontiguousarray(im)
            im = torch.from_numpy(im).to(self.device)
            im = im.float()
            im /= 255
            if len(im.shape) == 3:
                im = im[None]

            # Inference
            with torch.no_grad():
                pred = self.model(im)

            # NMS
            pred = non_max_suppression(pred[0], conf_thres=0.25, iou_thres=0.45)

            # Count detections
            n = 0
            for i, det in enumerate(pred):
                if len(det):
                    n = (det[:, 5] == 0).sum()

            prediction = n.item() if torch.is_tensor(n) else n
            frame_counts.append(prediction)

        cap.release()

        self.assertEqual(len(frame_counts), 5)
        for count in frame_counts:
            self.assertIsInstance(count, int)
            self.assertGreaterEqual(count, 0)

        print(f"\n[YOLO Multiple Frames] Counts: {frame_counts}")


class TestModelComparison(unittest.TestCase):
    """Compare CSRNet and YOLO results on same inputs."""

    @classmethod
    def setUpClass(cls):
        """Load both models once."""
        import torch
        from pythonModel import CSRNet
        from torchvision import transforms
        from models.common import DetectMultiBackend
        from utils.torch_utils import select_device

        # CSRNet
        cls.csrnet_model = CSRNet(load_weights=True)
        state_dict = torch.load(str(CSRNET_WEIGHTS), map_location='cpu', weights_only=True)
        cls.csrnet_model.load_state_dict(state_dict)
        cls.csrnet_model.eval()
        cls.csrnet_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        # YOLO
        cls.device = select_device('')
        cls.yolo_model = DetectMultiBackend(
            str(YOLO_WEIGHTS),
            device=cls.device,
            dnn=False,
            data=str(ROOT / 'data/coco128.yaml'),
            fp16=False
        )
        cls.yolo_stride = cls.yolo_model.stride

    def test_same_input_comparison(self):
        """Compare both models on the same image."""
        import torch
        import cv2
        from utils.datasets import letterbox
        from utils.general import non_max_suppression

        self.assertTrue(TEST_IMAGE.exists(), f"Test image not found: {TEST_IMAGE}")

        # CSRNet inference
        frame = cv2.imread(str(TEST_IMAGE))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        csrnet_tensor = self.csrnet_transform(frame_rgb)
        with torch.no_grad():
            csrnet_output = self.csrnet_model(csrnet_tensor.unsqueeze(0))
        csrnet_count = int(csrnet_output.detach().cpu().sum().numpy())

        # YOLO inference
        im = letterbox(frame, 640, stride=self.yolo_stride, auto=False)[0]
        im = im.transpose((2, 0, 1))[::-1]
        im = np.ascontiguousarray(im)
        im = torch.from_numpy(im).to(self.device)
        im = im.float()
        im /= 255
        if len(im.shape) == 3:
            im = im[None]

        with torch.no_grad():
            yolo_pred = self.yolo_model(im)
        yolo_pred = non_max_suppression(yolo_pred[0], conf_thres=0.25, iou_thres=0.45)

        yolo_count = 0
        for det in yolo_pred:
            if len(det):
                yolo_count = (det[:, 5] == 0).sum()
        yolo_count = yolo_count.item() if torch.is_tensor(yolo_count) else yolo_count

        print(f"\n[Model Comparison on IMG_1.jpg]")
        print(f"  CSRNet count: {csrnet_count}")
        print(f"  YOLO count: {yolo_count}")

        self.assertIsInstance(csrnet_count, int)
        self.assertIsInstance(yolo_count, int)


if __name__ == '__main__':
    print("=" * 60)
    print("Running Crowd Counting Model Tests")
    print("=" * 60)

    # Run tests with verbosity
    unittest.main(verbosity=2)
