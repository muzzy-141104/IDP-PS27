import glob
import math
import os
import torch
import cv2
import h5py
import numpy as np
import scipy.io as io
import scipy.spatial
from scipy.ndimage.filters import gaussian_filter

# Fixed paths for your data structure
root = 'd:/Crowd-Counting-Platform/ShanghaiTech/'

part_A_train = os.path.join(root, 'part_A/train_data', 'images')
part_A_test = os.path.join(root, 'part_A/test_data', 'images')
part_B_train = os.path.join(root, 'part_B/train_data', 'images')
part_B_test = os.path.join(root, 'part_B/test_data', 'images')

path_sets = [part_A_train, part_A_test]

# Create output directories
for path in path_sets:
    gt_fidt_dir = path.replace('images', 'gt_fidt_map')
    gt_show_dir = path.replace('images', 'gt_show')
    if not os.path.exists(gt_fidt_dir):
        os.makedirs(gt_fidt_dir)
    if not os.path.exists(gt_show_dir):
        os.makedirs(gt_show_dir)

img_paths = []
for path in path_sets:
    for img_path in glob.glob(os.path.join(path, '*.jpg')):
        img_paths.append(img_path)

img_paths.sort()


def fidt_generate1(im_data, gt_data, lamda):
    size = im_data.shape
    new_im_data = cv2.resize(im_data, (lamda * size[1], lamda * size[0]), 0)

    new_size = new_im_data.shape
    d_map = (np.zeros([new_size[0], new_size[1]]) + 255).astype(np.uint8)
    gt = lamda * gt_data

    for o in range(0, len(gt)):
        x = np.max([1, math.floor(gt[o][1])])
        y = np.max([1, math.floor(gt[o][0])])
        if x >= new_size[0] or y >= new_size[1]:
            continue
        d_map[x][y] = d_map[x][y] - 255

    distance_map = cv2.distanceTransform(d_map, cv2.DIST_L2, 0)
    distance_map = torch.from_numpy(distance_map)
    distance_map = 1 / (1 + torch.pow(distance_map, 0.02 * distance_map + 0.75))
    distance_map = distance_map.numpy()
    distance_map[distance_map < 1e-2] = 0

    return distance_map


for img_path in img_paths:
    print(f"Processing: {img_path}")

    # Load image
    Img_data = cv2.imread(img_path)

    # Load ground truth from .mat file
    # Your structure: ground-truth/GT_IMG_1.mat
    mat_path = img_path.replace('images', 'ground-truth').replace('IMG_', 'GT_IMG_').replace('.jpg', '.mat')
    print(f"  Loading mat: {mat_path}")

    mat = io.loadmat(mat_path)
    Gt_data = mat["image_info"][0][0][0][0][0]

    # Generate FIDT map
    fidt_map1 = fidt_generate1(Img_data, Gt_data, 1)

    # Generate kpoint (binary point map)
    kpoint = np.zeros((Img_data.shape[0], Img_data.shape[1]))
    for i in range(0, len(Gt_data)):
        if int(Gt_data[i][1]) < Img_data.shape[0] and int(Gt_data[i][0]) < Img_data.shape[1]:
            kpoint[int(Gt_data[i][1]), int(Gt_data[i][0])] = 1

    # Save FIDT map and kpoint as h5 file
    h5_path = img_path.replace('.jpg', '.h5').replace('images', 'gt_fidt_map')
    with h5py.File(h5_path, 'w') as hf:
        hf['fidt_map'] = fidt_map1
        hf['kpoint'] = kpoint
    print(f"  Saved: {h5_path}")

    # For visualization
    fidt_vis = fidt_map1 / np.max(fidt_map1) * 255
    fidt_vis = fidt_vis.astype(np.uint8)
    fidt_vis = cv2.applyColorMap(fidt_vis, 2)

    vis_path = img_path.replace('images', 'gt_show').replace('.jpg', '.jpg')
    cv2.imwrite(vis_path, fidt_vis)

    print(f"  Count: {len(Gt_data)} people")

print(f"\nDone! Generated {len(img_paths)} FIDT maps.")