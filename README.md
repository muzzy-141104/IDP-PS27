# Crowd-Counting-Platform

A state-of-the-art platform that implements 4 powerful crowd counting algorithms (YOLO-CROWD, FIDTM, P2PNet, and CSRNet). This platform allows users to predict the number of people in images and videos with high accuracy.

## 🚀 Key Features
- **4 Advanced Algorithms**:
  - **YOLO-CROWD**: Fast and accurate object detection-based counting (Supports bounding boxes).
  - **CSRNet**: High-quality density map estimation for dense crowds.
  - **FIDTM**: Focal Inverse Distance Transform Map for robust localization.
  - **P2PNet**: Purely point-based framework for crowd counting and localization.
- **Web Interface**: Easy-to-use Flask-based web interface.
- **Support for Images & Videos**: Upload `.jpg`, `.jpeg`, `.png`, and `.mp4` files.
- **Real-time Processing**: Optimized for performance on modern hardware.

## 📸 Screenshots

### Home Page
![crowdcounting-website](https://github.com/zaki1003/Crowd-Counting-Platform/assets/65148928/f3f1211a-18c5-4481-9601-bfe0aadadb2d)

### Prediction with YOLO-CROWD
![YOLO-Result](https://github.com/zaki1003/Crowd-Counting-Platform/assets/65148928/b9bbb1b1-2ddd-4ab1-9b0e-0583c2e4e4b0)

---

## 🛠️ Getting Started

### 1. Clone the Repository
This project uses **Git LFS** (Large File Storage) to manage model weights. Make sure you have Git LFS installed before cloning.

```bash
# Install Git LFS
git lfs install

# Clone the repo
git clone https://github.com/muzzy-141104/IDP-PS27.git
cd IDP-PS27
```

### 2. Install Requirements
```bash
pip install -r requirements.txt
```

### 3. Models
The core models are included in the repository via Git LFS:
- `yolo-crowd.pt` (YOLO Weights)
- `modelCRNet.pt` (CSRNet Weights)
- `yolo-crowd.engine` (TensorRT optimized YOLO)

**Note:** For FIDTM and P2PNet, manual download might be required if the LFS quota is exceeded:
- [FIDTM Weights](https://drive.google.com/file/d/1drjYZW7hp6bQI39u7ffPYwt4Kno9cLu8/view?usp=sharing)
- [P2PNet Weights](https://drive.google.com/file/d/1-189sscpNZBFaSHOz7dnEgAaFeUALiow/view?usp=sharing)

### 4. Run the Application
```bash
python app.py
```
Open your browser and navigate to `http://localhost:8080`.

---

## 📖 How to Use

1. **Upload**: Select an image or video file using the "Import Image or Video" button.
2. **Method**: Choose your preferred counting method from the dropdown (e.g., **YOLO-CROWD** for detection or **CSRNet** for density).
3. **Count**: Click the "Count" button to process the file.
4. **Results**:
   - For **YOLO-CROWD**, you will see the image with bounding boxes around detected people and the final count.
   - For **Density models** (CSRNet, FIDTM), you will see a colorized density map indicating crowd concentration.

---

## ⚖️ License
This project is licensed under the MIT License.
