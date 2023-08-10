from typing import Optional

import cv2
from ids_peak import ids_peak, ids_peak_ipl_extension

FPS_LIMIT = 30


class Camera:
    def __init__(self, device_manager, device_name: str):
        self.device_manager = device_manager
        self.device_name: str = device_name
        self.device_id: Optional[int] = None
        self.device = None
        self.data_stream = None

        self.image_width: Optional[int] = None
        self.image_height: Optional[int] = None

        self.nodemap_remote_device = None
        self.acquisition_running: bool = False

    def close_device(self):
        self.stop_acquisition()

        if self.data_stream is not None:
            try:
                for buffer in self.data_stream.AnnouncedBuffers():
                    self.data_stream.RevokeBuffer(buffer)
            except Exception as e:
                print(str(e))

    def open_device(self):
        # Return if no device was found
        if self.device_manager.Devices().empty():
            print("No device found!")
            exit()

        available_devices = {
            device.ModelName(): idx
            for idx, device in enumerate(self.device_manager.Devices())
        }
        self.device_id = available_devices[self.device_name]
        self.device = self.device_manager.Devices()[self.device_id].OpenDevice(
            ids_peak.DeviceAccessType_Control
        )

        # Return if no device could be opened
        if self.device is None:
            print("Device could not be opened!")
            exit()

        # Open standard data stream
        datastreams = self.device.DataStreams()
        if datastreams.empty():
            print("Device has no DataStream!")
            self.device = None
            exit()

        self.data_stream = datastreams[0].OpenDataStream()
        self.nodemap_remote_device = self.device.RemoteDevice().NodeMaps()[0]

        try:
            self.nodemap_remote_device.FindNode("UserSetSelector").SetCurrentEntry(
                "Default"
            )
            self.nodemap_remote_device.FindNode("UserSetLoad").Execute()
            self.nodemap_remote_device.FindNode("UserSetLoad").WaitUntilDone()
        except ids_peak.Exception:
            # Userset is not available
            pass

        self.image_height = self.nodemap_remote_device.FindNode("Height").Value()
        self.image_width = self.nodemap_remote_device.FindNode("Width").Value()

        payload_size = self.nodemap_remote_device.FindNode("PayloadSize").Value()
        buffer_count_max = self.data_stream.NumBuffersAnnouncedMinRequired()

        for i in range(buffer_count_max):
            buffer = self.data_stream.AllocAndAnnounceBuffer(payload_size)
            self.data_stream.QueueBuffer(buffer)

    def start_acquisition(self):
        if self.device is None:
            return False
        if self.acquisition_running is True:
            return True

        # Get the maximum framerate possible, limit it to the configured FPS_LIMIT. If the limit can't be reached, set
        # acquisition interval to the maximum possible framerate
        try:
            max_fps = self.nodemap_remote_device.FindNode(
                "AcquisitionFrameRate"
            ).Maximum()
            print(f"Max FPS = f{max_fps}")

            # target_fps = min(max_fps, FPS_LIMIT)
            # self.nodemap_remote_device.FindNode("AcquisitionFrameRate").SetValue(target_fps)
        except ids_peak.Exception:
            # AcquisitionFrameRate is not available. Unable to limit fps. Print warning and continue on.
            print(
                "Unable to limit fps, since the AcquisitionFrameRate Node is"
                " not supported by the connected camera. Program will continue without limit."
            )

        # Setup acquisition timer accordingly
        # self.__acquisition_timer.setInterval((1 / target_fps) * 1000)
        # self.__acquisition_timer.setSingleShot(False)
        # self.__acquisition_timer.timeout.connect(self.on_acquisition_timer)

        try:
            # Lock critical features to prevent them from changing during acquisition
            self.nodemap_remote_device.FindNode("TLParamsLocked").SetValue(1)

            # Start acquisition on camera
            self.data_stream.StartAcquisition()
            self.nodemap_remote_device.FindNode("AcquisitionStart").Execute()
            self.nodemap_remote_device.FindNode("AcquisitionStart").WaitUntilDone()
        except Exception as e:
            print("Exception: " + str(e))
            return False

        # Start acquisition timer
        # self.acquisition_timer.start()
        self.acquisition_running = True

        return True

    def stop_acquisition(self):
        """Stop acquisition timer and stop acquisition on camera :return:"""
        # Check that a device is opened and that the acquisition is running. If not, return.
        if self.device is None or self.acquisition_running is False:
            return

        # Otherwise try to stop acquisition
        try:
            remote_nodemap = self.device.RemoteDevice().NodeMaps()[0]
            remote_nodemap.FindNode("AcquisitionStop").Execute()

            # Stop and flush datastream
            self.data_stream.KillWait()
            self.data_stream.StopAcquisition(ids_peak.AcquisitionStopMode_Default)
            self.data_stream.Flush(ids_peak.DataStreamFlushMode_DiscardAll)

            self.acquisition_running = False

            # Unlock parameters after acquisition stop
            if self.nodemap_remote_device is not None:
                try:
                    self.nodemap_remote_device.FindNode("TLParamsLocked").SetValue(0)
                except Exception as e:
                    print(str(e))

        except Exception as e:
            print(str(e))


