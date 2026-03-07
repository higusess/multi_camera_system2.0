"""
手眼标定主程序
Eye-in-Hand 手眼标定：相机安装在机械臂末端
"""
import cv2
import numpy as np
from camera_handler import CameraHandler
from chessboard_detector import ChessboardDetector
from hand_eye_calibrator import HandEyeCalibrator
from ui_overlay import UIOverlay


class HandEyeCalibrationApp:
    def __init__(self, camera_id=0, chessboard_size=(9, 9), square_size=18.0):
        """
        初始化手眼标定应用

        Args:
            camera_id: 相机ID
            chessboard_size: 棋盘格内角点数量 (cols, rows)
            square_size: 每个格子的物理尺寸(mm)
        """
        # 初始化各模块
        self.camera = CameraHandler(camera_id)
        self.detector = ChessboardDetector(chessboard_size, square_size)
        self.calibrator = HandEyeCalibrator()
        self.ui = UIOverlay()

        # 状态
        self.is_running = False
        self.current_rvec = None
        self.current_tvec = None
        self.chessboard_detected = False
        self.current_tilt_info = None
        self.current_correction_info = None

        # 相机参数（需要先标定相机）
        # 如果没有标定相机，可以使用这些默认值作为示例
        # 实际使用时请先标定相机内参
        self.camera_matrix = np.array([
            [1000, 0, 640],
            [0, 1000, 360],
            [0, 0, 1]
        ], dtype=np.float32)

        self.dist_coeffs = np.zeros((5, 1), dtype=np.float32)

    def set_camera_params(self, camera_matrix, dist_coeffs):
        """
        设置相机参数

        Args:
            camera_matrix: 相机内参矩阵 (3x3)
            dist_coeffs: 畸变系数 (1x5)
        """
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        self.calibrator.set_camera_params(camera_matrix, dist_coeffs)
        print("相机参数已设置")

    def input_gripper_pose(self):
        """
        用户输入机械臂末端位姿

        Returns:
            tuple: (x, y, z, rx, ry, rz) 单位: mm, 度
        """
        print("\n" + "="*50)
        print("请输入机械臂末端位姿（相对于基座）")
        print("单位: x, y, z (mm), rx, ry, rz (度)")
        print("="*50)

        try:
            x = float(input("请输入 x (mm): "))
            y = float(input("请输入 y (mm): "))
            z = float(input("请输入 z (mm): "))
            rx = float(input("请输入 rx (度): "))
            ry = float(input("请输入 ry (度): "))
            rz = float(input("请输入 rz (度): "))
            return (x, y, z, rx, ry, rz)
        except ValueError as e:
            print(f"输入错误: {e}")
            return None

    def add_calibration_sample(self):
        """添加一个标定样本"""
        if not self.chessboard_detected:
            print("未检测到棋盘格，请调整相机位置")
            return False

        # 输入机械臂位姿
        gripper_pose = self.input_gripper_pose()
        if gripper_pose is None:
            return False

        # 添加到标定器
        target_pose = (self.current_rvec, self.current_tvec)
        self.calibrator.add_data(gripper_pose, target_pose)

        count = self.calibrator.get_data_count()
        print(f"已收集 {count} 个标定样本")
        return True

    def run_calibration(self):
        """执行手眼标定"""
        count = self.calibrator.get_data_count()
        if count < 3:
            print(f"当前只有 {count} 个样本，至少需要 3 个样本才能标定")
            return

        print("\n开始标定...")
        try:
            R, t = self.calibrator.calibrate()
            print("\n标定成功！")
            print(f"R_cam2gripper:\n{R}")
            print(f"t_cam2gripper (mm):\n{t.T}")

            # 转换为欧拉角
            calibrator = self.calibrator
            rx, ry, rz = calibrator.rotation_matrix_to_euler(R)
            print(f"\n欧拉角 (度): Rx={rx:.4f}, Ry={ry:.4f}, Rz={rz:.4f}")
            print(f"平移 (mm): Tx={t[0,0]:.4f}, Ty={t[1,0]:.4f}, Tz={t[2,0]:.4f}")

            # 保存结果
            self.calibrator.save_results()

        except Exception as e:
            print(f"标定失败: {e}")

    def print_tilt_info(self):
        """打印当前倾斜信息到控制台"""
        if self.current_tilt_info is None:
            print("\n未检测到棋盘格，无法计算倾斜")
            return

        print("\n" + "="*50)
        print("相机与桌面夹角")
        print("="*50)
        tilt = self.current_tilt_info
        print(f"X轴倾斜 (绕X轴): {tilt['tilt_x_deg']:.4f}°")
        print(f"Y轴倾斜 (绕Y轴): {tilt['tilt_y_deg']:.4f}°")
        print(f"总倾斜角度: {tilt['tilt_angle_deg']:.4f}°")
        print(f"状态: {'平行' if tilt['is_parallel'] else '倾斜'}")

        if self.current_correction_info:
            corr = self.current_correction_info
            if corr['adjustment_needed']:
                print("\n需要调整机械臂姿态:")
                print(f"  调整Rx: {corr['required_adjustment_x_deg']:.2f}°")
                print(f"  调整Ry: {corr['required_adjustment_y_deg']:.2f}°")
            else:
                print("\n相机已平行桌面，无需调整")

        print("="*50 + "\n")

    def save_current_target2cam(self):
        """保存当前的target2cam矩阵"""
        if not self.chessboard_detected:
            print("未检测到棋盘格")
            return

        T = self.calibrator.get_target2cam_matrix()
        if T is not None:
            timestamp = cv2.getTickCount()
            filename = f"target2cam_{timestamp}.txt"
            np.savetxt(filename, T, fmt='%.8f')
            print(f"当前target2cam矩阵已保存到: {filename}")
            print(T)

    def print_help(self):
        """打印帮助信息"""
        print("\n" + "="*50)
        print("手眼标定程序 - Eye-in-Hand")
        print("目标: 使相机始终平行于桌面")
        print("="*50)
        print("按键说明:")
        print("  [SPACE]  - 添加标定样本（输入机械臂位姿）")
        print("  [C]      - 执行标定计算")
        print("  [S]      - 保存当前target2cam矩阵")
        print("  [T]      - 打印当前倾斜角度（控制台）")
        print("  [R]      - 清除所有数据")
        print("  [P]      - 设置相机参数")
        print("  [H]      - 显示帮助")
        print("  [Q] / [ESC] - 退出程序")
        print("="*50)
        print("画面说明:")
        print("  - 左下角: 相机倾斜状态和角度")
        print("  - 右下角: 水平仪（气泡显示）")
        print("  - 右上角: Target2Cam 角度值")
        print("="*50 + "\n")

    def set_camera_params_interactive(self):
        """交互式设置相机参数"""
        print("\n请输入相机内参矩阵（3x3）:")
        camera_matrix = np.zeros((3, 3), dtype=np.float32)
        for i in range(3):
            row = input(f"第 {i+1} 行 (用空格分隔3个值): ")
            camera_matrix[i] = [float(x) for x in row.split()]

        print("\n请输入畸变系数（5个值，用空格分隔）:")
        dist = input("k1, k2, p1, p2, k3: ")
        dist_coeffs = np.array([float(x) for x in dist.split()], dtype=np.float32).reshape(5, 1)

        self.set_camera_params(camera_matrix, dist_coeffs)
        print(f"相机内参:\n{camera_matrix}")
        print(f"畸变系数:\n{dist_coeffs.T}")

    def run(self):
        """运行主程序"""
        print_help_called = False

        try:
            # 打开相机
            if not self.camera.open():
                print("无法打开相机")
                return

            self.is_running = True
            print("相机已打开，开始标定...")

            while self.is_running:
                # 读取图像
                frame = self.camera.read_frame()
                if frame is None:
                    continue

                # 检测棋盘格
                display_frame, corners, detected = self.detector.detect(frame)
                self.chessboard_detected = detected

                # 准备信息显示
                info_dict = {
                    '状态': '已检测棋盘格' if detected else '未检测到棋盘格',
                    '样本数量': self.calibrator.get_data_count()
                }

                # 如果检测到棋盘格，计算位姿
                if detected:
                    success, rvec, tvec = self.detector.solve_pnp(
                        corners, self.camera_matrix, self.dist_coeffs
                    )

                    if success:
                        self.current_rvec = rvec
                        self.current_tvec = tvec

                        # 转换为欧拉角
                        rx, ry, rz = self.detector.rotation_vector_to_angles(rvec)

                        # 计算相机与桌面的夹角
                        self.current_tilt_info = self.detector.get_camera_table_tilt(rvec)

                        # 计算需要调整的角度（如果已标定）
                        if self.calibrator.calibration_done:
                            cam2gripper_matrix = np.eye(4)
                            cam2gripper_matrix[:3, :3] = self.calibrator.R_cam2gripper
                            cam2gripper_matrix[:3, 3] = self.calibrator.t_cam2gripper.flatten()
                            self.current_correction_info = self.detector.calculate_correction_angles(
                                rvec, cam2gripper_matrix
                            )
                        else:
                            self.current_correction_info = self.detector.calculate_correction_angles(rvec)

                        # 更新信息
                        info_dict.update({
                            '位置 X (mm)': f"{tvec[0, 0]:.2f}",
                            '位置 Y (mm)': f"{tvec[1, 0]:.2f}",
                            '位置 Z (mm)': f"{tvec[2, 0]:.2f}"
                        })

                        # 绘制角度显示
                        angles_dict = {'rx': rx, 'ry': ry, 'rz': rz}
                        self.ui.draw_angles_display(display_frame, angles_dict, 'top_right')

                        # 绘制倾斜指示器
                        self.ui.draw_tilt_indicator(display_frame, self.current_tilt_info,
                                                 self.current_correction_info)

                        # 绘制水平仪
                        self.ui.draw_level_indicator(display_frame,
                                                   self.current_tilt_info['tilt_x_deg'],
                                                   self.current_tilt_info['tilt_y_deg'])

                        # 绘制坐标轴
                        self.ui.draw_axis(display_frame, rvec, tvec,
                                        self.camera_matrix, self.dist_coeffs)

                # 绘制信息面板
                self.ui.draw_info_panel(display_frame, info_dict)

                # 绘制进度条
                self.ui.draw_calibration_progress(display_frame,
                                                 self.calibrator.get_data_count(),
                                                 target=10)

                # 状态栏
                status = "按[H]查看帮助"
                self.ui.draw_status_bar(display_frame, status)

                # 显示图像
                cv2.imshow('Hand Eye Calibration', display_frame)

                # 按键处理
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q') or key == 27:  # q or ESC
                    self.is_running = False
                elif key == ord('h'):
                    self.print_help()
                    print_help_called = True
                elif key == ord(' ') and detected:  # Space
                    self.add_calibration_sample()
                elif key == ord('c'):
                    self.run_calibration()
                elif key == ord('s'):
                    self.save_current_target2cam()
                elif key == ord('t'):
                    self.print_tilt_info()
                elif key == ord('r'):
                    self.calibrator.clear_data()
                    print("已清除所有标定数据")
                elif key == ord('p'):
                    self.set_camera_params_interactive()

                # 首次运行显示帮助
                if not print_help_called:
                    self.print_help()
                    print_help_called = True

        except KeyboardInterrupt:
            print("\n程序被中断")
        except Exception as e:
            print(f"错误: {e}")
        finally:
            self.camera.close()
            cv2.destroyAllWindows()
            print("程序结束")


def main():
    """主函数"""
    # 创建应用实例
    # 可以修改参数：camera_id, chessboard_size=(9, 9), square_size=18.0
    app = HandEyeCalibrationApp(camera_id=0, chessboard_size=(9, 9), square_size=18.0)

    # 如果有标定好的相机参数，可以在这里设置
    # camera_matrix = np.array([...])
    # dist_coeffs = np.array([...])
    # app.set_camera_params(camera_matrix, dist_coeffs)

    # 运行程序
    app.run()


if __name__ == "__main__":
    main()
