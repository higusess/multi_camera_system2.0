"""
相机处理模块
负责USB相机的打开、读取和关闭
"""
import cv2
import threading
import time


class CameraHandler:
    def __init__(self, camera_id=0, width=1280, height=720):
        """
        初始化相机

        Args:
            camera_id: 相机ID，默认为0
            width: 图像宽度
            height: 图像高度
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.cap = None
        self.is_running = False
        self.lock = threading.Lock()

    def open(self):
        """打开相机"""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"无法打开相机ID: {self.camera_id}")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        # 等待相机稳定
        time.sleep(0.5)

        self.is_running = True
        return True

    def read_frame(self):
        """
        读取一帧图像

        Returns:
            numpy.ndarray: 图像帧，失败返回None
        """
        if not self.is_running or self.cap is None:
            return None

        with self.lock:
            ret, frame = self.cap.read()
            return frame if ret else None

    def close(self):
        """关闭相机"""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def __del__(self):
        """析构函数，确保相机关闭"""
        self.close()
