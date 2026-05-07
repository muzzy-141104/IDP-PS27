from __future__ import division
import warnings
import os
import random

import torch
import torch.nn as nn
from Networks.HR_Net.seg_hrnet import get_seg_model
import torch.nn.functional as F
from torchvision import datasets, transforms
import dataset
import math
from image import *
from utils import *
import time

warnings.filterwarnings('ignore')

# Setup random seed
def setup_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)

setup_seed(1)


def main():
    # Training configuration - optimized for 4GB GPU
    args = {
        'dataset': 'ShanghaiA',
        'save_path': 'save_file/my_fidtm',
        'workers': 2,  # Reduced for stability
        'print_freq': 50,
        'start_epoch': 0,
        'epochs': 200,  # Reasonable number of epochs
        'pre': None,
        'batch_size': 1,  # Very small batch size for 4GB GPU
        'crop_size': 128,  # Smaller crop size to fit in memory
        'seed': 1,
        'best_pred': 1e5,
        'gpu_id': '0',
        'lr': 1e-4,
        'weight_decay': 5e-4,
        'preload_data': False,  # Don't preload - saves memory
        'visual': False,
        'video_path': None,
    }

    # Set GPU
    os.environ['CUDA_VISIBLE_DEVICES'] = args['gpu_id']

    # Load data list
    if args['dataset'] == 'ShanghaiA':
        train_file = './npydata/ShanghaiA_train.npy'
        test_file = './npydata/ShanghaiA_test.npy'

    with open(train_file, 'rb') as outfile:
        train_list = np.load(outfile).tolist()
    with open(test_file, 'rb') as outfile:
        test_list = np.load(outfile).tolist()

    print(f"Training images: {len(train_list)}")
    print(f"Test images: {len(test_list)}")

    # Build model
    print("Building model...")
    model = get_seg_model(train=True)
    model = nn.DataParallel(model, device_ids=[0])
    model = model.cuda()

    optimizer = torch.optim.Adam(
        [{'params': model.parameters(), 'lr': args['lr']}],
        lr=args['lr'],
        weight_decay=args['weight_decay']
    )

    criterion = nn.MSELoss(size_average=False).cuda()

    # Create save directory
    if not os.path.exists(args['save_path']):
        os.makedirs(args['save_path'])

    # Preload data
    if args['preload_data'] == True:
        print("Preloading training data...")
        train_data = pre_data(train_list, args, train=True)
        print("Preloading test data...")
        test_data = pre_data(test_list, args, train=False)
    else:
        train_data = train_list
        test_data = test_list

    print(f"\nStarting training for {args['epochs']} epochs...")
    print(f"Batch size: {args['batch_size']}")
    print(f"Learning rate: {args['lr']}")
    print(f"Save path: {args['save_path']}")

    for epoch in range(args['start_epoch'], args['epochs']):
        start = time.time()

        # Train
        train_loss = train(train_data, model, criterion, optimizer, epoch, args)
        end1 = time.time()

        # Validate every 10 epochs after epoch 50
        if epoch % 10 == 0 and epoch >= 50:
            mae, mse = validate(test_data, model, args)
            end2 = time.time()

            is_best = mae < args['best_pred']
            args['best_pred'] = min(mae, args['best_pred'])

            print(f' * Epoch {epoch} - MAE: {mae:.3f}, Best MAE: {args["best_pred"]:.3f}')
            print(f'   Train time: {end1 - start:.1f}s, Eval time: {end2 - end1:.1f}s')

            # Save checkpoint
            save_checkpoint({
                'epoch': epoch + 1,
                'state_dict': model.state_dict(),
                'best_prec1': args['best_pred'],
                'optimizer': optimizer.state_dict(),
            }, is_best, args['save_path'])
        else:
            print(f' * Epoch {epoch} - Loss: {train_loss:.4f}, Time: {end1 - start:.1f}s')

        # Adjust learning rate
        if epoch % 50 == 0 and epoch > 0:
            for param_group in optimizer.param_groups:
                param_group['lr'] = param_group['lr'] * 0.5
            print(f'   Learning rate adjusted to {optimizer.param_groups[0]["lr"]:.6f}')

    print(f"\nTraining complete! Best MAE: {args['best_pred']:.3f}")
    print(f"Model saved to: {args['save_path']}/")


