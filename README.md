# 多相机采集系统

同时控制USB相机和海康相机进行图像采集。

## 快速开始

### Windows用户

1. 双击 `START.bat` 启动程序

2. 或在命令行运行：
```bash
python multi_camera_capture.py
```

## 程序控制

| 按键 | 功能 |
|------|------|
| `q` | 退出程序 |
| `s` | 保存当前图像 |
| `i` | 显示相机信息 |

## 文件说明

| 文件 | 说明 |
|------|------|
| `multi_camera_capture.py` | 主程序，双相机同时采集 |
| `detect_cameras.py` | 检测可用相机 |
| `test_usb_camera.py` | 单独测试USB相机 |
| `test_hikvision_camera.py` | 单独测试海康相机 |
| `START.bat` | Windows快速启动脚本 |
| `INSTALL.md` | 详细安装和迁移指南 |
| `requirements.txt` | Python依赖包列表 |

## 首次使用？

请查看 `INSTALL.md` 获取完整的安装和配置指南。

## 图像保存位置

默认保存到：`D:\multi_camera_images\`

文件名格式：
- USB相机：`usb_YYYYMMDD_HHMMSS_mmm.jpg`
- 海康相机：`hikvision_YYYYMMDD_HHMMSS_mmm.jpg`
