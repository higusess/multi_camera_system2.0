"""
棋盘格检测模块
负责检测棋盘格角点，计算目标位姿
"""
import cv2
import numpy as np


class ChessboardDetector:
    def __init__(self, pattern_size=(9, 9), square_size=18.0):
        """
        初始化棋盘格检测器

        Args:
            pattern_size: 棋盘格内角点数量 (cols, rows)
            square_size: 每个格子的物理尺寸(mm)
        """
        self.pattern_size = pattern_size  # (cols, rows)
        self.square_size = square_size
        self._prepare_object_points()

    def _prepare_object_points(self):
        """准备棋盘格的世界坐标系点集（目标坐标系）"""
        cols, rows = self.pattern_size

        # 生成棋盘格角点的3D坐标（假设棋盘格在Z=0平面）
        # 顺序：从左到右，从上到下
        self.object_points = np.zeros((rows * cols, 3), dtype=np.float32)
        self.object_points[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
        self.object_points *= self.square_size

    def detect(self, image):
        """
        检测棋盘格角点

        Args:
            image: 输入图像

        Returns:
            tuple: (image_with_corners, corners, success)
                - image_with_corners: 带角点标记的图像
                - corners: 检测到的角点坐标
                - success: 是否成功检测
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 亚像素级别的角点检测
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        # 检测棋盘格角点
        ret, corners = cv2.findChessboardCorners(
            gray, self.pattern_size, None,
            flags=cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE
        )

        if ret:
            # 亚像素精度优化
            corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

            # 绘制角点
            display_image = image.copy()
            cv2.drawChessboardCorners(display_image, self.pattern_size, corners, ret)
            return display_image, corners, True
        else:
            return image, None, False

    def solve_pnp(self, corners, camera_matrix, dist_coeffs):
        """
        使用SolvePnP计算目标到相机的位姿变换

        Args:
            corners: 检测到的角点坐标
            camera_matrix: 相机内参矩阵
            dist_coeffs: 畸变系数

        Returns:
            tuple: (success, rvec, tvec)
                - success: 是否成功求解
                - rvec: 旋转向量
                - tvec: 平移向量
        """
        if corners is None:
            return False, None, None

        success, rvec, tvec = cv2.solvePnP(
            self.object_points, corners,
            camera_matrix, dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )

        return success, rvec, tvec

    def rotation_vector_to_angles(self, rvec):
        """
        将旋转向量转换为欧拉角（度）

        Args:
            rvec: 旋转向量

        Returns:
            tuple: (rx, ry, rz) 欧拉角（度）
        """
        R, _ = cv2.Rodrigues(rvec)

        # 使用ZYX欧拉角顺序（roll, pitch, yaw）
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

        return np.degrees(rx), np.degrees(ry), np.degrees(rz)

    def get_camera_table_tilt(self, rvec):
        """
        计算相机与桌面的夹角

        target2cam的旋转矩阵R表示从目标(桌面)坐标系到相机坐标系的旋转
        当相机平行于桌面时，相机的Z轴应该垂直于桌面
        即：相机的Z轴与桌面的法向量(0,0,1)的夹角应该为90度

        更直观的理解：
        - R矩阵的列向量是相机坐标系的轴在目标(桌面)坐标系中的表示
        - 第1列是相机X轴在桌面坐标系中的方向
        - 第2列是相机Y轴在桌面坐标系中的方向
        - 第3列是相机Z轴在桌面坐标系中的方向

        当相机平行于桌面时，相机Z轴应该垂直于桌面，即R[:,2] ≈ [0,0,1]或[0,0,-1]
        这意味着 rx ≈ 0°, ry ≈ 0°

        Args:
            rvec: 旋转向量 (target to cam)

        Returns:
            dict: {
                'tilt_x_deg': 绕X轴的倾斜角度（度），
                'tilt_y_deg': 绕Y轴的倾斜角度（度），
                'tilt_angle_deg': 总倾斜角度（度），
                'is_parallel': 是否平行（偏差小于2度）
            }
        """
        R, _ = cv2.Rodrigues(rvec)

        # 相机Z轴在桌面坐标系中的方向
        # R[:,2] = [R[0,2], R[1,2], R[2,2]]
        cam_z_in_table = R[:, 2]

        # 计算相机Z轴与桌面法向量(0,0,1)的夹角
        # 点积: dot(a,b) = |a||b|cos(theta)
        # 单位向量的点积就是cos(theta)
        table_normal = np.array([0, 0, 1], dtype=np.float64)
        cos_angle = np.dot(cam_z_in_table, table_normal)

        # 防止数值误差
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle_from_normal = np.degrees(np.arccos(np.abs(cos_angle)))

        # 角度从法向量就是相机Z轴偏离桌面法向量的角度
        # 当相机平行桌面时，这个角度应该是0度
        tilt_angle = angle_from_normal

        # 计算绕X轴和Y轴的倾斜角度
        # 这些角度就是欧拉角的rx和ry
        rx, ry, rz = self.rotation_vector_to_angles(rvec)

        # 判断是否平行（偏差小于2度）
        is_parallel = (abs(rx) < 2.0) and (abs(ry) < 2.0)

        return {
            'tilt_x_deg': rx,
            'tilt_y_deg': ry,
            'tilt_angle_deg': tilt_angle,
            'is_parallel': is_parallel
        }

    def calculate_correction_angles(self, current_rvec, cam2gripper_matrix=None):
        """
        计算使相机平行桌面需要调整的机械臂角度

        Args:
            current_rvec: 当前target2cam的旋转向量
            cam2gripper_matrix: 相机到机械臂末端的变换矩阵 (4x4)，如果已标定

        Returns:
            dict: {
                'current_tilt_x_deg': 当前绕X轴倾斜，
                'current_tilt_y_deg': 当前绕Y轴倾斜，
                'required_adjustment_x_deg': 需要调整的X轴角度，
                'required_adjustment_y_deg': 需要调整的Y轴角度，
                'adjustment_needed': 是否需要调整
            }
        """
        tilt_info = self.get_camera_table_tilt(current_rvec)

        # 要使相机平行桌面，需要反向调整机械臂姿态
        # 如果当前相机绕X轴倾斜了rx度，机械臂需要反向调整rx度
        # 如果有cam2gripper矩阵，可以计算更精确的调整

        rx = tilt_info['tilt_x_deg']
        ry = tilt_info['tilt_y_deg']

        # 需要的调整角度（反向）
        adjustment_x = -rx
        adjustment_y = -ry

        # 如果有cam2gripper矩阵，可以应用更复杂的转换
        if cam2gripper_matrix is not None:
            R_c2g = cam2gripper_matrix[:3, :3]
            # 这里可以添加更精确的转换逻辑
            # 简单情况下，直接使用反向角度即可

        return {
            'current_tilt_x_deg': rx,
            'current_tilt_y_deg': ry,
            'required_adjustment_x_deg': adjustment_x,
            'required_adjustment_y_deg': adjustment_y,
            'adjustment_needed': (abs(rx) > 2.0) or (abs(ry) > 2.0)
        }

    def rotation_matrix_to_euler(self, R_matrix):
        """
        将旋转矩阵转换为欧拉角（度）

        Args:
            R_matrix: 旋转矩阵 (3x3)

        Returns:
            tuple: (rx, ry, rz) 欧拉角（度）
        """
        sy = np.sqrt(R_matrix[0, 0] ** 2 + R_matrix[1, 0] ** 2)
        singular = sy < 1e-6

        if not singular:
            rx = np.arctan2(R_matrix[2, 1], R_matrix[2, 2])
            ry = np.arctan2(-R_matrix[2, 0], sy)
            rz = np.arctan2(R_matrix[1, 0], R_matrix[0, 0])
        else:
            rx = np.arctan2(-R_matrix[1, 2], R_matrix[1, 1])
            ry = np.arctan2(-R_matrix[2, 0], sy)
            rz = 0

        return np.degrees(rx), np.degrees(ry), np.degrees(rz)
