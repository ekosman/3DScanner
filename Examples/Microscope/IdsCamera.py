from pyueye import ueye
from Utils import ImageBuffer, Rect, check, get_bits_per_pixel, uEyeException


class Camera:
    def __init__(self, device_id=0):
        self.h_cam = ueye.HIDS(device_id)
        self.img_buffers = []

    def __enter__(self):
        self.init()
        return self

    def __exit__(self, _type, value, traceback):
        self.exit()

    def handle(self):
        return self.h_cam

    def alloc(self, buffer_count=4):
        rect = self.get_aoi()
        bpp = get_bits_per_pixel(self.get_colormode())

        for buff in self.img_buffers:
            check(ueye.is_FreeImageMem(self.h_cam, buff.mem_ptr, buff.mem_id))

        for i in range(buffer_count):
            buff = ImageBuffer()
            ueye.is_AllocImageMem(
                self.h_cam, rect.width, rect.height, bpp, buff.mem_ptr, buff.mem_id
            )

            check(ueye.is_AddToSequence(self.h_cam, buff.mem_ptr, buff.mem_id))

            self.img_buffers.append(buff)

        ueye.is_InitImageQueue(self.h_cam, 0)

    def init(self):
        ret = ueye.is_InitCamera(self.h_cam, None)
        if ret != ueye.IS_SUCCESS:
            self.h_cam = None
            raise uEyeException(ret)

        return ret

    def exit(self):
        ret = None
        if self.h_cam is not None:
            ret = ueye.is_ExitCamera(self.h_cam)
        if ret == ueye.IS_SUCCESS:
            self.h_cam = None

    def get_aoi(self):
        rect_aoi = ueye.IS_RECT()
        ueye.is_AOI(
            self.h_cam, ueye.IS_AOI_IMAGE_GET_AOI, rect_aoi, ueye.sizeof(rect_aoi)
        )

        return Rect(
            rect_aoi.s32X.value,
            rect_aoi.s32Y.value,
            rect_aoi.s32Width.value,
            rect_aoi.s32Height.value,
        )

    def set_aoi(self, x, y, width, height):
        rect_aoi = ueye.IS_RECT()
        rect_aoi.s32X = ueye.int(x)
        rect_aoi.s32Y = ueye.int(y)
        rect_aoi.s32Width = ueye.int(width)
        rect_aoi.s32Height = ueye.int(height)

        return ueye.is_AOI(
            self.h_cam, ueye.IS_AOI_IMAGE_SET_AOI, rect_aoi, ueye.sizeof(rect_aoi)
        )

    def capture_video(self, wait=False):
        wait_param = ueye.IS_WAIT if wait else ueye.IS_DONT_WAIT
        return ueye.is_CaptureVideo(self.h_cam, wait_param)

    def stop_video(self):
        return ueye.is_StopLiveVideo(self.h_cam, ueye.IS_FORCE_VIDEO_STOP)

    def freeze_video(self, wait=False):
        wait_param = ueye.IS_WAIT if wait else ueye.IS_DONT_WAIT
        return ueye.is_FreezeVideo(self.h_cam, wait_param)

    def set_colormode(self, colormode):
        check(ueye.is_SetColorMode(self.h_cam, colormode))

    def get_colormode(self):
        ret = ueye.is_SetColorMode(self.h_cam, ueye.IS_GET_COLOR_MODE)
        return ret

    def get_format_list(self):
        count = ueye.UINT()
        check(
            ueye.is_ImageFormat(
                self.h_cam, ueye.IMGFRMT_CMD_GET_NUM_ENTRIES, count, ueye.sizeof(count)
            )
        )
        format_list = ueye.IMAGE_FORMAT_LIST(ueye.IMAGE_FORMAT_INFO * count.value)
        format_list.nSizeOfListEntry = ueye.sizeof(ueye.IMAGE_FORMAT_INFO)
        format_list.nNumListElements = count.value
        check(
            ueye.is_ImageFormat(
                self.h_cam,
                ueye.IMGFRMT_CMD_GET_LIST,
                format_list,
                ueye.sizeof(format_list),
            )
        )
        return format_list

    # ----- EXPOSURE -----

    def get_exposure_range(self):
        exposure_min, exposure_max, exposure_inc = (
            ueye.DOUBLE(),
            ueye.DOUBLE(),
            ueye.DOUBLE(),
        )
        ueye.is_Exposure(
            self.h_cam,
            ueye.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MIN,
            exposure_min,
            ueye.sizeof(exposure_min),
        )
        ueye.is_Exposure(
            self.h_cam,
            ueye.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MAX,
            exposure_max,
            ueye.sizeof(exposure_max),
        )
        ueye.is_Exposure(
            self.h_cam,
            ueye.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_INC,
            exposure_inc,
            ueye.sizeof(exposure_inc),
        )
        return [exposure_min.value, exposure_max.value, exposure_inc.value]

    def get_exposure(self):
        exposure = ueye.DOUBLE()
        ueye.is_Exposure(
            self.h_cam,
            ueye.IS_EXPOSURE_CMD_GET_EXPOSURE,
            exposure,
            ueye.sizeof(exposure),
        )
        return exposure.value

    def set_exposure(self, exposure):
        exposure = ueye.double(exposure)
        ueye.is_Exposure(
            self.h_cam,
            ueye.IS_EXPOSURE_CMD_SET_EXPOSURE,
            exposure,
            ueye.sizeof(exposure),
        )

    def set_auto_gain(self):
        self.auto_gain = True
        if self.auto_gain == True:
            param = ueye.DOUBLE(0)
            param2 = ueye.DOUBLE(0)
            ueye.is_SetAutoParameter(
                self.h_cam, ueye.IS_SET_ENABLE_AUTO_GAIN, param, param2
            )
        else:
            param = ueye.DOUBLE(1)
            param2 = ueye.DOUBLE(1)
            ueye.is_SetAutoParameter(
                self.h_cam, ueye.IS_SET_ENABLE_AUTO_GAIN, param, param2
            )

    def set_auto_gain_max(self, max_gain):
        limit = ueye.DOUBLE(max_gain)
        pval2 = ueye.DOUBLE(0)
        ueye.is_SetAutoParameter(self.h_cam, ueye.IS_SET_AUTO_GAIN_MAX, limit, pval2)

    def get_auto_gain_max(self):
        returned_gain = ueye.DOUBLE()
        val2 = ueye.DOUBLE(0)
        ueye.is_SetAutoParameter(
            self.h_cam, ueye.IS_GET_AUTO_GAIN_MAX, returned_gain, val2
        )
        return returned_gain.value

    def set_gain(self, master, red, green, blue):
        master, red, green, blue = (
            ueye.INT(master),
            ueye.INT(red),
            ueye.INT(green),
            ueye.INT(blue),
        )
        ueye.is_SetHardwareGain(self.h_cam, master, red, green, blue)

    def get_gain(self):
        nRed = 0
        nGreen = 0
        nBlue = 0
        return ueye.is_SetHardwareGain(
            self.h_cam, ueye.IS_GET_MASTER_GAIN, nRed, nGreen, nBlue
        )

    # ----- PIXEL CLOCK -----

    def get_pixel_clock(self):
        pixel_clock = ueye.UINT()
        ueye.is_PixelClock(
            self.h_cam,
            ueye.IS_PIXELCLOCK_CMD_GET,
            pixel_clock,
            ueye.sizeof(pixel_clock),
        )
        return pixel_clock.value

    def set_pixel_clock(self, pixel_clock):
        pixel_clock = ueye.UINT(pixel_clock)
        ueye.is_PixelClock(
            self.h_cam,
            ueye.IS_PIXELCLOCK_CMD_SET,
            pixel_clock,
            ueye.sizeof(pixel_clock),
        )

    # ----- FRAME RATE -----

    def set_frame_rate(self, frame_rate):
        frame_rate = ueye.double(frame_rate)
        frame_rate_actual = ueye.DOUBLE()
        ueye.is_SetFrameRate(self.h_cam, frame_rate, frame_rate_actual)
        return frame_rate_actual.value

    # ----- EXTERNAL TRIGGER -----
    def enable_external_trigger(self):
        # Hardcoded rising edge
        ueye.is_SetExternalTrigger(self.h_cam, ueye.IS_SET_TRIGGER_LO_HI)

    def disable_external_trigger(self):
        # Hardcoded rising edge
        ueye.is_SetExternalTrigger(self.h_cam, ueye.IS_SET_TRIGGER_OFF)


