"""This module contains a procedure for real time anomaly detection."""

import argparse
import ctypes
import functools
import sys
from time import sleep
from typing import Callable

import cv2
import numpy as np
from ids_peak import ids_peak, ids_peak_ipl_extension
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from numpy.lib.function_base import copy
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QThread  # pylint: disable=no-name-in-module
from PyQt5.QtGui import (  # pylint: disable=no-name-in-module
    QFont,
    QIcon,
    QIntValidator,
    QPalette,
    QPixmap,
)
from PyQt5.QtMultimedia import (  # pylint: disable=no-name-in-module
    QCameraInfo,
    QMediaPlayer,
)

from Scanner3D.camera.ids import Camera
from Scanner3D.interface import Direction, Mode, Scanner, SpeedMode
from Scanner3D.utils.connection import serial_ports

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyle,
    QWidget,
)

from utils.queue import Queue

MAX_PREDS = 50


# pylint disable=missing-function-docstring
def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Video Demo For Anomaly Detection")
    return parser.parse_args()


class VideoThread(QThread):
    """Read video stream and store frames in a queue."""

    def __init__(
        self, queue: Queue, preprocess_fn: Callable, camera_view: QLabel
    ) -> None:
        super().__init__()
        self._run_flag = True
        self._queue = queue
        self._preprocess_fn = preprocess_fn
        self._camera_view = camera_view

        ids_peak.Library.Initialize()
        device_manager = ids_peak.DeviceManager.Instance()
        device_manager.Update()

        self._rgb_camera: Camera = Camera(
            device_manager=device_manager, device_name="U3-308xCP-P"
        )
        self._rgb_camera.open_device()
        self._rgb_camera.start_acquisition()
        self._rgb_image_size = [
            self._rgb_camera.image_height,
            self._rgb_camera.image_width,
        ]

    def run(self) -> None:
        # capture from web cam

        # cap = cv2.VideoCapture(0)
        while self._run_flag:
            print("Hi")
            if self._rgb_camera.is_open:
                rgb_buffer = self._rgb_camera.data_stream.WaitForFinishedBuffer(5000)
                rgb_image_ipl = ids_peak_ipl_extension.BufferToImage(rgb_buffer)
                rgb_image_np = rgb_image_ipl.get_numpy_1D()
                self._rgb_camera.data_stream.QueueBuffer(rgb_buffer)
                cv_img = rgb_image_np.reshape(self._rgb_image_size)
            else:
                cv_img = np.random.randn(100,100,3)
            qt_img = self._preprocess_fn(cv_img)
            self._camera_view.setPixmap(qt_img)
            cv_img = cv2.cvtColor(cv_img.astype(np.float32), cv2.COLOR_BGR2RGB)
            self._queue.put(cv_img)
            sleep(1 / 30)

        # shut down capture system
        self._rgb_camera.close_device()
        ids_peak.Library.Close()

    def stop(self) -> None:
        """Sets run flag to False and waits for thread to finish."""
        self._run_flag = False
        self.wait()


class VideoConsumer(QThread):
    """Consume frames from a queue and perform predictions."""

    def __init__(
        self,
        queue: Queue,
    ) -> None:
        super().__init__()
        self._run_flag = True
        self._queue = queue

    def run(self) -> None:
        while self._run_flag:
            with self._queue._lock:
                if not self._queue.full():
                    continue

                batch = copy(list(reversed(self._queue.get())))

    def stop(self) -> None:
        """Sets run flag to False and waits for thread to finish."""
        self._run_flag = False
        self.wait()


# pylint: disable=missing-class-docstring
class MplCanvas(FigureCanvasQTAgg):
    # pylint: disable=unused-argument
    def __init__(self, parent=None, width=5, height=4, dpi=100) -> None:
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)


