"""
USB相机实现
USB Camera Implementation

使用OpenCV的VideoCapture控制USB相机
"""

import cv2
import numpy as np
from typing import Optional
from camera_base import CameraBase


class UsbCamera(CameraBase):
    """USB相机实现类"""

    def __init__(self, camera_id: int = 0):
        """
        初始化USB相机

        Args:
            camera_id: 相机设备ID，默认为0
        """
        super().__init__(camera_name=f"USB_Camera_{camera_id}")
        self.camera_id = camera_id
        self.cap = None

    def enum_devices(self):
        """枚举USB相机设备"""
        print(f"\n正在枚举USB相机设备...")

        available_cameras = []
        for i in range(10):  # 检查前10个设备
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                available_cameras.append(i)
                ret, _ = cap.read()
                if ret:
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    print(f"  设备 {i}: {width}x{height} @ {fps:.1f} FPS")
                else:
                    print(f"  设备 {i}: 可用但无法读取帧")
                cap.release()

        if not available_cameras:
            print("未找到任何USB相机设备")
            return None

        print(f"\n找到 {len(available_cameras)} 个USB相机设备")
        return available_cameras

    def open(self, device_index=0):
        """打开USB相机"""
        print(f"\n正在打开USB相机 (ID: {device_index})...")

        if self.is_opened:
            print(f"{self.camera_name}: 相机已打开")
            return True

        self.cap = cv2.VideoCapture(device_index, cv2.CAP_DSHOW)

        if not self.cap.isOpened():
            print(f"{self.camera_name}: 打开相机失败")
            return False

        # 获取相机参数
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        self.is_opened = True
        print(f"{self.camera_name}: 相机已打开!")
        print(f"  分辨率: {self.width}x{self.height}")
        print(f"  帧率: {self.fps:.1f} FPS")

        return True

    def close(self):
        """关闭USB相机"""
        if self.cap is not None:
            self.stop_grabbing()
            self.cap.release()
            self.cap = None
            self.is_opened = False
            print(f"{self.camera_name}: 相机已关闭")

    def start_grabbing(self):
        """开始取流"""
        if not self.is_opened:
            print(f"{self.camera_name}: 相机未打开")
            return False

        if self.is_grabbing:
            print(f"{self.camera_name}: 已在取流中")
            return True

        self.is_grabbing = True
        print(f"{self.camera_name}: 开始取流")
        return True

    def stop_grabbing(self):
        """停止取流"""
        if self.is_grabbing:
            self.is_grabbing = False
            print(f"{self.camera_name}: 停止取流")

    def _read_frame_raw(self, timeout_ms=1000):
        """
        原始读取一帧

        Args:
            timeout_ms: 超时时间（毫秒）

        Returns:
            帧数据（numpy数组）或None
        """
        if not self.is_grabbing:
            return None

        if self.cap is None:
            return None

        ret, frame = self.cap.read()

        if ret and frame is not None:
            return frame

        return None

    # ============ 参数设置方法 ============

    def set_resolution(self, width: int, height: int) -> bool:
        """
        设置分辨率

        Args:
            width: 宽度
            height: 高度

        Returns:
            是否成功
        """
        if not self.is_opened:
            return False

        ret1 = self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        ret2 = self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        if ret1 and ret2:
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"{self.camera_name}: 分辨率已设置为 {self.width}x{self.height}")
            return True

        return False

    def set_fps(self, fps: float) -> bool:
        """
        设置帧率

        Args:
            fps: 帧率

        Returns:
            是否成功
        """
        if not self.is_opened:
            return False

        ret = self.cap.set(cv2.CAP_PROP_FPS, fps)
        if ret:
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            print(f"{self.camera_name}: 帧率已设置为 {self.fps:.1f} FPS")
            return True

        return False

    def set_brightness(self, brightness: float) -> bool:
        """
        设置亮度

        Args:
            brightness: 亮度值 (0.0 - 1.0)

        Returns:
            是否成功
        """
        if not self.is_opened:
            return False

        return self.cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)

    def set_contrast(self, contrast: float) -> bool:
        """
        设置对比度

        Args:
            contrast: 对比度值 (0.0 - 1.0)

        Returns:
            是否成功
        """
        if not self.is_opened:
            return False

        return self.cap.set(cv2.CAP_PROP_CONTRAST, contrast)

    def set_saturation(self, saturation: float) -> bool:
        """
        设置饱和度

        Args:
            saturation: 饱和度值 (0.0 - 1.0)

        Returns:
            是否成功
        """
        if not self.is_opened:
            return False

        return self.cap.set(cv2.CAP_PROP_SATURATION, saturation)

    def set_exposure(self, exposure: float) -> bool:
        """
        设置曝光

        Args:
            exposure: 曝光值

        Returns:
            是否成功
        """
        if not self.is_opened:
            return False

        return self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure)

    def get_camera_properties(self) -> dict:
        """获取相机属性"""
        if not self.is_opened:
            return {}

        props = {
            'width': self.cap.get(cv2.CAP_PROP_FRAME_WIDTH),
            'height': self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
            'brightness': self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
            'contrast': self.cap.get(cv2.CAP_PROP_CONTRAST),
            'saturation': self.cap.get(cv2.CAP_PROP_SATURATION),
            'exposure': self.cap.get(cv2.CAP_PROP_EXPOSURE),
            'auto_exposure': self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE),
            'gain': self.cap.get(cv2.CAP_PROP_GAIN),
        }

        return props

    def get_available_resolutions(self) -> list:
        """
        获取相机支持的分辨率列表

        Returns:
            支持的分辨率列表 [(width, height), ...]
        """
        if not self.is_opened:
            return []

        # 常见的分辨率列表
        common_resolutions = [
            (640, 480),
            (800, 600),
            (1024, 768),
            (1280, 720),
            (1920, 1080),
            (2560, 1440),
            (3840, 2160),
        ]

        available = []
        for w, h in common_resolutions:
            old_w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            old_h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

            ret1 = self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            ret2 = self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

            if ret1 and ret2:
                actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                if actual_w == w and actual_h == h:
                    available.append((w, h))

            # 恢复原分辨率
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, old_w)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, old_h)

        return available
