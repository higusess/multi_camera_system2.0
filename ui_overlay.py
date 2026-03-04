"""
UI显示模块
负责在画面上绘制标定状态和信息
"""
import cv2
import numpy as np


class UIOverlay:
    def __init__(self):
        """初始化UI覆盖层"""
        self.colors = {
            'success': (0, 255, 0),
            'warning': (0, 255, 255),
            'error': (0, 0, 255),
            'info': (255, 255, 255),
            'bg': (0, 0, 0)
        }

    def draw_info_panel(self, image, info_dict):
        """
        绘制信息面板

        Args:
            image: 输入图像
            info_dict: 信息字典 {label: value}
        """
        panel_height = 220
        panel_width = 380
        y_start = 10

        # 绘制半透明背景
        overlay = image.copy()
        cv2.rectangle(overlay, (10, y_start),
                     (10 + panel_width, y_start + panel_height),
                     (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)

        # 绘制信息
        y = y_start + 30
        for label, value in info_dict.items():
            color = self.colors['info']
            if '角度' in label or 'Angle' in label:
                if isinstance(value, (int, float)):
                    color = self.colors['success'] if abs(value) < 90 else self.colors['warning']

            text = f"{label}: {value}"
            cv2.putText(image, text, (20, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            y += 25

    def draw_angles_display(self, image, angles, position='top_right'):
        """
        绘制角度显示区域

        Args:
            image: 输入图像
            angles: 角度字典 {'rx': value, 'ry': value, 'rz': value}
            position: 位置 'top_right', 'top_left', 'bottom_right', 'bottom_left'
        """
        h, w = image.shape[:2]

        # 确定位置
        if position == 'top_right':
            x_start, y_start = w - 280, 10
        elif position == 'top_left':
            x_start, y_start = 10, 250
        elif position == 'bottom_right':
            x_start, y_start = w - 280, h - 120
        else:  # bottom_left
            x_start, y_start = 10, h - 120

        # 绘制背景
        overlay = image.copy()
        cv2.rectangle(overlay, (x_start, y_start),
                     (x_start + 270, y_start + 100),
                     (0, 50, 0), -1)
        cv2.addWeighted(overlay, 0.8, image, 0.2, 0, image)

        # 绘制边框
        cv2.rectangle(image, (x_start, y_start),
                     (x_start + 270, y_start + 100),
                     (0, 255, 0), 2)

        # 标题
        cv2.putText(image, "Target to Cam Angles", (x_start + 10, y_start + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # 角度值
        y = y_start + 55
        angle_labels = {'rx': 'Rx (°)', 'ry': 'Ry (°)', 'rz': 'Rz (°)'}

        for key, label in angle_labels.items():
            if key in angles:
                value = angles[key]
                color = (0, 255, 0)
                # 根据角度大小改变颜色
                if abs(value) > 90:
                    color = (0, 165, 255)  # 橙色
                elif abs(value) > 45:
                    color = (0, 255, 255)  # 黄色

                text = f"{label}: {value:.2f}"
                cv2.putText(image, text, (x_start + 10, y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                y += 20

    def draw_status_bar(self, image, status_text, color=None):
        """
        绘制状态栏

        Args:
            image: 输入图像
            status_text: 状态文本
            color: 文本颜色
        """
        if color is None:
            color = self.colors['info']

        h, w = image.shape[:2]
        y = h - 30

        # 背景条
        overlay = image.copy()
        cv2.rectangle(overlay, (0, y), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.8, image, 0.2, 0, image)

        # 状态文本
        cv2.putText(image, status_text, (10, h - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    def draw_calibration_progress(self, image, current, target=10):
        """
        绘制标定进度条

        Args:
            image: 输入图像
            current: 当前数量
            target: 目标数量
        """
        h, w = image.shape[:2]
        bar_width = 300
        bar_height = 20
        x = (w - bar_width) // 2
        y = h - 60

        # 进度条背景
        cv2.rectangle(image, (x, y), (x + bar_width, y + bar_height),
                     (100, 100, 100), -1)

        # 进度条填充
        progress = min(current / target, 1.0)
        fill_width = int(bar_width * progress)
        fill_color = (0, 255, 0) if progress >= 1.0 else (0, 255, 255)
        cv2.rectangle(image, (x, y), (x + fill_width, y + bar_height),
                     fill_color, -1)

        # 边框
        cv2.rectangle(image, (x, y), (x + bar_width, y + bar_height),
                     (255, 255, 255), 2)

        # 文本
        text = f"标定进度: {current}/{target}"
        cv2.putText(image, text, (x, y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    def draw_axis(self, image, rvec, tvec, camera_matrix, dist_coeffs, length=50):
        """
        在图像上绘制3D坐标轴

        Args:
            image: 输入图像
            rvec: 旋转向量
            tvec: 平移向量
            camera_matrix: 相机内参
            dist_coeffs: 畸变系数
            length: 轴长度
        """
        # 定义坐标轴点
        axis_points = np.array([
            [0, 0, 0],
            [length, 0, 0],  # X轴 - 红色
            [0, length, 0],  # Y轴 - 绿色
            [0, 0, length]   # Z轴 - 蓝色
        ], dtype=np.float32)

        # 投影到图像平面
        image_points, _ = cv2.projectPoints(
            axis_points, rvec, tvec,
            camera_matrix, dist_coeffs
        )
        image_points = image_points.reshape(-1, 2)

        origin = tuple(image_points[0].astype(int))

        # 绘制轴线
        colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]  # BGR: X=红, Y=绿, Z=蓝
        labels = ['X', 'Y', 'Z']

        for i in range(3):
            point = tuple(image_points[i + 1].astype(int))
            cv2.line(image, origin, point, colors[i], 3)
            cv2.putText(image, labels[i], point,
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[i], 2)

        return image

    def draw_tilt_indicator(self, image, tilt_info, correction_info=None):
        """
        绘制相机倾斜指示器

        Args:
            image: 输入图像
            tilt_info: 倾斜信息字典
            correction_info: 校正信息字典（可选）
        """
        h, w = image.shape[:2]

        # 左下角位置
        panel_width = 300
        panel_height = 150
        x_start = 10
        y_start = h - 200

        # 绘制背景
        overlay = image.copy()
        cv2.rectangle(overlay, (x_start, y_start),
                     (x_start + panel_width, y_start + panel_height),
                     (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.8, image, 0.2, 0, image)

        # 根据是否平行设置边框颜色
        border_color = self.colors['success'] if tilt_info.get('is_parallel', False) else self.colors['error']
        cv2.rectangle(image, (x_start, y_start),
                     (x_start + panel_width, y_start + panel_height),
                     border_color, 3)

        # 标题
        status_text = "相机状态: 平行" if tilt_info.get('is_parallel', False) else "相机状态: 倾斜"
        cv2.putText(image, status_text, (x_start + 10, y_start + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, border_color, 2)

        # 倾斜角度显示
        y = y_start + 55
        cv2.putText(image, f"倾斜 X: {tilt_info['tilt_x_deg']:.2f}°",
                   (x_start + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        y += 25
        cv2.putText(image, f"倾斜 Y: {tilt_info['tilt_y_deg']:.2f}°",
                   (x_start + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

        # 总倾斜角度
        y += 25
        total_tilt = tilt_info.get('tilt_angle_deg', 0)
        tilt_color = self.colors['success'] if total_tilt < 2 else (self.colors['warning'] if total_tilt < 5 else self.colors['error'])
        cv2.putText(image, f"总倾斜: {total_tilt:.2f}°",
                   (x_start + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, tilt_color, 2)

        # 如果需要调整，显示调整建议
        if correction_info and correction_info.get('adjustment_needed', False):
            y += 30
            adj_x = correction_info['required_adjustment_x_deg']
            adj_y = correction_info['required_adjustment_y_deg']
            cv2.putText(image, f"调整: X {adj_x:.1f}°, Y {adj_y:.1f}°",
                       (x_start + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

    def draw_level_indicator(self, image, tilt_x, tilt_y):
        """
        绘制水平仪样式指示器（直观显示倾斜方向）

        Args:
            image: 输入图像
            tilt_x: X轴倾斜角度
            tilt_y: Y轴倾斜角度
        """
        h, w = image.shape[:2]

        # 右下角位置
        center_x = w - 80
        center_y = h - 80
        radius = 60

        # 绘制圆形背景
        cv2.circle(image, (center_x, center_y), radius, (50, 50, 50), -1)
        cv2.circle(image, (center_x, center_y), radius, (200, 200, 200), 2)

        # 绘制十字参考线
        cv2.line(image, (center_x - radius + 5, center_y), (center_x + radius - 5, center_y), (150, 150, 150), 1)
        cv2.line(image, (center_x, center_y - radius + 5), (center_x, center_y + radius - 5), (150, 150, 150), 1)

        # 计算气泡位置（反向）
        # 当相机向右倾斜时，气泡向左移动
        scale = 2.0  # 缩放因子，使倾斜更明显
        bubble_x = center_x - tilt_x * scale
        bubble_y = center_y + tilt_y * scale

        # 限制气泡在圆内
        dx = bubble_x - center_x
        dy = bubble_y - center_y
        dist = np.sqrt(dx*dx + dy*dy)
        max_dist = radius - 15

        if dist > max_dist:
            bubble_x = center_x + dx / dist * max_dist
            bubble_y = center_y + dy / dist * max_dist

        # 绘制气泡
        bubble_radius = 12
        cv2.circle(image, (int(bubble_x), int(bubble_y)), bubble_radius, (0, 200, 255), -1)
        cv2.circle(image, (int(bubble_x), int(bubble_y)), bubble_radius, (255, 255, 255), 2)

        # 绘制中心点
        cv2.circle(image, (center_x, center_y), 3, (255, 0, 0), -1)

        # 标签
        cv2.putText(image, "LEVEL", (center_x - 20, center_y - radius - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
