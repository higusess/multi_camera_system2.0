"""
相机内参标定辅助程序
用于标定相机的内参矩阵和畸变系数
"""
import cv2
import numpy as np
from pathlib import Path


class CameraCalibrationHelper:
    def __init__(self, pattern_size=(9, 9), square_size=18.0):
        """
        初始化相机标定助手

        Args:
            pattern_size: 棋盘格内角点数量 (cols, rows)
            square_size: 每个格子的物理尺寸 (mm)
        """
        self.pattern_size = pattern_size
        self.square_size = square_size
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        # 准备物体点
        self._prepare_object_points()

        # 存储标定数据
        self.obj_points = []
        self.img_points = []

        # 图像尺寸
        self.img_size = None

    def _prepare_object_points(self):
        """准备棋盘格的3D坐标"""
        cols, rows = self.pattern_size
        self.objp = np.zeros((rows * cols, 3), dtype=np.float32)
        self.objp[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
        self.objp *= self.square_size

    def detect_chessboard(self, frame):
        """
        检测棋盘格角点

        Args:
            frame: 输入图像

        Returns:
            tuple: (display_frame, corners, success)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        ret, corners = cv2.findChessboardCorners(
            gray, self.pattern_size, None,
            flags=cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE
        )

        if ret:
            corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)

        display_frame = frame.copy()
        if ret:
            cv2.drawChessboardCorners(display_frame, self.pattern_size, corners, ret)

        return display_frame, corners, ret

    def add_calibration_frame(self, frame, corners):
        """
        添加一帧用于标定的数据

        Args:
            frame: 输入图像
            corners: 检测到的角点
        """
        if self.img_size is None:
            self.img_size = frame.shape[:2][::-1]  # (width, height)

        self.obj_points.append(self.objp)
        self.img_points.append(corners)

    def calibrate(self):
        """
        执行相机标定

        Returns:
            tuple: (camera_matrix, dist_coeffs, rvecs, tvecs, mean_error)
        """
        if len(self.obj_points) == 0:
            raise ValueError("没有足够的标定数据")

        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            self.obj_points, self.img_points, self.img_size, None, None
        )

        if not ret:
            raise RuntimeError("相机标定失败")

        # 计算重投影误差
        mean_error = self._compute_reprojection_error(
            camera_matrix, dist_coeffs, rvecs, tvecs
        )

        return camera_matrix, dist_coeffs, rvecs, tvecs, mean_error

    def _compute_reprojection_error(self, camera_matrix, dist_coeffs, rvecs, tvecs):
        """计算重投影误差"""
        total_error = 0
        for i in range(len(self.obj_points)):
            img_points_reproj, _ = cv2.projectPoints(
                self.obj_points[i], rvecs[i], tvecs[i],
                camera_matrix, dist_coeffs
            )
            error = cv2.norm(self.img_points[i], img_points_reproj, cv2.NORM_L2) / len(img_points_reproj)
            total_error += error
        return total_error / len(self.obj_points)

    def save_results(self, camera_matrix, dist_coeffs, save_path="camera_calibration_results"):
        """
        保存标定结果

        Args:
            camera_matrix: 相机内参矩阵
            dist_coeffs: 畸变系数
            save_path: 保存路径
        """
        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)

        # 保存为 Python 文件
        with open(save_path / "camera_params.py", 'w') as f:
            f.write("import numpy as np\n\n")
            f.write("# 相机内参矩阵\n")
            f.write("camera_matrix = np.array(\n")
            f.write(str(camera_matrix.tolist()).replace("], [", "],\n    ["))
            f.write(",\n    dtype=np.float32)\n\n")
            f.write("# 畸变系数 (k1, k2, p1, p2, k3)\n")
            f.write("dist_coeffs = np.array(\n")
            f.write(str(dist_coeffs.tolist()).replace("], [", "],\n    ["))
            f.write(",\n    dtype=np.float32)\n")

        print(f"相机参数已保存到: {save_path / 'camera_params.py'}")

    def clear(self):
        """清除所有标定数据"""
        self.obj_points = []
        self.img_points = []
        self.img_size = None


def main():
    """相机内参标定主程序"""
    print("="*50)
    print("相机内参标定程序")
    print("="*50)

    # 创建标定助手
    helper = CameraCalibrationHelper(pattern_size=(9, 9), square_size=18.0)

    # 打开相机
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("无法打开相机")
        return

    print("\n操作说明:")
    print("  [SPACE] - 添加当前帧到标定数据")
    print("  [C]     - 执行标定")
    print("  [R]     - 清除所有数据")
    print("  [Q]     - 退出")

    count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # 检测棋盘格
        display_frame, corners, detected = helper.detect_chessboard(frame)

        # 显示计数
        cv2.putText(display_frame, f"Calibration frames: {count}",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 状态
        status = "Detected" if detected else "Not detected"
        color = (0, 255, 0) if detected else (0, 0, 255)
        cv2.putText(display_frame, status, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        cv2.imshow('Camera Calibration', display_frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q') or key == 27:
            break
        elif key == ord(' ') and detected:
            helper.add_calibration_frame(frame, corners)
            count += 1
            print(f"已添加 {count} 帧")
        elif key == ord('c'):
            if count >= 10:
                try:
                    camera_matrix, dist_coeffs, rvecs, tvecs, mean_error = helper.calibrate()
                    print(f"\n标定完成！重投影误差: {mean_error:.4f} 像素")
                    print(f"相机内参:\n{camera_matrix}")
                    print(f"畸变系数:\n{dist_coeffs.T}")
                    helper.save_results(camera_matrix, dist_coeffs)
                except Exception as e:
                    print(f"标定失败: {e}")
            else:
                print(f"需要至少10帧数据，当前只有{count}帧")
        elif key == ord('r'):
            helper.clear()
            count = 0
            print("数据已清除")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
