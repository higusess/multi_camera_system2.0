# 多相机采集系统使用说明

## 概述

本系统提供了一套完整的多相机采集解决方案，支持同时控制USB相机和海康相机进行图像采集。系统采用多线程架构，有效避免缓存爆炸问题。

## 文件结构

```
C:/Users/admin/
├── camera_base.py              # 相机抽象基类（必须）
├── usb_camera.py               # USB相机实现
├── hikvision_camera_impl.py    # 海康相机实现
├── multi_camera_capture.py     # 多相机同时采集主程序
├── test_usb_camera.py          # USB相机单独测试程序
├── test_hikvision_camera.py    # 海康相机单独测试程序
└── README_MULTI_CAMERA.md      # 本说明文档
```

## 系统架构

### 1. 抽象基类 (camera_base.py)

定义了所有相机必须实现的接口：
- `enum_devices()` - 枚举设备
- `open()` - 打开相机
- `close()` - 关闭相机
- `start_grabbing()` - 开始取流
- `stop_grabbing()` - 停止取流
- `_read_frame_raw()` - 原始读取一帧（子类实现）
- `read_frame()` - 从队列读取一帧
- `start_capture_thread()` - 启动采集线程
- `stop_capture_thread()` - 停止采集线程

### 2. 多线程缓存控制

- 使用 `queue.Queue` 限制帧队列大小（默认10帧）
- 采集线程在独立线程中运行，持续读取并放入队列
- 主线程从队列获取帧进行显示/处理
- 队列满时自动丢弃最旧的帧，避免缓存爆炸

## 使用方法

### 1. 测试单个相机

#### 测试USB相机

```bash
python test_usb_camera.py
```

控制键：
- `q` - 退出程序
- `s` - 保存当前画面
- `i` - 显示相机信息

#### 测试海康相机

```bash
python test_hikvision_camera.py
```

控制键：
- `q` - 退出程序
- `s` - 保存当前画面
- `i` - 显示相机信息
- `p` - 显示相机参数

### 2. 同时采集两个相机

```bash
python multi_camera_capture.py
```

控制键：
- `q` - 退出程序
- `s` - 保存当前图像（两个相机同时保存）
- `i` - 显示相机状态信息

### 3. 在自己的程序中使用

```python
from usb_camera import UsbCamera
from hikvision_camera_impl import HikvisionCamera

# 创建相机实例
usb_cam = UsbCamera(camera_id=0)
hik_cam = HikvisionCamera(device_type="USB", device_index=0)

# 打开相机
usb_cam.open()
hik_cam.open()

# 开始取流
usb_cam.start_grabbing()
hik_cam.start_grabbing()

# 启动采集线程
usb_cam.start_capture_thread()
hik_cam.start_capture_thread()

# 读取帧（非阻塞）
usb_frame = usb_cam.read_frame(timeout_ms=100)
hik_frame = hik_cam.read_frame(timeout_ms=100)

# 处理帧...

# 关闭相机
usb_cam.stop_capture_thread()
hik_cam.stop_capture_thread()
usb_cam.stop_grabbing()
hik_cam.stop_grabbing()
usb_cam.close()
hik_cam.close()
```

## 配置说明

### USB相机配置

在 `multi_camera_capture.py` 中修改：

```python
controller = MultiCameraController(
    usb_camera_id=0,          # 修改为你的USB相机ID
    hikvision_device_type="USB",  # 海康相机类型
    hikvision_index=0          # 海康相机索引
)
```

### 海康相机配置

海康相机有两种类型：
- `device_type="USB"` - USB接口相机
- `device_type="GigE"` - 网口相机

### 队列大小调整

如需调整队列大小（控制缓存），在 `camera_base.py` 中修改：

```python
self.frame_queue = queue.Queue(maxsize=10)  # 改为你想要的大小
```

## 参数设置

### USB相机参数

```python
# 设置分辨率
camera.set_resolution(1920, 1080)

# 设置帧率
camera.set_fps(30.0)

# 设置亮度
camera.set_brightness(0.5)

# 设置对比度
camera.set_contrast(0.5)

# 设置饱和度
camera.set_saturation(0.5)
```

### 海康相机参数

```python
# 设置曝光时间（微秒）
camera.set_exposure_time(10000)

# 设置增益（dB）
camera.set_gain(5.0)

# 设置触发模式（0=连续，1=触发）
camera.set_trigger_mode(0)

# 设置ROI区域
camera.set_roi(0, 0, 1920, 1080)

# 设置帧率
camera.set_frame_rate(30.0)

# 设置像素格式
camera.set_pixel_format("BGR8Packed")
```

## 故障排除

### 问题1：找不到相机

- 检查相机是否正确连接
- 检查相机是否被其他程序占用
- 运行单独测试程序检查单个相机是否正常

### 问题2：帧率低

- 检查USB带宽是否充足
- 降低分辨率或帧率
- 检查网络带宽（针对GigE相机）

### 问题3：内存占用过高

- 减小队列大小（`maxsize`）
- 检查是否有帧泄漏
- 确保正确关闭相机

### 问题4：海康相机SDK加载失败

- 检查MVS SDK是否正确安装
- 检查 `MVS_SDK_PATH` 和 `MVS_DLL_PATH` 是否正确
- 确保海康相机软件已关闭

## 性能建议

1. **队列大小**：一般设置为5-20帧，根据处理速度调整
2. **线程优先级**：采集线程使用daemon模式，不影响主线程
3. **帧丢弃策略**：队列满时自动丢弃旧帧，保证实时性
4. **资源释放**：始终调用 `close()` 方法释放相机资源

## 扩展开发

如需添加新的相机类型，只需：

1. 继承 `CameraBase` 类
2. 实现必需的抽象方法
3. 实现 `_read_frame_raw()` 方法

示例：

```python
from camera_base import CameraBase

class MyCamera(CameraBase):
    def __init__(self, device_id):
        super().__init__(camera_name=f"MyCamera_{device_id}")
        self.device_id = device_id

    def enum_devices(self):
        # 实现设备枚举
        pass

    def open(self, device_index=0):
        # 实现打开相机
        pass

    def close(self):
        # 实现关闭相机
        pass

    def start_grabbing(self):
        # 实现开始取流
        pass

    def stop_grabbing(self):
        # 实现停止取流
        pass

    def _read_frame_raw(self, timeout_ms=1000):
        # 实现原始读取一帧
        pass
```

## 依赖项

```bash
pip install opencv-python numpy
```

海康相机需要安装MVS SDK，请从海康官网下载。

## 许可

本代码仅供学习和研究使用。