class Window(QWidget):
    """Anomaly detection live gui Based on media player code from:

    https://codeloop.org/python-how-to-create-media-player-in-pyqt5/
    """

    def __init__(
        self,
    ) -> None:
        super().__init__()

        self.camera = None
        self.current_camera_name = None

        self.frames_queue = Queue(max_size=32)

        self.setWindowTitle("3D Scanner")

        width, height = [user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)]
        window_width = int(width * 0.75)
        window_height = int(height * 0.75)
        x_offset = (width - window_width) // 2
        y_offset = (height - window_height) // 2

        self.setGeometry(x_offset, y_offset, window_width, window_height)
        self.setWindowIcon(QIcon("player.png"))

        self._baudrate = 9600

        p = self.palette()
        p.setColor(QPalette.Window, Qt.black)
        self.setPalette(p)

        self.init_ui()

        self.y_pred = []

        self.show()

    def init_ui(self) -> None:
        """Create media player object."""
        # setup camera
        self.available_cameras = QCameraInfo.availableCameras()
        self.camera_view = QLabel()
        self.frames_queue = Queue(max_size=32)
        self.camera_id = None
        self.select_camera()

        # creating a combo box for selecting camera
        camera_selector = QComboBox()
        camera_selector.setStatusTip("Choose camera")
        camera_selector.setToolTip("Select Camera")
        camera_selector.setToolTipDuration(2500)
        camera_selector.addItems(
            [camera.description() for camera in self.available_cameras]
        )
        camera_selector.currentIndexChanged.connect(self.select_camera)

        # buttons grid
        buttons_grid = self._setup_buttons()
        buttons_grid_widget = QWidget()
        buttons_grid_widget.setLayout(buttons_grid)

        # AD signal
        # self.graphWidget = MplCanvas(self, width=5, height=1, dpi=100)

        # serial list
        self.serial_list_widget = QComboBox()

        self._ports = serial_ports()
        for i, port in enumerate(self._ports):
            self.serial_list_widget.insertItem(i, port)

        self.serial_list_widget.activated.connect(self._serial_list_clicked)
        self._serial_list_clicked(0)

        # create grid layout
        gridLayout = QGridLayout()
        gridLayout.addWidget(buttons_grid_widget, 2, 8, 3, 3)
        # set widgets to the hbox layout
        gridLayout.addWidget(self.serial_list_widget, 0, 0, 1, 2)
        gridLayout.addWidget(self.camera_view, 1, 0, 5, 5)

        self.setLayout(gridLayout)

        # create the video capture thread
        self.thread = VideoThread(
            queue=self.frames_queue,
            preprocess_fn=self.convert_cv_qt,
            camera_view=self.camera_view,
        )
        self._video_consumer = VideoConsumer(queue=self.frames_queue)
        self.thread.start()
        # self._video_consumer.start()

    def _setup_buttons(self):
        dirs = ["up", "down", "forward", "backward", "xRoll", "yRoll"]
        modes = ["normal", "fast"]
        buttons = {}
        texts = {}
        for dir in dirs:
            for mode in modes:
                button = QPushButton(" ".join([mode, dir]))
                button.setEnabled(True)
                if dir.endswith("Roll"):
                    text = QLineEdit()
                    text.setValidator(QIntValidator())
                    text.setMaxLength(3)
                    text.setAlignment(Qt.AlignCenter)
                    text.setFont(QFont("Arial", 14))
                    button.clicked.connect(
                        functools.partial(
                            self._roll, edit_text=text, dir=Direction(dir)
                        )
                    )
                    texts[" ".join([mode, dir])] = text

                else:
                    message = Scanner.generate_command_for_specs(
                        mode=Mode.SINGLE,
                        direction=Direction(dir),
                        steps=10000,
                        speed=SpeedMode(mode),
                    )
                    button.clicked.connect(
                        functools.partial(self._move, action=message)
                    )

                buttons[" ".join([mode, dir])] = button

        gridLayout = QGridLayout()
        gridLayout.addWidget(buttons["fast up"], 0, 2, 1, 1)
        gridLayout.addWidget(buttons["normal up"], 1, 2, 1, 1)

        gridLayout.addWidget(buttons["fast backward"], 2, 0, 1, 1)
        gridLayout.addWidget(buttons["normal backward"], 2, 1, 1, 1)

        gridLayout.addWidget(buttons["fast forward"], 2, 4, 1, 1)
        gridLayout.addWidget(buttons["normal forward"], 2, 3, 1, 1)

        gridLayout.addWidget(buttons["fast down"], 4, 2, 1, 1)
        gridLayout.addWidget(buttons["normal down"], 3, 2, 1, 1)

        # Rolls
        gridLayout.addWidget(buttons["normal xRoll"], 1, 5, 1, 1)
        gridLayout.addWidget(texts["normal xRoll"], 1, 6, 1, 1)

        gridLayout.addWidget(buttons["normal yRoll"], 3, 5, 1, 1)
        gridLayout.addWidget(texts["normal yRoll"], 3, 6, 1, 1)

        return gridLayout

    def _move(self, action) -> None:
        self._scanner.move(action)

    def _roll(self, edit_text: QLineEdit, dir: Direction):
        message = Scanner.generate_command_for_specs(
            mode=Mode.SINGLE,
            direction=dir,
            steps=edit_text.text(),
            speed=SpeedMode("normal"),
        )
        print(message)
        self._scanner.move(message)

    def _serial_list_clicked(
        self,
        item,
    ) -> None:
        if len(self._ports) == 0:
            return

        port = self._ports[item]
        self._scanner = Scanner(port=port, baudrate=self._baudrate)
        print(f"Using serial {port}")

    def convert_cv_qt(self, cv_img: np.ndarray) -> QPixmap:
        """Convert from an opencv image to QPixmap."""
        rgb_image = cv2.cvtColor(cv_img.astype(np.float32), cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        display_height, display_width = (
            self.camera_view.height(),
            self.camera_view.width(),
        )
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(
            rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888
        )
        p = convert_to_Qt_format.scaled(
            display_width, display_height, Qt.KeepAspectRatio
        )
        return QPixmap.fromImage(p)

    def select_camera(self, camera=0) -> None:
        """Select camera to display."""
        # getting the selected camera
        self.camera = cv2.VideoCapture(camera)

        # getting current camera name
        self.current_camera_name = self.available_cameras[camera].description()

    def play_video(self) -> None:
        """Change the state of the media player."""
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def mediastate_changed(self, *_args) -> None:
        """Called when the state of the media player changes."""
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

        else:
            self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def handle_errors(self) -> None:
        self.playBtn.setEnabled(False)
        self.label.setText("Error: " + self.mediaPlayer.errorString())

    def plot(self) -> None:
        ax = self.graphWidget.axes
        ax.clear()
        ax.set_xlim(0, MAX_PREDS)
        ax.set_ylim(-0.1, 1.1)
        ax.plot(self.y_pred, "*-", linewidth=5)
        self.graphWidget.draw()

    def closeEvent(self, event):
        self.thread._run_flag = False
        print("close")
        self.thread.wait()


if __name__ == "__main__":
    args = get_args()

    app = QApplication(sys.argv)
    window = Window()

    sys.exit(app.exec_())
