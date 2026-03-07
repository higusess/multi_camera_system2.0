"""
Simple camera detection script without GUI
"""

import cv2
from usb_camera import UsbCamera
from hikvision_camera_impl import HikvisionCamera


def detect_usb_cameras():
    """Detect USB cameras"""
    print("=" * 70)
    print("USB Camera Detection")
    print("=" * 70)

    available = []
    for i in range(10):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                print(f"  Camera {i}: {width}x{height} @ {fps:.1f} FPS")
                available.append(i)
            else:
                print(f"  Camera {i}: Available but cannot read")
            cap.release()

    print(f"\nFound {len(available)} USB camera(s)")
    return available


def detect_hikvision_cameras():
    """Detect Hikvision cameras"""
    print("\n" + "=" * 70)
    print("Hikvision Camera Detection")
    print("=" * 70)

    camera = HikvisionCamera(device_type="USB", device_index=0)
    device_list = camera.enum_devices()

    if device_list is not None:
        print(f"\nFound {device_list.nDeviceNum} Hikvision camera(s)")
        return device_list.nDeviceNum
    else:
        print("\nNo Hikvision cameras found")
        return 0


if __name__ == "__main__":
    usb_count = len(detect_usb_cameras())
    hikvision_count = detect_hikvision_cameras()

    print("\n" + "=" * 70)
    print("Summary:")
    print(f"  USB Cameras: {usb_count}")
    print(f"  Hikvision Cameras: {hikvision_count}")
    print("=" * 70)
