"""
Lightweight Crowd Counting Model using pretrained ResNet18 encoder
Optimized for 4GB GPU - Expected MAE < 100 after proper training
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.models import resnet18, ResNet18_Weights


class CrowdCounter(nn.Module):
    """
    Lightweight CSRNet-style model with ResNet18 encoder
    Uses dilated convolutions for larger receptive field
    """
    def __init__(self, load_weights=True):
        super(CrowdCounter, self).__init__()

        # Load pretrained ResNet18 backbone
        resnet = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1 if load_weights else None)
        self.feature = nn.Sequential(*list(resnet.children())[:-2])  # Remove avgpool and fc

        # Feature dimensions after ResNet18: 512 channels
        self.front_end = nn.Sequential(
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
        )

        # Dilated layers for larger receptive field
        self.dilated1 = nn.Sequential(
            nn.Conv2d(512, 256, kernel_size=3, padding=2, dilation=2),
            nn.ReLU(inplace=True),
        )
        self.dilated2 = nn.Sequential(
            nn.Conv2d(256, 128, kernel_size=3, padding=2, dilation=2),
            nn.ReLU(inplace=True),
        )
        self.dilated3 = nn.Sequential(
            nn.Conv2d(128, 64, kernel_size=3, padding=2, dilation=2),
            nn.ReLU(inplace=True),
        )

        # Output layer - generates density map
        self.back_end = nn.Sequential(
            nn.Conv2d(64, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 1, kernel_size=1),
        )

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.normal_(m.weight, std=0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        # x: (B, 3, H, W)
        feature = self.feature(x)  # (B, 512, H/32, W/32)
        front = self.front_end(feature)  # (B, 512, H/32, W/32)
        d1 = self.dilated1(front)  # (B, 256, H/32, W/32)
        d2 = self.dilated2(d1)  # (B, 128, H/32, W/32)
        d3 = self.dilated3(d2)  # (B, 64, H/32, W/32)
        out = self.back_end(d3)  # (B, 1, H/32, W/32)

        # Upsample to original image size
        out = F.interpolate(out, size=(x.shape[2], x.shape[3]), mode='bilinear', align_corners=False)

        return out


class CrowdCounterV2(nn.Module):
    """
    Even lighter model using only first few layers of ResNet
    For very limited GPU memory
    """
    def __init__(self, load_weights=True):
        super(CrowdCounterV2, self).__init__()

        resnet = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1 if load_weights else None)
        # Use only first 4 layers of ResNet18
        self.feature = nn.Sequential(*list(resnet.children())[:4])

        self.conv1 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(128, 128, kernel_size=3, padding=2, dilation=2),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
        )
        self.conv3 = nn.Sequential(
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 32, kernel_size=1),
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.normal_(m.weight, std=0.01)
                if m.bias is not None:
                    nn.constant_(m.bias, 0)

    def forward(self, x):
        feature = self.feature(x)
        c1 = self.conv1(feature)
        c2 = self.conv2(c1)
        c3 = self.conv3(c2)
        out = F.interpolate(c3, size=(x.shape[2], x.shape[3]), mode='bilinear', align_corners=False)
        return out


if __name__ == '__main__':
    # Test model
    model = CrowdCounter()
    x = torch.randn(1, 3, 256, 256)
    y = model(x)
    print(f"Model output shape: {y.shape}")
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"GPU memory needed: ~{sum(p.numel() * 4 for p in model.parameters()) / 1024**2:.1f} MB")