def pre_data(train_list, args, train):
    print(f"Preloading {'train' if train else 'test'} dataset...")
    data_keys = {}
    count = 0
    for j in range(len(train_list)):
        Img_path = train_list[j]
        fname = os.path.basename(Img_path)
        img, fidt_map, kpoint = load_data_fidt(Img_path, args, train)

        if min(fidt_map.shape[0], fidt_map.shape[1]) < 256 and train == True:
            continue  # Skip small images
        blob = {}
        blob['img'] = img
        blob['kpoint'] = np.array(kpoint)
        blob['fidt_map'] = fidt_map
        blob['fname'] = fname
        data_keys[count] = blob
        count += 1

    print(f"  Loaded {count} images")
    return data_keys


def train(Pre_data, model, criterion, optimizer, epoch, args):
    losses = AverageMeter()
    batch_time = AverageMeter()
    data_time = AverageMeter()

    train_loader = torch.utils.data.DataLoader(
        dataset.listDataset(Pre_data, args['save_path'],
                           shuffle=True,
                           transform=transforms.Compose([
                               transforms.ToTensor(),
                               transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                                    std=[0.229, 0.224, 0.225]),
                           ]),
                           train=True,
                           batch_size=args['batch_size'],
                           num_workers=args['workers'],
                           args=args),
        batch_size=args['batch_size'], drop_last=False)

    print(f'Epoch {epoch}, processed {epoch * len(train_loader.dataset)} samples, lr {optimizer.param_groups[0]["lr"]:.6f}')

    model.train()
    end = time.time()

    for i, (fname, img, fidt_map, kpoint) in enumerate(train_loader):
        data_time.update(time.time() - end)
        img = img.cuda()
        fidt_map = fidt_map.type(torch.FloatTensor).unsqueeze(1).cuda()

        d6 = model(img)

        if d6.shape != fidt_map.shape:
            print(f"Shape mismatch! Prediction: {d6.shape}, GT: {fidt_map.shape}")
            exit()

        loss = criterion(d6, fidt_map)
        losses.update(loss.item(), img.size(0))

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        batch_time.update(time.time() - end)
        end = time.time()

        if i % args['print_freq'] == 0:
            print(f'  Batch [{i}/{len(train_loader)}] - '
                  f'Loss: {losses.val:.4f} ({losses.avg:.4f})')

    return losses.avg


def validate(Pre_data, model, args):
    print('Running validation...')
    test_loader = torch.utils.data.DataLoader(
        dataset.listDataset(Pre_data, args['save_path'],
                           shuffle=False,
                           transform=transforms.Compose([
                               transforms.ToTensor(),
                               transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                                                            std=[0.229, 0.224, 0.225]),
                           ]),
                           args=args, train=False),
        batch_size=1)

    model.eval()
    mae = 0.0
    mse = 0.0

    for i, (fname, img, fidt_map, kpoint) in enumerate(test_loader):
        img = img.cuda()

        if len(img.shape) == 5:
            img = img.squeeze(0)
        if len(fidt_map.shape) == 5:
            fidt_map = fidt_map.squeeze(0)
        if len(img.shape) == 3:
            img = img.unsqueeze(0)
        if len(fidt_map.shape) == 3:
            fidt_map = fidt_map.unsqueeze(0)

        with torch.no_grad():
            d6 = model(img)
            count, pred_kpoint = LMDS_counting(d6, args)

        gt_count = torch.sum(kpoint).item()
        mae += abs(gt_count - count)
        mse += abs(gt_count - count) * abs(gt_count - count)

    mae = mae / len(test_loader)
    mse = math.sqrt(mse / len(test_loader))

    return mae, mse


def LMDS_counting(input, args):
    input_max = torch.max(input).item()

    keep = nn.functional.max_pool2d(input, (3, 3), stride=1, padding=1)
    keep = (keep == input).float()
    input = keep * input

    input[input < 100.0 / 255.0 * input_max] = 0
    input[input > 0] = 1

    if input_max < 0.1:
        input = input * 0

    count = int(torch.sum(input).item())
    return count, None


def save_checkpoint(state, is_best, save_path):
    filepath = os.path.join(save_path, 'latest_model.pth')
    torch.save(state, filepath)
    if is_best:
        bestpath = os.path.join(save_path, 'model_best_nwpu.pth')
        torch.save(state, bestpath)
        print(f'  -> New best model saved!')


class AverageMeter(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count


if __name__ == '__main__':
    main()