def run_single_camera():
    ids_peak.Library.Initialize()
    device_manager = ids_peak.DeviceManager.Instance()
    device_manager.Update()

    rgb_camera: Camera = Camera(
        device_manager=device_manager, device_name="U3-308xCP-C"
    )
    rgb_camera.open_device()
    rgb_camera.start_acquisition()
    rgb_image_size = [rgb_camera.image_height, rgb_camera.image_width]

    for i in range(500):
        rgb_buffer = rgb_camera.data_stream.WaitForFinishedBuffer(5000)
        rgb_image_ipl = ids_peak_ipl_extension.BufferToImage(rgb_buffer)
        rgb_image_np = rgb_image_ipl.get_numpy_1D()
        rgb_camera.data_stream.QueueBuffer(rgb_buffer)

        cv2.imshow("Color Image", rgb_image_np.reshape(rgb_image_size))
        cv2.waitKey(10)

    rgb_camera.close_device()
    ids_peak.Library.Close()


def run_two_cameras():
    ids_peak.Library.Initialize()
    device_manager = ids_peak.DeviceManager.Instance()
    device_manager.Update()

    rgb_camera: Camera = Camera(
        device_manager=device_manager, device_name="U3-308xCP-C"
    )
    pl_camera: Camera = Camera(device_manager=device_manager, device_name="U3-308xCP-P")

    rgb_camera.open_device()
    pl_camera.open_device()

    rgb_camera.start_acquisition()
    pl_camera.start_acquisition()

    rgb_image_size = [rgb_camera.image_height, rgb_camera.image_width]
    pl_image_size = [pl_camera.image_height, pl_camera.image_width]

    for i in range(500):
        rgb_buffer = rgb_camera.data_stream.WaitForFinishedBuffer(5000)
        pl_buffer = pl_camera.data_stream.WaitForFinishedBuffer(5000)

        # Create IDS peak IPL image for debayering and convert it to RGBa8 format
        rgb_image_ipl = ids_peak_ipl_extension.BufferToImage(rgb_buffer)
        pl_image_ipl = ids_peak_ipl_extension.BufferToImage(pl_buffer)

        rgb_image_np = rgb_image_ipl.get_numpy_1D()
        pl_image_np = pl_image_ipl.get_numpy_1D()

        # Queue buffer so that it can be used again
        rgb_camera.data_stream.QueueBuffer(rgb_buffer)
        pl_camera.data_stream.QueueBuffer(pl_buffer)

        cv2.imshow("Color Image", rgb_image_np.reshape(rgb_image_size))
        cv2.imshow("Polar Image", pl_image_np.reshape(pl_image_size))
        cv2.waitKey(10)

    rgb_camera.close_device()
    pl_camera.close_device()
    ids_peak.Library.Close()


if __name__ == "__main__":
    run_single_camera()
    # run_two_cameras()
