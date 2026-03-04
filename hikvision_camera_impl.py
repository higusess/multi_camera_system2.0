"""
海康相机实现
Hikvision Camera Implementation

基于海康MVS SDK的相机控制实现
"""

import sys
import os
import cv2
import numpy as np
from ctypes import *
from typing import Optional
from camera_base import CameraBase

# ============ SDK路径配置 ============
MVS_SDK_PATH = r"C:\Program Files (x86)\MVS\Development\Samples\Python"
MVS_DLL_PATH = r"C:\Program Files (x86)\Common Files\MVS\Runtime\Win64_x64"

# 添加SDK路径到sys.path
if MVS_SDK_PATH not in sys.path:
    sys.path.insert(0, MVS_SDK_PATH)

# 添加MvImport路径
MV_IMPORT_PATH = os.path.join(MVS_SDK_PATH, "MvImport")
if MV_IMPORT_PATH not in sys.path:
    sys.path.insert(0, MV_IMPORT_PATH)

# 添加DLL路径到DLL搜索路径
if os.path.exists(MVS_DLL_PATH):
    try:
        os.add_dll_directory(MVS_DLL_PATH)
    except:
        pass

# ============ 导入MVS SDK ============
SDK_LOADED = False
MvCamera = None
try:
    # 方法1：尝试导入MvImport模块
    import MvImport.MvCameraControl_class as mvc_module
    MvCamera = mvc_module
    SDK_LOADED = True
    print("成功加载海康MVS SDK!")
except Exception as e:
    print(f"加载MVS SDK失败: {e}")
    SDK_LOADED = False


