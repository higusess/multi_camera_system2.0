"""
手眼标定核心模块
负责收集数据、计算手眼矩阵、保存结果
"""
import cv2
import numpy as np
import pickle
from datetime import datetime
from pathlib import Path


class HandEyeCalibrator:
    def __init__(self, camera_matrix=None, dist_coeffs=None):
        """
        初始化手眼标定器

        Args:
            camera_matrix: 相机内参矩阵 (3x3)
            dist_coeffs: 畸变系数 (1x5)
        """
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs

        # 存储收集的数据
        self.R_gripper2base = []  # 机械臂末端相对于基座的旋转矩阵列表
        self.t_gripper2base = []  # 机械臂末端相对于基座的平移向量列表
        self.R_target2cam = []    # 目标相对于相机的旋转矩阵列表
        self.t_target2cam = []    # 目标相对于相机的平移向量列表

        # 手眼标定结果
        self.R_cam2gripper = None  # 相机相对于机械臂末端的旋转矩阵
        self.t_cam2gripper = None  # 相机相对于机械臂末端的平移向量
        self.calibration_done = False

    def set_camera_params(self, camera_matrix, dist_coeffs):
        """
        设置相机参数

        Args:
            camera_matrix: 相机内参矩阵
            dist_coeffs: 畸变系数
        """
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs

    def add_data(self, gripper_pose, target_pose):
        """
        添加一组标定数据

        Args:
            gripper_pose: 机械臂末端位姿 (x, y, z, rx, ry, rz) mm, degree
            target_pose: 目标相对于相机的位姿 (rvec, tvec)
        """
        x, y, z, rx, ry, rz = gripper_pose

        # 将机械臂姿态转换为旋转矩阵和平移向量
        R_gb = self.euler_to_rotation_matrix(rx, ry, rz)
        t_gb = np.array([x, y, z], dtype=np.float64).reshape(3, 1)

        # 将目标位姿从旋转向量转换为旋转矩阵
        rvec, tvec = target_pose
        R_tc, _ = cv2.Rodrigues(rvec)
        t_tc = tvec.reshape(3, 1)

        # 存储数据
        self.R_gripper2base.append(R_gb)
        self.t_gripper2base.append(t_gb)
        self.R_target2cam.append(R_tc)
        self.t_target2cam.append(t_tc)

    def euler_to_rotation_matrix(self, rx, ry, rz):
        """
        欧拉角转换为旋转矩阵（ZYX顺序）

        Args:
            rx, ry, rz: 欧拉角（度）

        Returns:
            旋转矩阵 (3x3)
        """
        rx, ry, rz = np.radians([rx, ry, rz])

        cx, sx = np.cos(rx), np.sin(rx)
        cy, sy = np.cos(ry), np.sin(ry)
        cz, sz = np.cos(rz), np.sin(rz)

        Rx = np.array([[1, 0, 0],
                       [0, cx, -sx],
                       [0, sx, cx]])
        Ry = np.array([[cy, 0, sy],
                       [0, 1, 0],
                       [-sy, 0, cy]])
        Rz = np.array([[cz, -sz, 0],
                       [sz, cz, 0],
                       [0, 0, 1]])

        # R = Rz * Ry * Rx (ZYX顺序)
        R = Rz @ Ry @ Rx
        return R

    def rotation_matrix_to_euler(self, R):
        """
        旋转矩阵转换为欧拉角（ZYX顺序）

        Args:
            R: 旋转矩阵 (3x3)

        Returns:
            (rx, ry, rz): 欧拉角（度）
        """
        sy = np.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)
        singular = sy < 1e-6

        if not singular:
            rx = np.arctan2(R[2, 1], R[2, 2])
            ry = np.arctan2(-R[2, 0], sy)
            rz = np.arctan2(R[1, 0], R[0, 0])
        else:
            rx = np.arctan2(-R[1, 2], R[1, 1])
            ry = np.arctan2(-R[2, 0], sy)
            rz = 0

        return np.degrees([rx, ry, rz])

    def calibrate(self, method=cv2.CALIB_HAND_EYE_TSAI):
        """
        执行手眼标定

        Args:
            method: 标定方法
                cv2.CALIB_HAND_EYE_TSAI
                cv2.CALIB_HAND_EYE_PARK
                cv2.CALIB_HAND_EYE_HORAUD
                cv2.CALIB_HAND_EYE_ANDREFF
                cv2.CALIB_HAND_EYE_DANIILIDIS

        Returns:
            tuple: (R_cam2gripper, t_cam2gripper)
        """
        if len(self.R_gripper2base) < 3:
            raise ValueError("至少需要3组数据才能进行标定")

        # Eye-in-hand标定：相机在机械臂末端
        # R_gripper2base * R_cam2gripper * R_target2cam = R_target2base
        # 我们需要求解 R_cam2gripper

        self.R_cam2gripper, self.t_cam2gripper = cv2.calibrateHandEye(
            self.R_gripper2base, self.t_gripper2base,
            self.R_target2cam, self.t_target2cam,
            method=method
        )

        self.calibration_done = True
        return self.R_cam2gripper, self.t_cam2gripper

    def get_target2cam_matrix(self):
        """
        获取当前最新的target2cam变换矩阵

        Returns:
            4x4 齐次变换矩阵
        """
        if not self.R_target2cam or not self.t_target2cam:
            return None

        R = self.R_target2cam[-1]
        t = self.t_target2cam[-1]

        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = t.flatten()
        return T

    def save_results(self, save_path=None):
        """
        保存标定结果

        Args:
            save_path: 保存路径，默认为程序目录下的calibration_results
        """
        if not self.calibration_done:
            raise RuntimeError("尚未完成标定")

        if save_path is None:
            save_path = Path(__file__).parent / "calibration_results"

        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)

        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存手眼矩阵
        result = {
            'R_cam2gripper': self.R_cam2gripper,
            't_cam2gripper': self.t_cam2gripper,
            'camera_matrix': self.camera_matrix,
            'dist_coeffs': self.dist_coeffs,
            'timestamp': timestamp,
            'num_samples': len(self.R_gripper2base)
        }

        result_file = save_path / f"hand_eye_calibration_{timestamp}.pkl"
        with open(result_file, 'wb') as f:
            pickle.dump(result, f)

        # 保存为可读的文本格式
        text_file = save_path / f"hand_eye_calibration_{timestamp}.txt"
        with open(text_file, 'w') as f:
            f.write(f"手眼标定结果\n")
            f.write(f"时间: {timestamp}\n")
            f.write(f"样本数量: {len(self.R_gripper2base)}\n\n")

            f.write("=== 相机到机械臂末端的变换 (cam2gripper) ===\n")
            f.write("\n旋转矩阵 R_cam2gripper:\n")
            np.savetxt(f, self.R_cam2gripper, fmt='%.8f')

            f.write("\n\n平移向量 t_cam2gripper (mm):\n")
            np.savetxt(f, self.t_cam2gripper.T, fmt='%.8f')

            f.write("\n\n=== 欧拉角表示 (度) ===\n")
            rx, ry, rz = self.rotation_matrix_to_euler(self.R_cam2gripper)
            f.write(f"Rx: {rx:.4f}°, Ry: {ry:.4f}°, Rz: {rz:.4f}°\n")
            f.write(f"Tx: {self.t_cam2gripper[0, 0]:.4f} mm\n")
            f.write(f"Ty: {self.t_cam2gripper[1, 0]:.4f} mm\n")
            f.write(f"Tz: {self.t_cam2gripper[2, 0]:.4f} mm\n")

            # 保存所有target2cam矩阵
            f.write("\n\n=== 所有 Target2Cam 矩阵 ===\n")
            for i, (R, t) in enumerate(zip(self.R_target2cam, self.t_target2cam)):
                f.write(f"\n--- 样本 {i+1} ---\n")
                T = np.eye(4)
                T[:3, :3] = R
                T[:3, 3] = t.flatten()
                np.savetxt(f, T, fmt='%.8f')

        print(f"标定结果已保存到: {result_file}")
        print(f"文本格式已保存到: {text_file}")

        return result_file, text_file

    def load_results(self, filepath):
        """
        加载之前的标定结果

        Args:
            filepath: 结果文件路径
        """
        with open(filepath, 'rb') as f:
            result = pickle.load(f)

        self.R_cam2gripper = result['R_cam2gripper']
        self.t_cam2gripper = result['t_cam2gripper']
        self.camera_matrix = result['camera_matrix']
        self.dist_coeffs = result['dist_coeffs']
        self.calibration_done = True

        return result

    def get_data_count(self):
        """返回已收集的数据数量"""
        return len(self.R_gripper2base)

    def clear_data(self):
        """清除所有已收集的数据"""
        self.R_gripper2base = []
        self.t_gripper2base = []
        self.R_target2cam = []
        self.t_target2cam = []
        self.calibration_done = False
        self.R_cam2gripper = None
        self.t_cam2gripper = None
