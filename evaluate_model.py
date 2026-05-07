"""
Evaluate FIDTM model - minimal memory version
"""
import os
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from sklearn.metrics import mean_absolute_error, mean_squared_error
from PIL import Image
import h5py
from Networks.HR_Net.seg_hrnet import get_seg_model

os.environ['CUDA_VISIBLE_DEVICES'] = '0'

def load_model(checkpoint_path):
    model = get_seg_model(train=False)
    model = nn.DataParallel(model, device_ids=[0])
    model = model.cuda()
    checkpoint = torch.load(checkpoint_path, weights_only=False)
    model.load_state_dict(checkpoint['state_dict'])
    model.eval()
    return model

def LMDS_counting(input):
    input_max = torch.max(input).item()
    keep = nn.functional.max_pool2d(input, (3, 3), stride=1, padding=1)
    keep = (keep == input).float()
    input = keep * input
    input[input < 100.0 / 255.0 * input_max] = 0
    input[input > 0] = 1
    if input_max < 0.1:
        input = input * 0
    return int(torch.sum(input).item())

def main():
    test_file = './npydata/ShanghaiA_test.npy'
    with open(test_file, 'rb') as outfile:
        test_list = np.load(outfile).tolist()

    print(f"Test images: {len(test_list)}")

    model_path = 'save_file/my_fidtm/model_best_nwpu.pth'
    print(f"Loading model from {model_path}...")
    model = load_model(model_path)

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    ground_truth_counts = []
    predicted_counts = []

    print("Evaluating...")
    for i, img_path in enumerate(test_list):
        try:
            # Load image
            img = Image.open(img_path).convert('RGB')
            img_tensor = transform(img).unsqueeze(0).cuda()

            # Load ground truth
            gt_path = img_path.replace('.jpg', '.h5').replace('images', 'gt_fidt_map')
            with h5py.File(gt_path, 'r') as gt_file:
                kpoint = np.asarray(gt_file['kpoint'], dtype=np.float32)
                gt_count = int(np.sum(kpoint))

            # Predict
            with torch.no_grad():
                d6 = model(img_tensor)
                pred_count = LMDS_counting(d6)

            ground_truth_counts.append(gt_count)
            predicted_counts.append(pred_count)

            if (i + 1) % 30 == 0:
                print(f"  [{i+1}/{len(test_list)}] GT: {gt_count:.0f}, Pred: {pred_count:.0f}")

            # Clear memory
            del img_tensor, d6
            torch.cuda.empty_cache()

        except Exception as e:
            print(f"  Error on image {i}: {str(e)[:60]}")
            continue

    y_true = np.array(ground_truth_counts)
    y_pred = np.array(predicted_counts)
    errors = y_pred - y_true

    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)

    # Save results
    os.makedirs('evaluation_results', exist_ok=True)

    with open('evaluation_results/metrics.txt', 'w') as f:
        f.write("="*50 + "\n")
        f.write("FIDTM MODEL EVALUATION RESULTS\n")
        f.write("="*50 + "\n\n")
        f.write(f"MAE (Mean Absolute Error): {mae:.2f}\n")
        f.write(f"RMSE (Root Mean Squared Error): {rmse:.2f}\n")
        f.write(f"Mean Error: {np.mean(errors):.2f}\n")
        f.write(f"Std Error: {np.std(errors):.2f}\n\n")
        f.write(f"Ground Truth - Min: {y_true.min():.0f}, Max: {y_true.max():.0f}, Mean: {y_true.mean():.1f}\n")
        f.write(f"Predicted - Min: {y_pred.min():.0f}, Max: {y_pred.max():.0f}, Mean: {y_pred.mean():.1f}\n\n")
        f.write(f"Total Test Images: {len(y_true)}\n\n")
        f.write("Sample Predictions:\n")
        f.write("-"*30 + "\n")
        for j in range(min(20, len(y_true))):
            f.write(f"GT: {y_true[j]:5.0f}  Pred: {y_pred[j]:5.0f}  Error: {errors[j]:+7.0f}\n")
        f.write("="*50 + "\n")

    print("\n" + "="*50)
    print("EVALUATION RESULTS")
    print("="*50)
    print(f"MAE:  {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"Mean Error: {np.mean(errors):.2f}")
    print(f"Std Error: {np.std(errors):.2f}")
    print(f"Test Images: {len(y_true)}")
    print("="*50)
    print("\nResults saved to evaluation_results/metrics.txt")

if __name__ == '__main__':
    main()