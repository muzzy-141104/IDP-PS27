"""
FIDTM Training without validation - continuous training
Avoids validation crashes by only training
"""
from __future__ import division
import warnings
import os
import random
import time

import torch
import torch.nn as nn
import torchvision.transforms as transforms
from Networks.HR_Net.seg_hrnet import get_seg_model
import dataset
import math
from image import *

warnings.filterwarnings('ignore')

# Setup random seed
def setup_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

setup_seed(1)


def main():
    args = {
        'save_path': 'save_file/my_fidtm',
        'workers': 1,
        'print_freq': 100,
        'start_epoch': 179,  # Continue from where we left off
        'epochs': 400,
        'pre': 'save_file/my_fidtm/latest_model.pth',
        'batch_size': 1,
        'crop_size': 128,
        'seed': 1,
        'best_pred': 1502.8,
        'gpu_id': '0',
        'lr': 3e-5,  # Lower LR for fine-tuning
        'weight_decay': 5e-4,
    }

    os.environ['CUDA_VISIBLE_DEVICES'] = args['gpu_id']

    if args['dataset'] == 'ShanghaiA':
        train_file = './npydata/ShanghaiA_train.npy'

    with open(train_file, 'rb') as outfile:
        train_list = np.load(outfile).tolist()

    print(f"Training images: {len(train_list)}")

    print("Building model...")
    model = get_seg_model(train=True)
    model = nn.DataParallel(model, device_ids=[0])
    model = model.cuda()

    # Load checkpoint
    if args['pre'] and os.path.isfile(args['pre']):
        print(f"Loading checkpoint from {args['pre']}...")
        checkpoint = torch.load(args['pre'])
        model.load_state_dict(checkpoint['state_dict'])
        print("Checkpoint loaded!")

    optimizer = torch.optim.Adam(
        [{'params': model.parameters(), 'lr': args['lr']}],
        lr=args['lr'],
        weight_decay=args['weight_decay']
    )

    criterion = nn.MSELoss(size_average=False).cuda()

    print(f"\nStarting training from epoch {args['start_epoch']}")
    print(f"Learning rate: {args['lr']}")
    print(f"No validation - just training\n")

    for epoch in range(args['start_epoch'], args['epochs']):
        start = time.time()

        # Train
        model.train()
        losses = AverageMeter()

        train_loader = torch.utils.data.DataLoader(
            dataset.listDataset(train_list, args['save_path'],
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

        for i, (fname, img, fidt_map, kpoint) in enumerate(train_loader):
            img = img.cuda()
            fidt_map = fidt_map.type(torch.FloatTensor).unsqueeze(1).cuda()

            d6 = model(img)

            if d6.shape != fidt_map.shape:
                continue

            loss = criterion(d6, fidt_map)
            losses.update(loss.item(), img.size(0))

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            if i % args['print_freq'] == 0:
                print(f'Epoch {epoch}[{i}/{len(train_loader)}] Loss: {losses.avg:.4f}')

        end = time.time()
        print(f'* Epoch {epoch} - Loss: {losses.avg:.4f} - Time: {end - start:.1f}s')

        # Save checkpoint every 10 epochs
        if epoch % 10 == 0:
            save_checkpoint({
                'epoch': epoch + 1,
                'state_dict': model.state_dict(),
                'best_prec1': args['best_pred'],
            }, args['save_path'])
            print(f'  -> Checkpoint saved at epoch {epoch}')

        # Reduce LR every 50 epochs
        if epoch % 50 == 0 and epoch > args['start_epoch']:
            for param_group in optimizer.param_groups:
                param_group['lr'] = param_group['lr'] * 0.5
            print(f'  -> LR reduced to {optimizer.param_groups[0]["lr"]:.6f}')

    print(f"\nTraining complete!")
    save_checkpoint({
        'epoch': args['epochs'],
        'state_dict': model.state_dict(),
        'best_prec1': args['best_pred'],
    }, args['save_path'])


def save_checkpoint(state, save_path):
    filepath = os.path.join(save_path, 'latest_model.pth')
    torch.save(state, filepath)


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
        self.sum = val * n
        self.count += n
        self.avg = self.sum / self.count


if __name__ == '__main__':
    main()