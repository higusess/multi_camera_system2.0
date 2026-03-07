"""
相机抽象基类
Camera Abstract Base Class

定义相机接口的抽象基类，所有相机实现都需要继承此类
"""

from abc import ABC, abstractmethod
import threading
import queue
import time


class CameraBase(ABC):
    """相机抽象基类"""

    def __init__(self, camera_name: str):
        """
        初始化相机

        Args:
            camera_name: 相机名称
        """
        self.camera_name = camera_name
        self.is_opened = False
        self.is_grabbing = False

        # 多线程采集相关
        self.frame_queue = queue.Queue(maxsize=10)  # 限制队列大小避免缓存爆炸
        # ======低延迟模式========
        # self.latest_frame = None
        # self.frame_lock = threading.Lock()

        self.capture_thread = None
        self.stop_event = threading.Event()

        # 相机参数
        self.width = 0
        self.height = 0
        self.fps = 0

    @abstractmethod
    def enum_devices(self):
        """枚举设备"""
        pass

    @abstractmethod
    def open(self, device_index=0):
        """打开相机"""
        pass

    @abstractmethod
    def close(self):
        """关闭相机"""
        pass

    @abstractmethod
    def start_grabbing(self):
        """开始取流"""
        pass

    @abstractmethod
    def stop_grabbing(self):
        """停止取流"""
        pass

    @abstractmethod
    def _read_frame_raw(self, timeout_ms=1000):
        """
        原始读取一帧（由子类实现）

        Args:
            timeout_ms: 超时时间（毫秒）

        Returns:
            帧数据（numpy数组）或None
        """
        pass

    def read_frame(self, timeout_ms=1000):
        """
        读取一帧图像（从队列获取）

        Args:
            timeout_ms: 超时时间（毫秒）

        Returns:
            帧数据（numpy数组）或None
        """
        # ====低延时模式，以下整段替换====
        # with self.frame_lock:
        #     return self.latest_frame
        try:
            return self.frame_queue.get(timeout=timeout_ms / 1000)
        except queue.Empty:
            return None

    def start_capture_thread(self):
        """启动采集线程"""
        if self.capture_thread is not None and self.capture_thread.is_alive():
            print(f"{self.camera_name}: 采集线程已在运行")
            return

        self.stop_event.clear()
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            name=f"{self.camera_name}_capture",
            daemon=True
        )
        self.capture_thread.start()
        print(f"{self.camera_name}: 采集线程已启动")

    def stop_capture_thread(self):
        """停止采集线程"""
        if self.capture_thread is not None:
            self.stop_event.set()
            if self.capture_thread.is_alive():
                self.capture_thread.join(timeout=2.0)
            self.capture_thread = None
            print(f"{self.camera_name}: 采集线程已停止")

    def _capture_loop(self):
        """采集循环（在独立线程中运行）"""
        print(f"{self.camera_name}: 采集循环开始")

        while not self.stop_event.is_set():
            try:
                frame = self._read_frame_raw(timeout_ms=100)

                if frame is not None:
                    # 使用非阻塞方式放入队列
                    try:
                        self.frame_queue.put_nowait(frame)
                    except queue.Full:
                        # 队列已满，丢弃最旧的帧
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait(frame)
                        except queue.Empty:
                            pass
                else:
                    # 读取失败，短暂休眠
                    time.sleep(0.001)

            except Exception as e:
                print(f"{self.camera_name}: 采集循环出错: {e}")
                time.sleep(0.1)

        print(f"{self.camera_name}: 采集循环结束")

    def get_frame_count(self):
        """获取当前队列中的帧数"""
        return self.frame_queue.qsize()

    def clear_queue(self):
        """清空队列"""
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
        print(f"{self.camera_name}: 队列已清空")

    def get_info(self):
        """获取相机信息"""
        return {
            'name': self.camera_name,
            'opened': self.is_opened,
            'grabbing': self.is_grabbing,
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'queue_size': self.get_frame_count()
        }

    def __del__(self):
        """析构函数，确保资源释放"""
        self.stop_capture_thread()
        self.close()
