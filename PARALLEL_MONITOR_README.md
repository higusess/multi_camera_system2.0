# 相机平行桌面实时监控

## 概述

此程序用于实时监控相机是否平行于桌面，帮助您在机械臂运动过程中保持相机平行于桌面。

## 使用场景

- 标定完成后，监控相机是否平行桌面
- 机械臂运动过程中，实时检测相机姿态偏差
- 根据倾斜角度调整机械臂，使相机恢复平行

## 快速开始

### 1. 先标定相机内参

如果还没有标定相机内参，运行：

```bash
python camera_calibration_helper.py
```

### 2. 运行平行监控程序

```bash
python parallel_monitor.py
```

程序会自动加载 `camera_calibration_results/camera_params.py` 中的相机参数。

## 画面说明

### 左下角：倾斜指示器
```
┌─────────────────────────────┐
│ 相机状态: 平行/倾斜         │
│ 倾斜 X: 1.23°              │
│ 倾斜 Y: -0.45°             │
│ 总倾斜: 1.31°              │
│ 调整: X -1.2°, Y 0.5°      │ ← 需要调整时显示
└─────────────────────────────┘
```

- **绿色边框** = 相机平行桌面
- **红色边框** = 相机倾斜

### 右下角：水平仪
```
         LEVEL
       ┌─────────┐
       │    ┼    │  ← 中心点（红色）
       │  ●     │  ← 气泡（橙色）
       └─────────┘
```

- 气泡偏离中心表示相机倾斜
- 气泡方向与相机倾斜方向相反

### 右上角：角度显示
```
┌─────────────────────┐
│ Target to Cam Angles│
│ Rx (°): 1.23        │
│ Ry (°): -0.45       │
│ Rz (°): 0.00        │
└─────────────────────┘
```

## 操作按键

| 按键 | 功能 |
|------|------|
| `H` | 显示帮助 |
| `T` | 打印当前倾斜角度（控制台） |
| `S` | 保存当前 target2cam 矩阵 |
| `P` | 设置相机参数 |
| `Q` / `ESC` | 退出程序 |

## 倾斜角度说明

### X轴倾斜 (Rx)
- 相机绕其X轴旋转
- 正值：相机前端向下倾斜
- 负值：相机前端向上倾斜

### Y轴倾斜 (Ry)
- 相机绕其Y轴旋转
- 正值：相机向右倾斜
- 负值：相机向左倾斜

### 总倾斜角度
- 相机Z轴与桌面法向量的夹角
- 0° = 完全平行
- > 2° = 需要调整

## 调整机械臂

当相机倾斜时，根据提示调整机械臂姿态：

```
调整: X -1.2°, Y 0.5°
```

表示：
- 机械臂 Rx 需要调整 -1.2°
- 机械臂 Ry 需要调整 0.5°

## 完整工作流程

### 第一次使用（标定）

```bash
# 1. 标定相机内参
python camera_calibration_helper.py

# 2. 进行手眼标定
python hand_eye_calibration.py

# 3. 标定完成后，使用平行监控
python parallel_monitor.py
```

### 日常使用（监控）

```bash
# 直接运行监控程序
python parallel_monitor.py
```

## 与手眼标定的关系

1. **手眼标定**：计算相机与机械臂末端的变换矩阵 (cam2gripper)
2. **平行监控**：实时检测相机是否平行桌面

两者可以结合使用：
- 标定后，使用平行监控验证相机平行
- 如果相机不平行，调整机械臂姿态
- 重复调整直到相机平行

## 程序集成

### 在代码中使用

```python
from parallel_monitor import ParallelMonitor
import numpy as np

# 创建监控器
monitor = ParallelMonitor(
    camera_id=0,
    chessboard_size=(9, 9),
    square_size=18.0,
    camera_matrix=camera_matrix,  # 您的相机内参
    dist_coeffs=dist_coeffs       # 您的畸变系数
)

# 检查是否平行
if monitor.current_tilt_info:
    is_parallel = monitor.current_tilt_info['is_parallel']
    tilt_x = monitor.current_tilt_info['tilt_x_deg']
    tilt_y = monitor.current_tilt_info['tilt_y_deg']

    print(f"平行: {is_parallel}")
    print(f"倾斜X: {tilt_x:.2f}°")
    print(f"倾斜Y: {tilt_y:.2f}°")
```

### 多线程集成

```python
import threading
from parallel_monitor import ParallelMonitor

class MonitorThread(threading.Thread):
    def __init__(self, camera_id):
        super().__init__()
        self.monitor = ParallelMonitor(camera_id)
        self.running = False

    def run(self):
        self.monitor.camera.open()
        self.running = True

        while self.running:
            frame = self.monitor.camera.read_frame()
            if frame is not None:
                # 检测和计算倾斜
                display_frame, corners, detected = self.monitor.detector.detect(frame)

                if detected:
                    success, rvec, tvec = self.monitor.detector.solve_pnp(
                        corners,
                        self.monitor.camera_matrix,
                        self.monitor.dist_coeffs
                    )
                    if success:
                        self.monitor.current_tilt_info = \
                            self.monitor.detector.get_camera_table_tilt(rvec)

        self.monitor.camera.close()

    def stop(self):
        self.running = False
```

## 故障排查

### 问题：检测不稳定
- 确保光线充足
- 棋盘格清晰可见
- 相机对焦正确

### 问题：角度数值跳动
- 检查棋盘格是否固定牢固
- 检查相机是否安装牢固
- 增加角点亚像素优化的迭代次数

### 问题：无法加载相机参数
- 确认 `camera_calibration_results/camera_params.py` 存在
- 检查文件格式是否正确
- 或使用 `P` 键手动输入参数
