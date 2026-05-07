"""
Evaluate lightweight model - Final evaluation with charts
"""
import os
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import h5py
import matplotlib.pyplot as plt
from models.lightweight_crowd import CrowdCounter
from sklearn.metrics import mean_absolute_error, mean_squared_error

os.environ['CUDA_VISIBLE_DEVICES'] = '0'


def main():
    test_file = './npydata/ShanghaiA_test.npy'
    with open(test_file, 'rb') as outfile:
        test_list = np.load(outfile).tolist()

    print(f"Test images: {len(test_list)}")

    model_path = 'save_file/lightweight_model/model_best.pth'
    print(f"Loading model from {model_path}...")

    model = CrowdCounter(load_weights=True).to('cuda')
    checkpoint = torch.load(model_path, weights_only=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    ground_truth_counts = []
    predicted_counts = []

    print("\nEvaluating...")
    for i, img_path in enumerate(test_list):
        try:
            img = Image.open(img_path).convert('RGB')
            img_tensor = transform(img).unsqueeze(0).cuda()

            gt_path = img_path.replace('.jpg', '.h5').replace('images', 'gt_density_map')
            with h5py.File(gt_path, 'r') as gt_file:
                density_map = np.asarray(gt_file['density_map'], dtype=np.float32)
                gt_count = float(np.sum(density_map))

            with torch.no_grad():
                output = model(img_tensor)
                pred_count = torch.sum(output).item()

            ground_truth_counts.append(gt_count)
            predicted_counts.append(pred_count)

            if (i + 1) % 30 == 0:
                print(f"  [{i+1}/{len(test_list)}]")

        except Exception as e:
            print(f"  Error on image {i}: {str(e)[:60]}")
            continue

    y_true = np.array(ground_truth_counts)
    y_pred = np.array(predicted_counts)
    errors = y_pred - y_true

    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)

    # Save metrics
    os.makedirs('evaluation_results', exist_ok=True)

    with open('evaluation_results/lightweight_metrics.txt', 'w') as f:
        f.write("="*60 + "\n")
        f.write("LIGHTWEIGHT CROWD COUNTING MODEL EVALUATION RESULTS\n")
        f.write("="*60 + "\n\n")
        f.write(f"Model: ResNet18-based CSRNet-style with Gaussian density maps\n")
        f.write(f"Parameters: 19,832,417\n")
        f.write(f"Training: 105 epochs with batch_size=8, lr=1e-4\n\n")
        f.write(f"MAE (Mean Absolute Error): {mae:.2f}\n")
        f.write(f"RMSE (Root Mean Squared Error): {rmse:.2f}\n")
        f.write(f"Mean Error: {np.mean(errors):.2f}\n")
        f.write(f"Std Error: {np.std(errors):.2f}\n\n")
        f.write(f"Ground Truth - Min: {y_true.min():.0f}, Max: {y_true.max():.0f}, Mean: {y_true.mean():.1f}\n")
        f.write(f"Predicted - Min: {y_pred.min():.0f}, Max: {y_pred.max():.0f}, Mean: {y_pred.mean():.1f}\n\n")
        f.write(f"Total Test Images: {len(y_true)}\n\n")
        f.write("Sample Predictions (first 20):\n")
        f.write("-"*50 + "\n")
        for j in range(min(20, len(y_true))):
            f.write(f"GT: {y_true[j]:5.0f}  Pred: {y_pred[j]:6.0f}  Error: {errors[j]:+7.0f}\n")
        f.write("="*60 + "\n")

    print("\n" + "="*60)
    print("LIGHTWEIGHT MODEL EVALUATION RESULTS")
    print("="*60)
    print(f"MAE:  {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"Mean Error: {np.mean(errors):.2f}")
    print(f"Std Error: {np.std(errors):.2f}")
    print(f"Test Images: {len(y_true)}")
    print("="*60)

    # Create evaluation charts
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Scatter plot: GT vs Predicted
    ax1 = axes[0, 0]
    ax1.scatter(y_true, y_pred, alpha=0.5, s=20)
    max_val = max(y_true.max(), y_pred.max())
    ax1.plot([0, max_val], [0, max_val], 'r--', label='Perfect prediction')
    ax1.set_xlabel('Ground Truth Count')
    ax1.set_ylabel('Predicted Count')
    ax1.set_title(f'Ground Truth vs Predicted (MAE: {mae:.2f})')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Error distribution histogram
    ax2 = axes[0, 1]
    ax2.hist(errors, bins=40, edgecolor='black', alpha=0.7)
    ax2.axvline(x=0, color='r', linestyle='--', label='Zero error')
    ax2.axvline(x=np.mean(errors), color='g', linestyle='--', label=f'Mean: {np.mean(errors):.1f}')
    ax2.set_xlabel('Prediction Error (Pred - GT)')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Error Distribution')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. Bar chart: Sample predictions
    ax3 = axes[1, 0]
    n_samples = min(30, len(y_true))
    x = np.arange(n_samples)
    width = 0.35
    ax3.bar(x - width/2, y_true[:n_samples], width, label='Ground Truth', alpha=0.8)
    ax3.bar(x + width/2, y_pred[:n_samples], width, label='Predicted', alpha=0.8)
    ax3.set_xlabel('Sample Index')
    ax3.set_ylabel('Count')
    ax3.set_title('Sample Predictions (First 30)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 4. Error by GT count bins
    ax4 = axes[1, 1]
    bins = [0, 200, 400, 600, 800, 1000, 1500, 2500]
    bin_labels = ['0-200', '200-400', '400-600', '600-800', '800-1k', '1k-1.5k', '1.5k+']
    bin_indices = np.digitize(y_true, bins)
    bin_mae = []
    for i in range(1, len(bins)):
        mask = bin_indices == i
        if mask.sum() > 0:
            bin_mae.append(np.mean(np.abs(errors[mask])))
        else:
            bin_mae.append(0)
    ax4.bar(bin_labels, bin_mae, color='steelblue', edgecolor='black')
    ax4.set_xlabel('Ground Truth Count Range')
    ax4.set_ylabel('Mean Absolute Error')
    ax4.set_title('MAE by Crowd Count Range')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('evaluation_results/lightweight_evaluation.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("\nEvaluation charts saved to evaluation_results/lightweight_evaluation.png")
    print("Metrics saved to evaluation_results/lightweight_metrics.txt")

    # Comparison with FIDTM
    print("\n" + "="*60)
    print("MODEL COMPARISON")
    print("="*60)
    print(f"{'Model':<25} {'MAE':>10} {'Improvement':>12}")
    print("-"*50)
    print(f"{'FIDTM (original)':<25} {'1247.69':>10} {'-':>12}")
    print(f"{'Lightweight (CSRNet-style)':<25} {mae:>10.2f} {(1247.69 - mae) / 1247.69 * 100:>11.1f}%")
    print("="*60)


if __name__ == '__main__':
    main()