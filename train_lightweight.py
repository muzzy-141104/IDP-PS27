"""
Train Lightweight Crowd Counting Model
Optimized for 4GB GPU with pretrained backbone
Expected MAE < 100 with proper training
"""
import os
import time
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
from PIL import Image
import h5py
import matplotlib.pyplot as plt
from models.lightweight_crowd import CrowdCounter

# Setup seeds
def setup_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

setup_seed(42)


class CrowdDataset(Dataset):
    """Dataset for crowd counting with density maps"""
    def __init__(self, img_list, crop_size=256, train=True, flip=True):
        self.img_list = img_list
        self.crop_size = crop_size
        self.train = train
        self.flip = flip
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def __len__(self):
        return len(self.img_list)

    def __getitem__(self, idx):
        img_path = self.img_list[idx]
        gt_path = img_path.replace('.jpg', '.h5').replace('images', 'gt_density_map')

        # Load image
        img = Image.open(img_path).convert('RGB')
        orig_w, orig_h = img.size

        # Load proper Gaussian density map
        with h5py.File(gt_path, 'r') as gt_file:
            density_map = np.asarray(gt_file['density_map'], dtype=np.float32)

        # Get ground truth count
        gt_count = float(np.sum(density_map))

        # Data augmentation
        if self.train and self.flip and random.random() > 0.5:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
            density_map = np.fliplr(density_map).copy()

        # Resize image and density map to fixed size
        target_h = self.crop_size
        target_w = self.crop_size

        img = img.resize((target_w, target_h), Image.BILINEAR)
        density_map = np.array(Image.fromarray(density_map).resize((target_w, target_h), Image.BILINEAR))

        # Random crop
        if self.train:
            top = random.randint(0, max(0, target_h - self.crop_size))
            left = random.randint(0, max(0, target_w - self.crop_size))
        else:
            top, left = 0, 0

        # Convert to tensor
        img_tensor = self.transform(img)

        # Density map tensor - use raw values
        density_tensor = torch.from_numpy(density_map).unsqueeze(0).float()

        return img_tensor, density_tensor, gt_count


def count_points(density_map):
    """Count people from density map"""
    return int(torch.sum(density_map).item())


def train_model(model, train_loader, criterion, optimizer, device, epoch):
    model.train()
    total_loss = 0
    batch_count = 0

    for i, (imgs, density_maps, _) in enumerate(train_loader):
        imgs = imgs.to(device)
        density_maps = density_maps.to(device)

        optimizer.zero_grad()
        outputs = model(imgs)

        loss = criterion(outputs, density_maps)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        batch_count += 1

        if (i + 1) % 50 == 0:
            print(f"  Batch [{i+1}/{len(train_loader)}] - Loss: {loss.item():.4f}")

    return total_loss / batch_count


def validate_model(model, val_loader, device):
    """Evaluate model using MAE and MSE with sum-based counting"""
    model.eval()
    total_mae = 0
    total_mse = 0
    count = 0

    with torch.no_grad():
        for imgs, density_maps, gt_counts in val_loader:
            imgs = imgs.to(device)
            density_maps = density_maps.to(device)

            outputs = model(imgs)

            for j in range(len(outputs)):
                # Sum prediction to get count (density map approach)
                pred_count = torch.sum(outputs[j]).item()
                gt_count = gt_counts[j].item()

                mae = abs(pred_count - gt_count)
                mse = (pred_count - gt_count) ** 2
                total_mae += mae
                total_mse += mse
                count += 1

    return total_mae / count, np.sqrt(total_mse / count)


