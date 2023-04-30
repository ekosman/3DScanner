"""This module contains a procedure for real time anomaly detection."""

import argparse
import sys
from typing import Callable

import cv2
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from numpy.lib.function_base import copy
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QThread  # pylint: disable=no-name-in-module
from PyQt5.QtGui import QIcon, QPalette, QPixmap  # pylint: disable=no-name-in-module
from PyQt5.QtMultimedia import (  # pylint: disable=no-name-in-module
    QCameraInfo,
    QMediaPlayer,
)
from PyQt5.QtWidgets import QComboBox  # pylint: disable=no-name-in-module
from PyQt5.QtWidgets import (
    QApplication,
    QGridLayout,
    QLabel,
    QPushButton,
    QStyle,
    QWidget,
)

from utils.queue import Queue

MAX_PREDS = 50


# pylint disable=missing-function-docstring
def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Video Demo For Anomaly Detection")

    parser.add_argument(
        "--clip_length",
        type=int,
        default=16,
        help="define the length of each input sample",
    )

    return parser.parse_args()


class VideoThread(QThread):
    """Read video stream and store frames in a queue."""

    def __init__(self, queue: Queue, preprocess_fn: Callable, camera_view: QLabel) -> None:
        super().__init__()
        self._run_flag = True
        self._queue = queue
        self._preprocess_fn = preprocess_fn
        self._camera_view = camera_view

    def run(self) -> None:
        # capture from web cam
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                qt_img = self._preprocess_fn(cv_img)
                self._camera_view.setPixmap(qt_img)
                cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                self._queue.put(cv_img)
        # shut down capture system
        cap.release()

    def stop(self) -> None:
        """Sets run flag to False and waits for thread to finish."""
        self._run_flag = False
        self.wait()


class VideoConsumer(QThread):
    """Consume frames from a queue and perform predictions."""

    def __init__(self, queue: Queue,) -> None:
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

        self.setWindowTitle("Anomaly Media Player")
        self.setGeometry(350, 100, 700, 500)
        self.setWindowIcon(QIcon("player.png"))

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
        camera_selector.addItems([camera.description() for camera in self.available_cameras])
        camera_selector.currentIndexChanged.connect(self.select_camera)

        # create button for playing
        self.playBtn = QPushButton()
        self.playBtn.setEnabled(True)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playBtn.clicked.connect(self.play_video)

        # create grid layout
        gridLayout = QGridLayout()

        # AD signal
        self.graphWidget = MplCanvas(self, width=5, height=1, dpi=100)

        # set widgets to the hbox layout
        gridLayout.addWidget(self.graphWidget, 0, 0, 1, 5)
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
        self._video_consumer.start()

    def convert_cv_qt(self, cv_img: np.ndarray) -> QPixmap:
        """Convert from an opencv image to QPixmap."""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        display_height, display_width = (
            self.camera_view.height(),
            self.camera_view.width(),
        )
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(display_width, display_height, Qt.KeepAspectRatio)
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


if __name__ == "__main__":
    args = get_args()

    app = QApplication(sys.argv)
    window = Window()

    sys.exit(app.exec_())