class HikvisionCamera(CameraBase):
    """海康相机实现类"""

    def __init__(self, device_type: str = "USB", device_index: int = 0):
        """
        初始化海康相机

        Args:
            device_type: 设备类型 ("USB" 或 "GigE")
            device_index: 设备索引
        """
        super().__init__(camera_name=f"Hikvision_{device_type}_{device_index}")
        self.device_type = device_type
        self.device_index = device_index
        self.camera = None
        self.device_list = None
        self.device_info = None
        self.current_params = {}

        # SDK初始化
        if SDK_LOADED:
            self.MvCamera = MvCamera
        else:
            self.MvCamera = None
            print(f"{self.camera_name}: SDK未加载")

    def enum_devices(self):
        """枚举海康相机设备"""
        if self.MvCamera is None:
            print(f"{self.camera_name}: SDK未加载")
            return None

        print(f"\n正在枚举海康相机设备...")

        device_list = self.MvCamera.MV_CC_DEVICE_INFO_LIST()

        # 根据设备类型选择枚举类型
        device_type_flag = 0
        if self.device_type == "USB":
            device_type_flag = self.MvCamera.MV_USB_DEVICE
        elif self.device_type == "GigE":
            device_type_flag = self.MvCamera.MV_GIGE_DEVICE
        else:
            device_type_flag = self.MvCamera.MV_GIGE_DEVICE | self.MvCamera.MV_USB_DEVICE

        ret = self.MvCamera.MvCamera.MV_CC_EnumDevices(device_type_flag, device_list)

        if ret != 0 or device_list.nDeviceNum == 0:
            print(f"{self.camera_name}: 未找到任何海康相机设备")
            return None

        self.device_list = device_list
        print(f"找到 {device_list.nDeviceNum} 个海康相机设备:")

        # 显示设备信息
        for i in range(device_list.nDeviceNum):
            device_info = cast(device_list.pDeviceInfo[i],
                             POINTER(self.MvCamera.MV_CC_DEVICE_INFO)).contents

            if device_info.nTLayerType == self.MvCamera.MV_GIGE_DEVICE:
                print(f"  设备 {i}: GigE相机")
            elif device_info.nTLayerType == self.MvCamera.MV_USB_DEVICE:
                print(f"  设备 {i}: USB相机")

        return device_list

    def open(self, device_index=0):
        """打开海康相机"""
        if self.MvCamera is None:
            print(f"{self.camera_name}: SDK未加载")
            return False

        print(f"\n正在打开海康相机 (索引: {device_index})...")

        if self.is_opened:
            print(f"{self.camera_name}: 相机已打开")
            return True

        if self.device_list is None:
            device_list = self.enum_devices()
            if device_list is None:
                return False
        else:
            device_list = self.device_list

        if device_index >= device_list.nDeviceNum:
            print(f"{self.camera_name}: 设备索引超出范围")
            return False

        device_info = cast(device_list.pDeviceInfo[device_index],
                         POINTER(self.MvCamera.MV_CC_DEVICE_INFO)).contents

        # 判断设备类型
        if self.device_type == "USB" and device_info.nTLayerType != self.MvCamera.MV_USB_DEVICE:
            print(f"{self.camera_name}: 警告: 这不是USB接口的相机")
        elif self.device_type == "GigE" and device_info.nTLayerType != self.MvCamera.MV_GIGE_DEVICE:
            print(f"{self.camera_name}: 警告: 这不是GigE接口的相机")

        self.device_info = device_info
        self.camera = self.MvCamera.MvCamera()

        ret = self.camera.MV_CC_CreateHandle(device_info)
        if ret != 0:
            print(f"{self.camera_name}: 创建句柄失败: 0x{ret:08x}")
            return False

        ret = self.camera.MV_CC_OpenDevice()
        # self.camera.MV_CC_SetImageNodeNum(1)
        if ret != 0:
            print(f"{self.camera_name}: 打开设备失败: 0x{ret:08x}")
            print("请确保相机未被其他程序占用")
            self.camera.MV_CC_DestroyHandle()
            return False

        # 读取基本参数
        self._read_basic_params()
        self.is_opened = True
        print(f"{self.camera_name}: 相机已打开!")
        print(f"  分辨率: {self.width}x{self.height}")
        print(f"  帧率: {self.fps:.1f} FPS")

        return True

    def _read_basic_params(self):
        """读取基本参数"""
        param = self.MvCamera.MVCC_INTVALUE()

        ret = self.camera.MV_CC_GetIntValue("PayloadSize", param)
        self.payload_size = param.nCurValue if ret == 0 else 0

        ret = self.camera.MV_CC_GetIntValue("Width", param)
        self.width = param.nCurValue if ret == 0 else 0

        ret = self.camera.MV_CC_GetIntValue("Height", param)
        self.height = param.nCurValue if ret == 0 else 0

        float_param = self.MvCamera.MVCC_FLOATVALUE()
        ret = self.camera.MV_CC_GetFloatValue("AcquisitionFrameRate", float_param)
        self.fps = float_param.fCurValue if ret == 0 else 0

    def close(self):
        """关闭海康相机"""
        if self.camera is None:
            return

        self.stop_grabbing()

        if self.is_opened:
            self.camera.MV_CC_CloseDevice()
            self.camera.MV_CC_DestroyHandle()
            self.camera = None
            self.is_opened = False
            print(f"{self.camera_name}: 相机已关闭")

    def start_grabbing(self):
        """开始取流"""
        if not self.is_opened:
            print(f"{self.camera_name}: 相机未打开")
            return False

        if self.is_grabbing:
            print(f"{self.camera_name}: 已在取流中")
            return True

        ret = self.camera.MV_CC_StartGrabbing()
        if ret == 0:
            self.is_grabbing = True
            print(f"{self.camera_name}: 开始取流")
            return True
        else:
            print(f"{self.camera_name}: 开始取流失败: 0x{ret:08x}")
            return False

    def stop_grabbing(self):
        """停止取流"""
        if self.is_grabbing:
            ret = self.camera.MV_CC_StopGrabbing()
            if ret == 0:
                self.is_grabbing = False
                print(f"{self.camera_name}: 停止取流")

    def _read_frame_raw(self, timeout_ms=1000):
        """
        原始读取一帧

        Args:
            timeout_ms: 超时时间（毫秒）

        Returns:
            帧数据（numpy数组）或None
        """
        if not self.is_grabbing:
            return None

        stOutFrame = self.MvCamera.MV_FRAME_OUT()
        memset(byref(stOutFrame), 0, self.MvCamera.ctypes.sizeof(stOutFrame))

        ret = self.camera.MV_CC_GetImageBuffer(stOutFrame, timeout_ms)
        if ret != 0:
            return None

        try:
            frame_info = stOutFrame.stFrameInfo
            image_data = (c_ubyte * frame_info.nFrameLen)()
            cdll.msvcrt.memcpy(byref(image_data), stOutFrame.pBufAddr, frame_info.nFrameLen)
            #低延时模式：删除整段memcpy改为以下代码
            # buf = (c_ubyte * frame_info.nFrameLen).from_address(
            #     addressof(stOutFrame.pBufAddr.contents)
            # )
            #
            # img = np.frombuffer(buf, dtype=np.uint8)
            img = np.frombuffer(image_data, dtype=np.uint8)
            pixel_type = frame_info.enPixelType

            if pixel_type == self.MvCamera.PixelType_Gvsp_Mono8:
                img = img.reshape((frame_info.nHeight, frame_info.nWidth))
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif pixel_type == self.MvCamera.PixelType_Gvsp_RGB8_Packed:
                img = img.reshape((frame_info.nHeight, frame_info.nWidth, 3))
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            elif pixel_type == self.MvCamera.PixelType_Gvsp_BGR8_Packed:
                img = img.reshape((frame_info.nHeight, frame_info.nWidth, 3))
            elif pixel_type == self.MvCamera.PixelType_Gvsp_YUV422_Packed:
                img = img.reshape((frame_info.nHeight, frame_info.nWidth, 2))
                img = cv2.cvtColor(img, cv2.COLOR_YUV2BGR_YUYV)
            elif pixel_type == self.MvCamera.PixelType_Gvsp_YUV422_YumVista:
                img = img.reshape((frame_info.nHeight, frame_info.nWidth, 2))
                img = cv2.cvtColor(img, cv2.COLOR_YUV2BGR_YVYU)
            else:
                # 尝试像素格式转换
                convert_param = self.MvCamera.MV_CC_PIXEL_CONVERT_PARAM()
                memset(byref(convert_param), 0, self.MvCamera.ctypes.sizeof(convert_param))
                convert_param.nWidth = frame_info.nWidth
                convert_param.nHeight = frame_info.nHeight
                convert_param.enSrcPixelType = pixel_type
                convert_param.pSrcData = stOutFrame.pBufAddr
                convert_param.nSrcDataLen = frame_info.nFrameLen
                convert_param.enDstPixelType = self.MvCamera.PixelType_Gvsp_BGR8_Packed
                convert_param.nDstBufSize = frame_info.nWidth * frame_info.nHeight * 3
                dst_buffer = (c_ubyte * convert_param.nDstBufSize)()
                convert_param.pDstBuffer = dst_buffer

                ret = self.camera.MV_CC_ConvertPixelType(convert_param)
                if ret == 0:
                    img = np.frombuffer(dst_buffer, dtype=np.uint8)
                    img = img.reshape((frame_info.nHeight, frame_info.nWidth, 3))
                else:
                    return None

            return img
        except Exception as e:
            print(f"{self.camera_name}: 转换图像时出错: {e}")
            return None
        finally:
            self.camera.MV_CC_FreeImageBuffer(stOutFrame)

    # ============ 参数设置方法 ============

    def set_exposure_time(self, exposure_time: float) -> bool:
        """
        设置曝光时间（微秒）

        Args:
            exposure_time: 曝光时间（微秒）

        Returns:
            是否成功
        """
        if not self.is_opened:
            return False

        # 设置为手动曝光
        ret = self.camera.MV_CC_SetEnumValue("ExposureAuto", 0)
        if ret != 0:
            return False

        ret = self.camera.MV_CC_SetFloatValue("ExposureTime", float(exposure_time))
        if ret == 0:
            print(f"{self.camera_name}: 曝光时间已设置为: {exposure_time} µs")
            return True

        return False

    def set_gain(self, gain: float) -> bool:
        """
        设置增益（dB）

        Args:
            gain: 增益值（dB）

        Returns:
            是否成功
        """
        if not self.is_opened:
            return False

        # 设置为手动增益
        ret = self.camera.MV_CC_SetEnumValue("GainAuto", 0)
        if ret != 0:
            return False

        ret = self.camera.MV_CC_SetFloatValue("Gain", float(gain))
        if ret == 0:
            print(f"{self.camera_name}: 增益已设置为: {gain} dB")
            return True

        return False

    def set_trigger_mode(self, mode: int) -> bool:
        """
        设置触发模式
        0 = 连续采集模式 (Off)
        1 = 触发采集模式 (On)

        Args:
            mode: 触发模式

        Returns:
            是否成功
        """
        if not self.is_opened:
            return False

        ret = self.camera.MV_CC_SetEnumValue("TriggerMode", mode)
        if ret == 0:
            mode_str = "连续采集" if mode == 0 else "触发采集"
            print(f"{self.camera_name}: 触发模式已设置为: {mode_str}")
            return True

        return False

    def set_roi(self, x: int, y: int, width: int, height: int) -> bool:
        """
        设置ROI区域

        Args:
            x: 起始X坐标
            y: 起始Y坐标
            width: 区域宽度
            height: 区域高度

        Returns:
            是否成功
        """
        if not self.is_opened:
            return False

        # 先停止取流
        was_grabbing = self.is_grabbing
        if was_grabbing:
            self.stop_grabbing()

        success = True
        ret = self.camera.MV_CC_SetIntValue("OffsetX", x)
        if ret != 0:
            success = False

        ret = self.camera.MV_CC_SetIntValue("OffsetY", y)
        if ret != 0:
            success = False

        ret = self.camera.MV_CC_SetIntValue("Width", width)
        if ret != 0:
            success = False

        ret = self.camera.MV_CC_SetIntValue("Height", height)
        if ret != 0:
            success = False

        if success:
            print(f"{self.camera_name}: ROI已设置: ({x}, {y}) {width}x{height}")
            # 更新参数
            self.width = width
            self.height = height

        # 恢复取流
        if was_grabbing:
            self.start_grabbing()

        return success

    def set_frame_rate(self, fps: float) -> bool:
        """
        设置帧率

        Args:
            fps: 帧率

        Returns:
            是否成功
        """
        if not self.is_opened:
            return False

        ret = self.camera.MV_CC_SetFloatValue("AcquisitionFrameRate", float(fps))
        if ret == 0:
            print(f"{self.camera_name}: 帧率已设置为: {fps} FPS")
            self.fps = fps
            return True

        return False

    def set_pixel_format(self, format_name: str) -> bool:
        """
        设置像素格式
        常用格式: Mono8, RGB8Packed, BGR8Packed

        Args:
            format_name: 像素格式名称

        Returns:
            是否成功
        """
        if not self.is_opened:
            return False

        ret = self.camera.MV_CC_SetEnumValue("PixelFormat", format_name)
        if ret == 0:
            print(f"{self.camera_name}: 像素格式已设置为: {format_name}")
            return True

        return False

    def get_current_params(self) -> dict:
        """获取当前参数"""
        params = {}

        if not self.is_opened:
            return params

        # 曝光时间
        float_param = self.MvCamera.MVCC_FLOATVALUE()
        if self.camera.MV_CC_GetFloatValue("ExposureTime", float_param) == 0:
            params['exposure'] = float_param.fCurValue

        # 增益
        if self.camera.MV_CC_GetFloatValue("Gain", float_param) == 0:
            params['gain'] = float_param.fCurValue

        # ROI
        int_param = self.MvCamera.MVCC_INTVALUE()
        if self.camera.MV_CC_GetIntValue("Width", int_param) == 0:
            params['width'] = int_param.nCurValue
        if self.camera.MV_CC_GetIntValue("Height", int_param) == 0:
            params['height'] = int_param.nCurValue
        if self.camera.MV_CC_GetIntValue("OffsetX", int_param) == 0:
            params['offset_x'] = int_param.nCurValue
        if self.camera.MV_CC_GetIntValue("OffsetY", int_param) == 0:
            params['offset_y'] = int_param.nCurValue

        return params
