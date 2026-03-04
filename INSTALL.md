# 多相机采集系统 - 安装和迁移指南

## 目录结构

```
D:\Multi_Camera_System\
├── camera_base.py              # 相机基类
├── usb_camera.py               # USB相机实现
├── hikvision_camera_impl.py    # 海康相机实现
├── multi_camera_capture.py     # 主程序（多相机同时采集）
├── detect_cameras.py           # 相机检测工具
├── test_usb_camera.py          # USB相机测试
├── test_hikvision_camera.py    # 海康相机测试
├── requirements.txt            # Python依赖包
├── INSTALL.md                  # 本安装指南
└── README.md                   # 使用说明
```

## 系统要求

### 1. 操作系统
- Windows 10/11 (64位)

### 2. Python环境
- Python 3.8 或更高版本

### 3. 相机设备
- USB相机（任意品牌）
- 海康威视工业相机

## 安装步骤

### 第一步：安装Python

从官网下载并安装Python：https://www.python.org/downloads/

安装时务必勾选 "Add Python to PATH"

### 第二步：安装MVS SDK（海康相机必需）

1. 访问海康官网下载MVS SDK
   - 网址：https://www.hikrobot.com/cn/machinevision/service/download

2. 下载并安装 "MVS_标准版"

3. 确认安装路径（默认）：
   - SDK路径：`C:\Program Files (x86)\MVS\Development\Samples\Python`
   - DLL路径：`C:\Program Files (x86)\Common Files\MVS\Runtime\Win64_x64`

### 第三步：安装Python依赖包

打开命令提示符（CMD）或PowerShell，进入项目目录：

```bash
cd D:\Multi_Camera_System
pip install -r requirements.txt
```

如果下载速度慢，可以使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 第四步：修改SDK路径（如果安装路径不同）

如果MVS SDK安装在其他位置，请修改 `hikvision_camera_impl.py` 中的路径：

```python
# 第16-17行
MVS_SDK_PATH = r"C:\Program Files (x86)\MVS\Development\Samples\Python"
MVS_DLL_PATH = r"C:\Program Files (x86)\Common Files\MVS\Runtime\Win64_x64"
```

## 运行程序

### 1. 检测相机

```bash
python detect_cameras.py
```

### 2. 测试单个相机

```bash
# 测试USB相机
python test_usb_camera.py

# 测试海康相机
python test_hikvision_camera.py
```

### 3. 运行主程序（双相机）

```bash
python multi_camera_capture.py
```

**控制键：**
- `q` - 退出程序
- `s` - 保存当前图像
- `i` - 显示相机信息

## 配置说明

### 修改相机配置

编辑 `multi_camera_capture.py` 第264-268行：

```python
controller = MultiCameraController(
    usb_camera_id=0,          # USB相机ID（0, 1, 2...）
    hikvision_device_type="USB",  # 海康相机类型："USB" 或 "GigE"
    hikvision_index=0          # 海康相机索引
)
```

### 修改图像保存路径

编辑 `multi_camera_capture.py` 第39行：

```python
self.save_dir = r"D:\multi_camera_images"  # 修改为你想要的路径
```

## 故障排除

### 问题1：找不到海康相机
- 检查MVS SDK是否正确安装
- 检查相机是否连接正常
- 检查是否被其他程序占用（如海康MVS客户端）

### 问题2：DLL加载失败
- 确认MVS SDK路径配置正确
- 确保使用64位Python
- 重启电脑后再试

### 问题3：USB相机打不开
- 检查USB连接是否正常
- 尝试更换USB端口
- 使用 `detect_cameras.py` 查看可用相机

### 问题4：只有一个窗口显示
- 按 `i` 键查看相机状态
- 检查对应的相机是否正常连接
- 运行单独测试程序排查

## 常见错误代码

| 错误 | 原因 | 解决方法 |
|------|------|----------|
| 0x80000000 | 内存不足 | 关闭其他程序 |
| 0x80000002 | 句柄无效 | 重启程序 |
| 0x80000003 | 超时 | 检查相机连接 |
| 0x80000007 | 相机被占用 | 关闭其他相机程序 |

## 迁移到新计算机

1. 将整个 `Multi_Camera_System` 文件夹复制到新计算机
2. 按照"安装步骤"安装Python和MVS SDK
3. 安装Python依赖包
4. 运行 `detect_cameras.py` 测试相机

## 技术支持

如遇问题，请检查：
1. Python版本是否正确
2. 所有依赖包是否安装
3. MVS SDK是否正确安装
4. 相机驱动是否正常

---

最后更新：2026-02-28
