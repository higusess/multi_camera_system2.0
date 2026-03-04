# 手眼标定程序 (Eye-in-Hand)

## 概述

这是一个基于 OpenCV 的手眼标定程序，用于计算相机（安装在机械臂末端）相对于机械臂末端的变换矩阵。

### 场景描述

- **Eye-in-Hand**: 相机安装在机械臂末端
- 棋盘格固定在桌面上（目标坐标系）
- 通过移动机械臂，从不同角度观察棋盘格
- 计算相机到机械臂末端的变换矩阵 (cam2gripper)

## 文件结构

```
D:/Multi_Camera_System/
├── camera_handler.py           # 相机处理模块（线程安全）
├── chessboard_detector.py      # 棋盘格检测模块 + 倾斜检测
├── hand_eye_calibrator.py      # 手眼标定核心模块
├── ui_overlay.py               # UI显示模块 + 水平仪显示
├── hand_eye_calibration.py     # 主程序（含倾斜检测）
├── parallel_monitor.py          # 平行桌面实时监控程序
├── camera_calibration_helper.py # 相机内参标定辅助程序
├── config.py                   # 配置文件
├── HAND_EYE_README.md          # 本文档
├── PARALLEL_MONITOR_README.md   # 平行监控程序说明
└── requirements.txt            # 依赖包
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用步骤

### 第一步：标定相机内参（可选但推荐）

如果还没有标定相机内参，先运行相机内参标定程序：

```bash
python camera_calibration_helper.py
```

标定完成后，相机参数会保存到 `camera_calibration_results/camera_params.py`

### 第二步：设置相机参数

有两种方式设置相机参数：

#### 方式1：运行时设置
启动程序后按 `P` 键，手动输入相机参数

#### 方式2：代码中设置
修改 `hand_eye_calibration.py` 中的 `set_camera_params` 调用：

```python
camera_matrix = np.array([
    [1000, 0, 640],
    [0, 1000, 360],
    [0, 0, 1]
], dtype=np.float32)

dist_coeffs = np.array([k1, k2, p1, p2, k3], dtype=np.float32).reshape(5, 1)

app.set_camera_params(camera_matrix, dist_coeffs)
```

### 第三步：运行手眼标定程序

```bash
python hand_eye_calibration.py
```

## 程序操作

| 按键 | 功能 |
|------|------|
| `SPACE` | 添加标定样本（输入机械臂位姿） |
| `C` | 执行手眼标定计算 |
| `S` | 保存当前 target2cam 矩阵 |
| `T` | 打印当前倾斜角度（控制台） |
| `R` | 清除所有标定数据 |
| `P` | 设置相机参数 |
| `H` | 显示帮助 |
| `Q` / `ESC` | 退出程序 |

## 标定流程

1. 启动程序，相机画面出现
2. 调整机械臂到第一个位置
3. 确保画面中能清晰看到棋盘格
4. 按 `SPACE` 键，输入当前机械臂末端位姿 (x, y, z, rx, ry, rz)
5. 移动机械臂到第二个位置，重复步骤3-4
6. 至少收集3组数据（推荐10-15组）
7. 按 `C` 键执行标定计算
8. 标定结果自动保存到 `calibration_results/` 目录

## 输入机械臂位姿

当按 `SPACE` 键添加样本时，需要输入机械臂末端相对于基座的位姿：

```
单位:
- x, y, z: 毫米 (mm)
- rx, ry, rz: 度 (degree)

示例:
x: 100.0
y: 200.0
z: 300.0
rx: 0.0
ry: 0.0
rz: 0.0
```

## 标定结果

标定完成后，结果保存在两个文件中：

1. `hand_eye_calibration_YYYYMMDD_HHMMSS.pkl` - Python pickle 格式
2. `hand_eye_calibration_YYYYMMDD_HHMMSS.txt` - 可读文本格式

文本格式包含：
- R_cam2gripper: 相机到机械臂末端的旋转矩阵
- t_cam2gripper: 相机到机械臂末端的平移向量 (mm)
- 欧拉角表示 (度)

## 画面显示

程序在画面上实时显示：

- **左上角**：状态信息和样本数量
- **左下角**：相机倾斜状态指示器（绿色=平行，红色=倾斜）
  - X轴倾斜角度 (绕X轴)
  - Y轴倾斜角度 (绕Y轴)
  - 总倾斜角度
  - 需要调整的角度（如果倾斜）
- **右上角**：Target to Cam 角度 (Rx, Ry, Rz)
- **右下角**：水平仪（气泡显示倾斜方向）
- 棋盘格角点标记
- 3D坐标轴（X:红色, Y:绿色, Z:蓝色）
- 底部：标定进度条

## 倾斜检测说明

程序实时检测相机与桌面的夹角：

- **X轴倾斜 (Rx)**：相机绕其X轴的旋转角度
  - 正值：相机前端向下
  - 负值：相机前端向上
- **Y轴倾斜 (Ry)**：相机绕其Y轴的旋转角度
  - 正值：相机向右倾斜
  - 负值：相机向左倾斜
- **总倾斜角度**：相机Z轴与桌面法向量的夹角
  - 0° = 完全平行
  - < 2° = 视为平行（绿色显示）
  - > 2° = 需要调整（红色显示）

### 使用倾斜检测

1. 标定完成后，观察画面左下角的倾斜指示器
2. 如果显示红色，说明相机不平行桌面
3. 按 `T` 键在控制台查看详细倾斜信息
4. 根据提示调整机械臂姿态
5. 直到指示器变为绿色（平行状态）

## 集成到多线程系统

### 模块化设计

各模块功能独立，方便集成：

#### CameraHandler
```python
from camera_handler import CameraHandler