def main():
    # Config
    config = {
        'dataset': 'ShanghaiA',
        'save_path': 'save_file/lightweight_model',
        'batch_size': 8,  # Should fit in 4GB GPU
        'num_epochs': 200,
        'lr': 1e-4,
        'weight_decay': 5e-4,
        'crop_size': 256,
        'workers': 2,
        'val_interval': 5,
        'gpu_id': '0',
    }

    os.environ['CUDA_VISIBLE_DEVICES'] = config['gpu_id']

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    # Load data
    train_file = './npydata/ShanghaiA_train.npy'
    val_file = './npydata/ShanghaiA_test.npy'

    with open(train_file, 'rb') as f:
        train_list = np.load(f).tolist()
    with open(val_file, 'rb') as f:
        val_list = np.load(f).tolist()

    print(f"Train images: {len(train_list)}")
    print(f"Val images: {len(val_list)}")

    # Create datasets
    train_dataset = CrowdDataset(train_list, crop_size=config['crop_size'], train=True)
    val_dataset = CrowdDataset(val_list, crop_size=config['crop_size'], train=False)

    train_loader = DataLoader(train_dataset, batch_size=config['batch_size'],
                             shuffle=True, num_workers=config['workers'], pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=config['batch_size'],
                            shuffle=False, num_workers=config['workers'], pin_memory=True)

    # Create model
    print("\nCreating lightweight model with pretrained ResNet18...")
    model = CrowdCounter(load_weights=True).to(device)

    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params:,}")

    # Loss and optimizer
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=config['lr'], weight_decay=config['weight_decay'])
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=50, gamma=0.5)

    # Create save directory
    os.makedirs(config['save_path'], exist_ok=True)

    # Training loop
    print(f"\nStarting training for {config['num_epochs']} epochs...")
    print(f"Batch size: {config['batch_size']}, Learning rate: {config['lr']}")
    print("-" * 60)

    best_mae = float('inf')
    training_history = {'epoch': [], 'train_loss': [], 'val_mae': [], 'val_rmse': []}

    for epoch in range(config['num_epochs']):
        epoch_start = time.time()

        # Train
        train_loss = train_model(model, train_loader, criterion, optimizer, device, epoch)
        scheduler.step()

        epoch_time = time.time() - epoch_start

        print(f"Epoch {epoch+1}/{config['num_epochs']} - Loss: {train_loss:.4f} - Time: {epoch_time:.1f}s")

        # Validate
        if (epoch + 1) % config['val_interval'] == 0:
            val_mae, val_rmse = validate_model(model, val_loader, device)
            print(f"  -> Val MAE: {val_mae:.2f}, Val RMSE: {val_rmse:.2f}")

            training_history['epoch'].append(epoch + 1)
            training_history['train_loss'].append(train_loss)
            training_history['val_mae'].append(val_mae)
            training_history['val_rmse'].append(val_rmse)

            # Save best model
            if val_mae < best_mae:
                best_mae = val_mae
                torch.save({
                    'epoch': epoch + 1,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'best_mae': best_mae,
                    'config': config,
                }, os.path.join(config['save_path'], 'model_best.pth'))
                print(f"  -> New best model saved! MAE: {best_mae:.2f}")

        # Save latest checkpoint
        torch.save({
            'epoch': epoch + 1,
            'model_state_dict': model.state_dict(),
            'train_loss': train_loss,
            'config': config,
        }, os.path.join(config['save_path'], 'latest.pth'))

        # Save training history
        if len(training_history['epoch']) > 0:
            plt.figure(figsize=(10, 5))
            plt.subplot(1, 2, 1)
            plt.plot(training_history['epoch'], training_history['train_loss'], 'b-', label='Train Loss')
            plt.xlabel('Epoch')
            plt.ylabel('Loss')
            plt.title('Training Loss')
            plt.legend()
            plt.grid(True)

            plt.subplot(1, 2, 2)
            plt.plot(training_history['epoch'], training_history['val_mae'], 'r-', label='Val MAE')
            plt.plot(training_history['epoch'], training_history['val_rmse'], 'g-', label='Val RMSE')
            plt.xlabel('Epoch')
            plt.ylabel('Error')
            plt.title('Validation Metrics')
            plt.legend()
            plt.grid(True)

            plt.tight_layout()
            plt.savefig(os.path.join(config['save_path'], 'training_history.png'), dpi=150)
            plt.close()

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"Best validation MAE: {best_mae:.2f}")
    print(f"Models saved to: {config['save_path']}/")


if __name__ == '__main__':
    main()