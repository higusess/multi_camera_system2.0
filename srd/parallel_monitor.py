"""
相机平行桌面实时监控程序
用于在标定后实时监控相机是否平行于桌面
"""
import cv2
import numpy as np
from camera_handler import CameraHandler
from chessboard_detector import ChessboardDetector
from ui_overlay import UIOverlay


class ParallelMonitor:
    """相机平行桌面监控器"""

    def __init__(self, camera_id=0, chessboard_size=(9, 9), square_size=18.0,
                 camera_matrix=None, dist_coeffs=None):
        """
        初始化监控器

        Args:
            camera_id: 相机ID
            chessboard_size: 棋盘格内角点数量 (cols, rows)
            square_size: 每个格子的物理尺寸 (mm)
            camera_matrix: 相机内参矩阵
            dist_coeffs: 畸变系数
        """
        self.camera = CameraHandler(camera_id)
        self.detector = ChessboardDetector(chessboard_size, square_size)
        self.ui = UIOverlay()

        # 相机参数
        if camera_matrix is not None and dist_coeffs is not None:
            self.camera_matrix = camera_matrix
            self.dist_coeffs = dist_coeffs
        else:
            # 默认参数（请使用实际标定参数）
            self.camera_matrix = np.array([
                [1000, 0, 640],
                [0, 1000, 360],
                [0, 0, 1]
            ], dtype=np.float32)
            self.dist_coeffs = np.zeros((5, 1), dtype=np.float32)

        self.is_running = False
        self.current_tilt_info = None

    def load_calibration(self, filepath):
        """
        加载相机参数文件

        Args:
            filepath: 相机参数文件路径
        """
        try:
            # 尝试从 Python 文件加载
            spec = __import__('importlib.util').util.spec_from_file_location("cam_params", filepath)
            module = __import__('importlib.util').util.module_from_spec(spec)
            spec.loader.exec_module(module)

            self.camera_matrix = module.camera_matrix
            self.dist_coeffs = module.dist_coeffs
            print(f"相机参数已加载: {filepath}")
            return True
        except Exception as e:
            print(f"加载相机参数失败: {e}")
            return False

    def print_tilt_info(self):
        """打印当前倾斜信息"""
        if self.current_tilt_info is None:
            print("\n未检测到棋盘格")
            return

        print("\n" + "="*50)
        print("相机与桌面夹角")
        print("="*50)
        print(f"X轴倾斜 (Rx): {self.current_tilt_info['tilt_x_deg']:.4f}°")
        print(f"Y轴倾斜 (Ry): {self.current_tilt_info['tilt_y_deg']:.4f}°")
        print(f"总倾斜角度: {self.current_tilt_info['tilt_angle_deg']:.4f}°")

        status = "平行 ✓" if self.current_tilt_info['is_parallel'] else "倾斜 ✗"
        print(f"状态: {status}")

        if not self.current_tilt_info['is_parallel']:
            print("\n调整建议:")
            rx = self.current_tilt_info['tilt_x_deg']
            ry = self.current_tilt_info['tilt_y_deg']
            print(f"  机械臂Rx需要调整: {-rx:.2f}°")
            print(f"  机械臂Ry需要调整: {-ry:.2f}°")

        print("="*50 + "\n")

    def run(self):
        """运行监控"""
        print("\n" + "="*50)
        print("相机平行桌面实时监控")
        print("="*50)
        print("按键说明:")
        print("  [H]      - 显示帮助")
        print("  [T]      - 打印当前倾斜角度")
        print("  [S]      - 保存当前target2cam矩阵")
        print("  [P]      - 设置相机参数")
        print("  [Q] / [ESC] - 退出")
        print("="*50)
        print("\n目标: 使相机始终平行于桌面")
        print("绿色边框 = 平行，红色边框 = 倾斜")
        print("="*50 + "\n")

        try:
            if not self.camera.open():
                print("无法打开相机")
                return

            self.is_running = True
            print("相机已打开，开始监控...\n")

            while self.is_running:
                frame = self.camera.read_frame()
                if frame is None:
                    continue

                # 检测棋盘格
                display_frame, corners, detected = self.detector.detect(frame)

                if detected:
                    success, rvec, tvec = self.detector.solve_pnp(
                        corners, self.camera_matrix, self.dist_coeffs
                    )

                    if success:
                        # 计算倾斜
                        self.current_tilt_info = self.detector.get_camera_table_tilt(rvec)
                        rx, ry, rz = self.detector.rotation_vector_to_angles(rvec)

                        # 绘制角度显示
                        angles_dict = {'rx': rx, 'ry': ry, 'rz': rz}
                        self.ui.draw_angles_display(display_frame, angles_dict, 'top_right')

                        # 绘制倾斜指示器
                        self.ui.draw_tilt_indicator(display_frame, self.current_tilt_info)

                        # 绘制水平仪
                        self.ui.draw_level_indicator(display_frame,
                                                   self.current_tilt_info['tilt_x_deg'],
                                                   self.current_tilt_info['tilt_y_deg'])

                        # 绘制坐标轴
                        self.ui.draw_axis(display_frame, rvec, tvec,
                                        self.camera_matrix, self.dist_coeffs)
                else:
                    self.current_tilt_info = None

                # 状态栏
                status = "已检测" if detected else "未检测"
                color = (0, 255, 0) if detected else (0, 0, 255)
                self.ui.draw_status_bar(display_frame, f"棋盘格: {status} | 按[H]查看帮助", color)

                cv2.imshow('Parallel Monitor', display_frame)

                # 按键处理
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q') or key == 27:
                    self.is_running = False
                elif key == ord('h'):
                    print("\n" + "="*50)
                    print("相机平行桌面实时监控")
                    print("="*50)
                    print("按键说明:")
                    print("  [H]      - 显示帮助")
                    print("  [T]      - 打印当前倾斜角度")
                    print("  [S]      - 保存当前target2cam矩阵")
                    print("  [P]      - 设置相机参数")
                    print("  [Q] / [ESC] - 退出")
                    print("="*50 + "\n")
                elif key == ord('t'):
                    self.print_tilt_info()
                elif key == ord('s') and detected:
                    # 保存target2cam
                    T = np.eye(4)
                    R, _ = cv2.Rodrigues(rvec)
                    T[:3, :3] = R
                    T[:3, 3] = tvec.flatten()
                    timestamp = cv2.getTickCount()
                    filename = f"target2cam_{timestamp}.txt"
                    np.savetxt(filename, T, fmt='%.8f')
                    print(f"已保存到: {filename}")
                elif key == ord('p'):
                    self._set_camera_params_interactive()

        except KeyboardInterrupt:
            print("\n程序被中断")
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.camera.close()
            cv2.destroyAllWindows()
            print("\n程序结束")

    def _set_camera_params_interactive(self):
        """交互式设置相机参数"""
        print("\n请输入相机内参矩阵（3x3）:")
        camera_matrix = np.zeros((3, 3), dtype=np.float32)
        for i in range(3):
            row = input(f"第 {i+1} 行 (用空格分隔3个值): ")
            camera_matrix[i] = [float(x) for x in row.split()]

        print("\n请输入畸变系数（5个值，用空格分隔）:")
        dist = input("k1, k2, p1, p2, k3: ")
        dist_coeffs = np.array([float(x) for x in dist.split()], dtype=np.float32).reshape(5, 1)

        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        print(f"相机参数已设置")


def main():
    """主函数"""
    monitor = ParallelMonitor(camera_id=0, chessboard_size=(9, 9), square_size=18.0)

    # 尝试加载相机参数（如果存在）
    import os
    if os.path.exists("camera_calibration_results/camera_params.py"):
        monitor.load_calibration("camera_calibration_results/camera_params.py")

    # 运行监控
    monitor.run()


if __name__ == "__main__":
    main()