camera = CameraHandler(camera_id=0)
camera.open()
frame = camera.read_frame()
camera.close()
```

#### ChessboardDetector
```python
from chessboard_detector import ChessboardDetector

detector = ChessboardDetector(pattern_size=(9, 9), square_size=18.0)
display_frame, corners, detected = detector.detect(frame)

if detected:
    success, rvec, tvec = detector.solve_pnp(corners, camera_matrix, dist_coeffs)
```

#### HandEyeCalibrator
```python
from hand_eye_calibrator import HandEyeCalibrator

calibrator = HandEyeCalibrator(camera_matrix, dist_coeffs)
calibrator.add_data(gripper_pose, (rvec, tvec))
R, t = calibrator.calibrate()
calibrator.save_results()
```

### 多线程集成示例

```python
import threading
from camera_handler import CameraHandler
from chessboard_detector import ChessboardDetector
from hand_eye_calibrator import HandEyeCalibrator

class CalibrationThread(threading.Thread):
    def __init__(self, camera_id):
        super().__init__()
        self.camera = CameraHandler(camera_id)
        self.detector = ChessboardDetector()
        self.calibrator = HandEyeCalibrator()
        self.running = False

    def run(self):
        self.camera.open()
        self.running = True

        while self.running:
            frame = self.camera.read_frame()
            if frame is not None:
                display_frame, corners, detected = self.detector.detect(frame)
                # 处理...

        self.camera.close()

    def stop(self):
        self.running = False
```

## 配置参数

编辑 `config.py` 文件修改默认配置：

```python
CHESSBOARD_CONFIG = {
    'pattern_size': (9, 9),    # 内角点数量
    'square_size': 18.0,        # 格子大小 (mm)
}

CAMERA_CONFIG = {
    'camera_id': 0,
    'width': 1280,
    'height': 720,
    # ... 相机参数
}
```

## 标定方法

OpenCV 提供多种手眼标定方法：

- `TSAI` (默认): Tsai-Lenz 方法
- `PARK`: Park-Martin 方法
- `HORAUD`: Horaud 方法
- `ANDREFF`: Andreff 方法
- `DANIILIDIS`: Daniilidis 方法

在 `config.py` 中修改：

```python
CALIBRATION_CONFIG = {
    'calibration_method': 'TSAI',  # 改为其他方法
}
```

## 常见问题

### Q: 棋盘格检测不稳定？
A: 确保光线充足，棋盘格清晰，无反光

### Q: 标定误差大？
A: 增加标定样本数量，确保样本覆盖不同角度和位置

### Q: 需要多少组数据？
A: 至少3组，推荐10-15组，且机械臂姿态变化要多样化

### Q: 如何验证标定结果？
A: 使用标定结果进行坐标变换，验证是否准确

### Q: 如何让相机平行桌面？
A:
1. 使用 `parallel_monitor.py` 实时监控相机倾斜
2. 根据倾斜指示器调整机械臂姿态
3. 直到显示"相机状态: 平行"

### Q: 倾斜角度是什么意思？
A:
- Rx: 相机绕X轴旋转角度（俯仰）
- Ry: 相机绕Y轴旋转角度（左右）
- 当 Rx≈0 且 Ry≈0 时，相机平行桌面

## 平行监控程序

标定完成后，使用 `parallel_monitor.py` 实时监控相机是否平行桌面：

```bash
python parallel_monitor.py
```

详细说明请查看 `PARALLEL_MONITOR_README.md`

## 完整工作流程

```
1. 标定相机内参
   └─> python camera_calibration_helper.py

2. 进行手眼标定
   └─> python hand_eye_calibration.py
       └─> 收集多组数据
       └─> 计算cam2gripper矩阵

3. 验证/调整相机平行
   └─> python parallel_monitor.py
       └─> 观察倾斜指示器
       └─> 调整机械臂直到平行

4. 日常使用
   └─> python parallel_monitor.py
       └─> 实时监控相机姿态
```
