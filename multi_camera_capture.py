"""
多相机同时采集程序
Multi-Camera Capture Program

同时控制USB相机和海康相机进行图像采集
使用多线程避免缓存爆炸
"""

import cv2
import numpy as np
import time
import os
from datetime import datetime
from threading import Thread
import signal
import sys

from usb_camera import UsbCamera
from hikvision_camera_impl import HikvisionCamera


class MultiCameraController:
    """多相机控制器"""

    def __init__(self, usb_camera_id: int = 0, hikvision_device_type: str = "USB", hikvision_index: int = 0):
        """
        初始化多相机控制器

        Args:
            usb_camera_id: USB相机设备ID
            hikvision_device_type: 海康相机设备类型 ("USB" 或 "GigE")
            hikvision_index: 海康相机设备索引
        """
        self.usb_camera = UsbCamera(camera_id=usb_camera_id)
        self.hikvision_camera = HikvisionCamera(device_type=hikvision_device_type, device_index=hikvision_index)

        self.running = False
        self.display_thread = None
        self.save_dir = r"D:\Multi_Camera_System\images"

        # 统计信息
        self.frame_counts = {'usb': 0, 'hikvision': 0}
        self.start_time = None

    def init_cameras(self):
        """初始化相机"""
        print("=" * 70)
        print("          多相机初始化")
        print("=" * 70)

        # 初始化USB相机
        print("\n[1/4] 初始化USB相机...")
        usb_devices = self.usb_camera.enum_devices()
        if usb_devices is None:
            print("未找到USB相机")
            return False

        # 使用指定的设备ID
        print(f"打开USB相机 (ID: {self.usb_camera.camera_id})...")
        if not self.usb_camera.open(self.usb_camera.camera_id):
            print("打开USB相机失败")
            return False

        # 设置连续采集模式
        self.usb_camera.start_grabbing()
        self.usb_camera.start_capture_thread()

        # 初始化海康相机
        print("\n[2/4] 初始化海康相机...")
        hikvision_devices = self.hikvision_camera.enum_devices()
        if hikvision_devices is None:
            print("未找到海康相机")
            self.usb_camera.stop_capture_thread()
            self.usb_camera.stop_grabbing()
            self.usb_camera.close()
            return False

        print(f"打开海康相机 (索引: {self.hikvision_camera.device_index})...")
        if not self.hikvision_camera.open(self.hikvision_camera.device_index):
            print("打开海康相机失败")
            self.usb_camera.stop_capture_thread()
            self.usb_camera.stop_grabbing()
            self.usb_camera.close()
            return False

        # 设置连续采集模式
        print("  设置触发模式为连续采集...")
        self.hikvision_camera.set_trigger_mode(0)

        print("  开始取流...")
        if not self.hikvision_camera.start_grabbing():
            print("  警告: 海康相机开始取流失败")
        else:
            print("  取流启动成功")

        print("  启动采集线程...")
        self.hikvision_camera.start_capture_thread()
        print("  采集线程已启动")

        # 创建保存目录
        print("\n[3/4] 创建保存目录...")
        os.makedirs(self.save_dir, exist_ok=True)

        # 显示相机信息
        print("\n[4/4] 相机信息:")
        print(f"  USB相机: {self.usb_camera.get_info()}")
        print(f"  海康相机: {self.hikvision_camera.get_info()}")

        print("\n" + "=" * 70)
        print("          多相机初始化完成！")
        print("=" * 70)

        return True

    def start_display(self):
        """启动显示线程"""
        self.running = True
        self.start_time = time.time()
        self.display_thread = Thread(target=self._display_loop, daemon=True)
        self.display_thread.start()

    def stop_display(self):
        """停止显示"""
        self.running = False
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=2.0)

    def _display_loop(self):
        """显示循环"""
        print("\n显示循环已启动")
        hikvision_frame_count = 0
        hikvision_show_window = False

        while self.running:
            # 获取USB相机帧
            usb_frame = self.usb_camera.read_frame(timeout_ms=100)
            if usb_frame is not None:
                self.frame_counts['usb'] += 1
                usb_frame = self._add_info(usb_frame, self.usb_camera.camera_name, self.frame_counts['usb'])

            # 获取海康相机帧
            hikvision_frame = self.hikvision_camera.read_frame(timeout_ms=100)
            if hikvision_frame is not None:
                self.frame_counts['hikvision'] += 1
                hikvision_frame_count += 1
                hikvision_frame = self._add_info(hikvision_frame, self.hikvision_camera.camera_name, self.frame_counts['hikvision'])

                # 显示调试信息
                if hikvision_frame_count == 1:
                    print(f"海康相机成功读取第一帧: {hikvision_frame.shape}")

            # 显示帧
            if usb_frame is not None:
                cv2.imshow("USB Camera", usb_frame)

            if hikvision_frame is not None:
                cv2.imshow("Hikvision Camera", hikvision_frame)
                hikvision_show_window = True

            # 定期检查海康相机状态
            if hikvision_frame_count == 10 and not hikvision_show_window:
                print("警告: 海康相机已读取10帧但未显示窗口")

            # 检查按键
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                self.running = False
                print("\n退出程序...")
                break

            elif key == ord('s'):
                self.save_images()

            elif key == ord('i'):
                self.show_info()

        print("显示循环已结束")

    def _add_info(self, frame, camera_name, frame_count):
        """在帧上添加信息"""
        height, width = frame.shape[:2]
        overlay = frame.copy()

        # 背景
        cv2.rectangle(overlay, (10, 10), (350, 130), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

        # 相机名称
        cv2.putText(frame, camera_name, (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # 时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        cv2.putText(frame, f"Time: {timestamp}", (20, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # 帧数
        cv2.putText(frame, f"Frame: {frame_count}", (20, 95),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # FPS
        elapsed = time.time() - self.start_time if self.start_time else 0
        fps = frame_count / elapsed if elapsed > 0 else 0
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        return frame

    def save_images(self):
        """保存当前图像"""
        usb_frame = self.usb_camera.read_frame(timeout_ms=100)
        hikvision_frame = self.hikvision_camera.read_frame(timeout_ms=100)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')

        if usb_frame is not None:
            usb_filename = os.path.join(self.save_dir, f"usb_{timestamp}.jpg")
            cv2.imwrite(usb_filename, usb_frame)
            print(f"已保存USB图像: {usb_filename}")

        if hikvision_frame is not None:
            hikvision_filename = os.path.join(self.save_dir, f"hikvision_{timestamp}.jpg")
            cv2.imwrite(hikvision_filename, hikvision_frame)
            print(f"已保存海康图像: {hikvision_filename}")

    def show_info(self):
        """显示相机信息"""
        print("\n" + "=" * 70)
        print("相机状态信息:")
        print("-" * 70)
        print(f"USB相机:")
        print(f"  打开状态: {self.usb_camera.is_opened}")
        print(f"  取流状态: {self.usb_camera.is_grabbing}")
        print(f"  分辨率: {self.usb_camera.width}x{self.usb_camera.height}")
        print(f"  帧率: {self.usb_camera.fps:.1f} FPS")
        print(f"  队列大小: {self.usb_camera.get_frame_count()}")
        print(f"  总帧数: {self.frame_counts['usb']}")

        print(f"\n海康相机:")
        print(f"  打开状态: {self.hikvision_camera.is_opened}")
        print(f"  取流状态: {self.hikvision_camera.is_grabbing}")
        print(f"  分辨率: {self.hikvision_camera.width}x{self.hikvision_camera.height}")
        print(f"  帧率: {self.hikvision_camera.fps:.1f} FPS")
        print(f"  队列大小: {self.hikvision_camera.get_frame_count()}")
        print(f"  总帧数: {self.frame_counts['hikvision']}")

        elapsed = time.time() - self.start_time if self.start_time else 0
        print(f"\n运行时间: {elapsed:.1f} 秒")
        print("=" * 70)

    def close(self):
        """关闭所有相机"""
        print("\n正在关闭相机...")

        self.stop_display()

        # 关闭海康相机
        self.hikvision_camera.stop_capture_thread()
        self.hikvision_camera.stop_grabbing()
        self.hikvision_camera.close()

        # 关闭USB相机
        self.usb_camera.stop_capture_thread()
        self.usb_camera.stop_grabbing()
        self.usb_camera.close()

        cv2.destroyAllWindows()

        print("所有相机已关闭")


def main():
    """主函数"""
    print("=" * 70)
    print("          多相机同时采集程序")
    print("=" * 70)
    print("\n控制说明:")
    print("  q - 退出程序")
    print("  s - 保存当前图像")
    print("  i - 显示相机信息")
    print("=" * 70)

    # 创建控制器
    controller = MultiCameraController(
        usb_camera_id=0,          # USB相机ID
        hikvision_device_type="USB",  # 海康相机类型
        hikvision_index=0          # 海康相机索引
    )

    # 设置信号处理
    def signal_handler(sig, frame):
        print("\n接收到中断信号")
        controller.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 初始化相机
        if not controller.init_cameras():
            print("相机初始化失败")
            return

        # 启动显示
        controller.start_display()

        # 等待显示线程结束
        while controller.display_thread and controller.display_thread.is_alive():
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n程序出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        controller.close()
        print("\n程序结束")


if __name__ == "__main__":
    main()
