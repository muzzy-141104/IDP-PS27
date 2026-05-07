"""
Generate proper Gaussian density maps from kpoint annotations.
This is the standard approach used in CSRNet and other density-based methods.
"""
import os
import numpy as np
from scipy.ndimage import gaussian_filter
import h5py
from PIL import Image


def generate_density_map(kpoint, sigma=4):
    """
    Generate Gaussian density map from kpoint annotations.

    Args:
        kpoint: 2D array with 1s at person locations, 0s elsewhere
        sigma: Gaussian kernel sigma (controls blob size)

    Returns:
        density_map: 2D array where sum equals the count
    """
    # Create density map by applying Gaussian filter to point annotations
    density_map = gaussian_filter(kpoint.astype(np.float32), sigma=sigma)

    # Ensure the sum equals the count (preserving ground truth count)
    count = np.sum(kpoint)
    if count > 0:
        density_map = density_map * (count / np.sum(density_map))

    return density_map


def create_density_maps_from_h5(img_path, gt_path, output_path, sigma=4):
    """
    Read kpoint from existing h5 file and create proper density map.

    Args:
        img_path: Path to image file
        gt_path: Path to existing h5 file with kpoint
        output_path: Path to save new density map h5
        sigma: Gaussian kernel sigma
    """
    # Read image dimensions
    img = Image.open(img_path)
    img_h, img_w = np.array(img).shape[:2]

    # Read kpoint from existing h5
    with h5py.File(gt_path, 'r') as f:
        kpoint = np.asarray(f['kpoint'], dtype=np.float32)

    # Resize kpoint if needed
    if kpoint.shape != (img_h, img_w):
        kpoint_pil = Image.fromarray(kpoint.astype(np.uint8))
        kpoint_pil = kpoint_pil.resize((img_w, img_h), Image.NEAREST)
        kpoint = np.array(kpoint_pil).astype(np.float32)

    # Generate density map
    density_map = generate_density_map(kpoint, sigma=sigma)

    # Save to h5
    with h5py.File(output_path, 'w') as f:
        f.create_dataset('density_map', data=density_map)
        f.create_dataset('kpoint', data=kpoint)
        f.create_dataset('count', data=np.sum(kpoint))

    return np.sum(kpoint), np.sum(density_map)


def main():
    """Generate density maps for ShanghaiTech dataset"""
    base_path = 'd:/Crowd-Counting-Platform/ShanghaiTech'

    # Process train and test sets
    splits = [
        ('part_A/train_data', 'train'),
        ('part_A/test_data', 'test'),
        ('part_B/train_data', 'train'),
        ('part_B/test_data', 'test'),
    ]

    sigma = 8  # Typical sigma for crowd counting

    for split_path, split_name in splits:
        img_dir = os.path.join(base_path, split_path, 'images')
        output_dir = os.path.join(base_path, split_path, 'gt_density_map')

        os.makedirs(output_dir, exist_ok=True)

        if not os.path.exists(img_dir):
            print(f"Skipping {img_dir} - not found")
            continue

        img_files = [f for f in os.listdir(img_dir) if f.endswith('.jpg')]
        print(f"\nProcessing {split_name} ({len(img_files)} images)...")

        for i, img_file in enumerate(img_files):
            img_path = os.path.join(img_dir, img_file)
            h5_name = img_file.replace('.jpg', '.h5')

            # Original GT path (may not exist for all files)
            orig_gt_path = os.path.join(base_path, split_path, 'gt_fidt_map', h5_name)
            if not os.path.exists(orig_gt_path):
                # Try alternative location
                orig_gt_path = img_path.replace('.jpg', '.h5').replace('images', 'gt_fidt_map')

            output_path = os.path.join(output_dir, h5_name)

            try:
                if os.path.exists(orig_gt_path):
                    # Create density map from existing kpoint
                    gt_count, dm_sum = create_density_maps_from_h5(
                        img_path, orig_gt_path, output_path, sigma=sigma
                    )
                else:
                    print(f"\n  Warning: GT not found for {img_file}")
                    continue

                if (i + 1) % 100 == 0:
                    print(f"  Processed {i+1}/{len(img_files)}")

            except Exception as e:
                print(f"\n  Error on {img_file}: {str(e)[:50]}")

    print("\nDone!")


if __name__ == '__main__':
    main()