if __name__ == "__main__":
    import cv2
    from Utils import FrameThread

    cam = Camera()
    cam.init()
    cam.set_auto_gain_max(50)
    # cam.get_auto_gain_max()
    # print(cam.get_auto_gain_max())
    # cam.set_auto_gain()
    # cam.set_gain(5, 5, 5, 5)
    # cam.get_gain()
    cam.set_colormode(ueye.IS_CM_SENSOR_RAW8)
    cam.set_aoi(0, 0, 1280, 1024)
    cam.alloc()
    print(cam.set_frame_rate(10))
    cam.set_exposure(5)
    print("Exposure set to {} ms".format(cam.get_exposure()))
    # cam.enable_external_trigger()
    cam.capture_video()

    thread = FrameThread(cam)
    thread.start()
    resize_factor = 0.5
    cv2.namedWindow("frame")
    while True:
        frame_1 = thread.read()

        frame_1 = cv2.cvtColor(frame_1.astype("uint8"), cv2.COLOR_BAYER_BG2BGR)
        frame_1 = cv2.resize(frame_1, None, fx=resize_factor, fy=resize_factor)
        frame_1[frame_1 > 255] = 255
        cv2.imshow("frame", frame_1.astype("uint8"))

        key = cv2.waitKey(1)
        if key == 13:
            break

    # cleanup

    thread.stop()
    thread.join()
    cv2.destroyAllWindows()
    cam.stop_video()
    cam.exit()
