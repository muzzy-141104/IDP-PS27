"""
Evaluate CSRNet model on ShanghaiTech Part A test set
Generates accuracy charts and metrics
"""
import os
import sys
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image
import scipy.io as sio
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pythonModel import CSRNet

os.environ['CUDA_VISIBLE_DEVICES'] = '0'


def main():
    # Paths
    test_img_dir = './shanghaitech_h5_empty/ShanghaiTech/part_A/test_data/images'
    test_gt_dir = './shanghaitech_h5_empty/ShanghaiTech/part_A/test_data/ground-truth'
    model_path = './modelCRNet.pt'
    output_dir = './evaluation_results'
    os.makedirs(output_dir, exist_ok=True)

    # Load model
    print("Loading CSRNet model...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = CSRNet()
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    print(f"Model loaded on {device}")

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # Get all test images
    img_files = sorted([f for f in os.listdir(test_img_dir) if f.endswith('.jpg')])
    print(f"Test images: {len(img_files)}")

    ground_truth_counts = []
    predicted_counts = []
    filenames = []

    print("\nEvaluating...")
    for i, img_file in enumerate(img_files):
        try:
            # Load image
            img_path = os.path.join(test_img_dir, img_file)
            img = Image.open(img_path).convert('RGB')
            img_tensor = transform(img).unsqueeze(0).to(device)

            # Load ground truth (.mat file with point annotations)
            gt_name = 'GT_' + img_file.replace('.jpg', '.mat')
            gt_path = os.path.join(test_gt_dir, gt_name)
            mat = sio.loadmat(gt_path)
            # Ground truth count = number of annotated points
            gt_count = mat['image_info'][0][0][0][0][1][0][0]

            # Predict
            with torch.no_grad():
                output = model(img_tensor)
                pred_count = output.detach().cpu().sum().item()

            ground_truth_counts.append(float(gt_count))
            predicted_counts.append(float(pred_count))
            filenames.append(img_file)

            if (i + 1) % 20 == 0:
                print(f"  [{i+1}/{len(img_files)}] {img_file} - GT: {gt_count}, Pred: {pred_count:.1f}")

            # Free memory
            del img_tensor, output
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        except Exception as e:
            print(f"  Error on {img_file}: {str(e)[:80]}")
            continue

    # Calculate metrics
    y_true = np.array(ground_truth_counts)
    y_pred = np.array(predicted_counts)
    errors = y_pred - y_true

    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)

    # ========== Save Metrics ==========
    with open(os.path.join(output_dir, 'csrnet_metrics.txt'), 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("CSRNet MODEL EVALUATION RESULTS\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Model: CSRNet (VGG16 backbone + Dilated Convolutions)\n")
        f.write(f"Dataset: ShanghaiTech Part A (Test Set)\n")
        f.write(f"Weights: modelCRNet.pt\n\n")
        f.write(f"MAE (Mean Absolute Error): {mae:.2f}\n")
        f.write(f"RMSE (Root Mean Squared Error): {rmse:.2f}\n")
        f.write(f"Mean Error: {np.mean(errors):.2f}\n")
        f.write(f"Std Error: {np.std(errors):.2f}\n\n")
        f.write(f"Ground Truth - Min: {y_true.min():.0f}, Max: {y_true.max():.0f}, Mean: {y_true.mean():.1f}\n")
        f.write(f"Predicted    - Min: {y_pred.min():.0f}, Max: {y_pred.max():.0f}, Mean: {y_pred.mean():.1f}\n\n")
        f.write(f"Total Test Images: {len(y_true)}\n\n")
        f.write("Sample Predictions (first 20):\n")
        f.write("-" * 50 + "\n")
        for j in range(min(20, len(y_true))):
            f.write(f"GT: {y_true[j]:5.0f}  Pred: {y_pred[j]:6.0f}  Error: {errors[j]:+7.0f}\n")
        f.write("=" * 60 + "\n")

    # ========== Generate Charts ==========
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('CSRNet Model Evaluation - ShanghaiTech Part A', fontsize=16, fontweight='bold')

    # 1. Scatter plot: GT vs Predicted
    ax1 = axes[0, 0]
    ax1.scatter(y_true, y_pred, alpha=0.5, s=25, c='steelblue', edgecolors='navy', linewidths=0.5)
    max_val = max(y_true.max(), y_pred.max()) * 1.1
    ax1.plot([0, max_val], [0, max_val], 'r--', linewidth=2, label='Perfect prediction')
    ax1.set_xlabel('Ground Truth Count', fontsize=12)
    ax1.set_ylabel('Predicted Count', fontsize=12)
    ax1.set_title(f'Ground Truth vs Predicted (MAE: {mae:.2f})', fontsize=13)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, max_val)
    ax1.set_ylim(0, max_val)

    # 2. Error distribution histogram
    ax2 = axes[0, 1]
    ax2.hist(errors, bins=40, edgecolor='black', alpha=0.7, color='coral')
    ax2.axvline(x=0, color='r', linestyle='--', linewidth=2, label='Zero error')
    ax2.axvline(x=np.mean(errors), color='green', linestyle='--', linewidth=2, label=f'Mean: {np.mean(errors):.1f}')
    ax2.set_xlabel('Prediction Error (Pred - GT)', fontsize=12)
    ax2.set_ylabel('Frequency', fontsize=12)
    ax2.set_title('Error Distribution', fontsize=13)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)

    # 3. Bar chart: Sample predictions
    ax3 = axes[1, 0]
    n_samples = min(30, len(y_true))
    x = np.arange(n_samples)
    width = 0.35
    ax3.bar(x - width / 2, y_true[:n_samples], width, label='Ground Truth', alpha=0.8, color='steelblue')
    ax3.bar(x + width / 2, y_pred[:n_samples], width, label='Predicted', alpha=0.8, color='coral')
    ax3.set_xlabel('Sample Index', fontsize=12)
    ax3.set_ylabel('Count', fontsize=12)
    ax3.set_title('Sample Predictions (First 30)', fontsize=13)
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)

    # 4. MAE by crowd density range
    ax4 = axes[1, 1]
    bins = [0, 100, 200, 400, 600, 800, 1200, 2500]
    bin_labels = ['0-100', '100-200', '200-400', '400-600', '600-800', '800-1.2k', '1.2k+']
    bin_indices = np.digitize(y_true, bins)
    bin_mae = []
    bin_counts = []
    for bi in range(1, len(bins)):
        mask = bin_indices == bi
        if mask.sum() > 0:
            bin_mae.append(np.mean(np.abs(errors[mask])))
            bin_counts.append(mask.sum())
        else:
            bin_mae.append(0)
            bin_counts.append(0)

    bars = ax4.bar(bin_labels, bin_mae, color='steelblue', edgecolor='black')
    # Add count labels on bars
    for bar, count in zip(bars, bin_counts):
        ax4.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                 f'n={count}', ha='center', va='bottom', fontsize=8)
    ax4.set_xlabel('Ground Truth Count Range', fontsize=12)
    ax4.set_ylabel('Mean Absolute Error', fontsize=12)
    ax4.set_title('MAE by Crowd Density Range', fontsize=13)
    ax4.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    chart_path = os.path.join(output_dir, 'csrnet_evaluation.png')
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.close()

    # Print results
    print("\n" + "=" * 60)
    print("CSRNet EVALUATION RESULTS")
    print("=" * 60)
    print(f"MAE:  {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"Mean Error: {np.mean(errors):.2f}")
    print(f"Std Error:  {np.std(errors):.2f}")
    print(f"Test Images: {len(y_true)}")
    print("=" * 60)
    print(f"\nCharts saved to: {chart_path}")
    print(f"Metrics saved to: {os.path.join(output_dir, 'csrnet_metrics.txt')}")


if __name__ == '__main__':
    main()
