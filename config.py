"""
配置文件
包含相机参数、棋盘格参数等可配置项
"""
import numpy as np


# 棋盘格参数
CHESSBOARD_CONFIG = {
    'pattern_size': (9, 9),    # 内角点数量 (cols, rows)
    'square_size': 18.0,        # 每个格子的物理尺寸 (mm)
}

# 相机参数
# 注意：这些是示例值，实际使用前需要先标定相机内参
# 可以使用 OpenCV 的 calibrateCamera 函数进行相机标定
CAMERA_CONFIG = {
    'camera_id': 0,             # 相机ID
    'width': 1280,              # 图像宽度
    'height': 720,              # 图像高度

    # 相机内参矩阵 (3x3)
    'camera_matrix': np.array([
        [1000, 0, 640],
        [0, 1000, 360],
        [0, 0, 1]
    ], dtype=np.float32),

    # 畸变系数 (k1, k2, p1, p2, k3)
    'dist_coeffs': np.zeros((5, 1), dtype=np.float32),
}

# 标定参数
CALIBRATION_CONFIG = {
    'min_samples': 3,           # 最少样本数量
    'recommended_samples': 10,  # 推荐样本数量
    'calibration_method': 'TSAI',  # 标定方法: TSAI, PARK, HORAUD, ANDREFF, DANIILIDIS
}

# UI 配置
UI_CONFIG = {
    'window_name': 'Hand Eye Calibration',
    'show_axis': True,
    'show_angles': True,
}


def get_calibration_method_code(method_name):
    """
    获取标定方法的 OpenCV 代码

    Args:
        method_name: 方法名称

    Returns:
        OpenCV 标定方法代码
    """
    import cv2
    methods = {
        'TSAI': cv2.CALIB_HAND_EYE_TSAI,
        'PARK': cv2.CALIB_HAND_EYE_PARK,
        'HORAUD': cv2.CALIB_HAND_EYE_HORAUD,
        'ANDREFF': cv2.CALIB_HAND_EYE_ANDREFF,
        'DANIILIDIS': cv2.CALIB_HAND_EYE_DANIILIDIS,
    }
    return methods.get(method_name.upper(), cv2.CALIB_HAND_EYE_TSAI)
