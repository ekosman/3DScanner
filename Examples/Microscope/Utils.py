import os
import time
from threading import Thread

import numpy as np
from pyueye import ueye

# from mainDisplay import ControlWindow


def get_bits_per_pixel(color_mode):
    """Returns the number of bits per pixel for the given color mode raises
    exception if color mode is not is not in dict."""

    return {
        ueye.IS_CM_SENSOR_RAW8: 8,
        ueye.IS_CM_SENSOR_RAW10: 16,
        ueye.IS_CM_SENSOR_RAW12: 16,
        ueye.IS_CM_SENSOR_RAW16: 16,
        ueye.IS_CM_MONO8: 8,
        ueye.IS_CM_RGB8_PACKED: 24,
        ueye.IS_CM_BGR8_PACKED: 24,
        ueye.IS_CM_RGBA8_PACKED: 32,
        ueye.IS_CM_BGRA8_PACKED: 32,
        ueye.IS_CM_BGR10_PACKED: 32,
        ueye.IS_CM_RGB10_PACKED: 32,
        ueye.IS_CM_BGRA12_UNPACKED: 64,
        ueye.IS_CM_BGR12_UNPACKED: 48,
        ueye.IS_CM_BGRY8_PACKED: 32,
        ueye.IS_CM_BGR565_PACKED: 16,
        ueye.IS_CM_BGR5_PACKED: 16,
        ueye.IS_CM_UYVY_PACKED: 16,
        ueye.IS_CM_UYVY_MONO_PACKED: 16,
        ueye.IS_CM_UYVY_BAYER_PACKED: 16,
        ueye.IS_CM_CBYCRY_PACKED: 16,
    }[color_mode]


class uEyeException(Exception):
    def __init__(self, error_code):
        self.error_code = error_code

    def __str__(self):
        return "Err: " + str(self.error_code)


def check(ret):
    if ret != ueye.IS_SUCCESS:
        raise uEyeException(ret)


class ImageBuffer:
    def __init__(self):
        self.mem_ptr = ueye.c_mem_p()
        self.mem_id = ueye.int()


class MemoryInfo:
    def __init__(self, h_cam, img_buff):
        self.x = ueye.int()
        self.y = ueye.int()
        self.bits = ueye.int()
        self.pitch = ueye.int()
        self.img_buff = img_buff

        rect_aoi = ueye.IS_RECT()
        check(
            ueye.is_AOI(
                h_cam, ueye.IS_AOI_IMAGE_GET_AOI, rect_aoi, ueye.sizeof(rect_aoi)
            )
        )
        self.width = rect_aoi.s32Width.value
        self.height = rect_aoi.s32Height.value

        check(
            ueye.is_InquireImageMem(
                h_cam,
                self.img_buff.mem_ptr,
                self.img_buff.mem_id,
                self.x,
                self.y,
                self.bits,
                self.pitch,
            )
        )


class ImageData:
    def __init__(self, h_cam, img_buff):
        self.h_cam = h_cam
        self.img_buff = img_buff
        self.mem_info = MemoryInfo(h_cam, img_buff)
        self.color_mode = ueye.is_SetColorMode(h_cam, ueye.IS_GET_COLOR_MODE)
        self.bits_per_pixel = get_bits_per_pixel(self.color_mode)
        self.array = ueye.get_data(
            self.img_buff.mem_ptr,
            self.mem_info.width,
            self.mem_info.height,
            self.mem_info.bits,
            self.mem_info.pitch,
            True,
        )

    def as_1d_image(self):
        channels = int((7 + self.bits_per_pixel) / 8)
        import numpy

        if channels > 1:
            return numpy.reshape(
                self.array, (self.mem_info.height, self.mem_info.width, channels)
            )
        else:
            return numpy.reshape(
                self.array, (self.mem_info.height, self.mem_info.width)
            )

    def unlock(self):
        check(
            ueye.is_UnlockSeqBuf(
                self.h_cam, self.img_buff.mem_id, self.img_buff.mem_ptr
            )
        )


class Rect:
    def __init__(self, x=0, y=0, width=0, height=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class FrameThread(Thread):
    def __init__(self, cam, views=None):
        super(FrameThread, self).__init__()

        self.timeout = 1000
        self.cam = cam
        self.views = views
        self.running = True
        self.frame = np.zeros((100, 100, 1))
        self.action = ""
        self.Folder = ""
        self.dirName = ""
        self.index = 0
        self.exp = 0
        self.save_image = False

    def run(self):
        while self.running:
            img_buffer = ImageBuffer()
            ret = ueye.is_WaitForNextImage(
                self.cam.handle(), self.timeout, img_buffer.mem_ptr, img_buffer.mem_id
            )
            if ret == ueye.IS_SUCCESS:
                image_data = ImageData(self.cam.handle(), img_buffer)
                # frame = image_data.as_1d_image()
                # curr_frame_rgb    = cv2.cvtColor(frame.astype('uint8'), cv2.COLOR_BAYER_GB2BGR)
                # curr_frame_resize = cv2.resize(curr_frame_rgb, (500, 500))
                # # cv2.imwrite('D:/Judith/GUI/MicroscopeLatest/Test/test.png', curr_frame_rgb)
                # height, width, ch = curr_frame_resize.shape
                # bytesPerLine = ch * width
                # qt_image = QImage(curr_frame_resize.data, width, height, bytesPerLine, QImage.Format_RGB888)
                self.notify(image_data)
                print("successful frame")
            else:
                print("Image Timeout")

    def notify(self, image_data):
        if self.views:
            if type(self.views) is not list:
                self.views = [self.views]
            for view in self.views:
                view.handle(image_data)

    def read(self):
        return self.frame

    def stop(self):
        self.cam.stop_video()
        self.running = False


def create_Folder(action, Folder):
    t = time.localtime()
    current_time = time.strftime("%d.%m.%Y_%H.%M.%S", t)
    dirName = Folder + action + str(current_time) + "\\"

    if not os.path.exists(dirName):
        os.mkdir(dirName)
        print("Directory ", dirName, " Created ")
    else:
        print("Directory ", dirName, " already exists")

    return dirName
