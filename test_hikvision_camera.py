"""
海康相机单独测试程序
Hikvision Camera Test Program

单独测试海康相机的采集功能
"""

import cv2
import time
from datetime import datetime
from hikvision_camera_impl import HikvisionCamera


def main():
    print("=" * 70)
    print("          海康相机测试程序")
    print("=" * 70)

    # 创建海康相机
    camera = HikvisionCamera(device_type="USB", device_index=0)

    # 枚举设备
    devices = camera.enum_devices()
    if devices is None:
        print("\n未找到海康相机")
        return

    # 打开相机
    print(f"\n打开海康相机 (索引: 0)...")
    if not camera.open(0):
        print("打开相机失败")
        return

    # 设置连续采集模式
    camera.set_trigger_mode(0)

    # 开始取流
    camera.start_grabbing()
    camera.start_capture_thread()

    print("\n相机已就绪！")
    print("\n控制说明:")
    print("  q - 退出程序")
    print("  s - 保存当前画面")
    print("  i - 显示相机信息")
    print("  p - 显示相机参数")
    print("=" * 70)

    frame_count = 0
    start_time = time.time()

    try:
        while True:
            # 读取帧
            frame = camera.read_frame(timeout_ms=100)

            if frame is not None:
                frame_count += 1
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                fps = frame_count / (time.time() - start_time) if time.time() > start_time else 0

                # 添加信息
                cv2.putText(frame, "Hikvision Camera", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(frame, f"Time: {timestamp}", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.putText(frame, f"FPS: {fps:.1f}", (10, 85),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.putText(frame, f"Frame: {frame_count}", (10, 110),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.putText(frame, f"Queue: {camera.get_frame_count()}", (10, 135),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                cv2.imshow("Hikvision Camera", frame)

            # 检查按键
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                print("\n退出程序...")
                break

            elif key == ord('s'):
                if frame is not None:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    filename = f"hikvision_test_{timestamp}.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"\n已保存: {filename}")

            elif key == ord('i'):
                print("\n相机信息:")
                print(f"  打开状态: {camera.is_opened}")
                print(f"  取流状态: {camera.is_grabbing}")
                print(f"  分辨率: {camera.width}x{camera.height}")
                print(f"  帧率: {camera.fps:.1f} FPS")
                print(f"  队列大小: {camera.get_frame_count()}")
                print(f"  总帧数: {frame_count}")

            elif key == ord('p'):
                params = camera.get_current_params()
                print("\n相机参数:")
                for key, value in params.items():
                    print(f"  {key}: {value}")

    except KeyboardInterrupt:
        print("\n程序被用户中断")

    finally:
        camera.stop_capture_thread()
        camera.stop_grabbing()
        camera.close()
        cv2.destroyAllWindows()
        print("\n程序结束")


if __name__ == "__main__":
    main()
