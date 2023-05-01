import sys
import time
import cv2
import pickle
import PIL
from PIL import Image
import numpy as np
from IdsCamera import Camera
from ArduinoControl import ArduinoControl
from Utils import FrameThread, create_Folder
from pyueye import ueye
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QHBoxLayout, QPushButton, QGridLayout, QGraphicsScene, QGraphicsView, QVBoxLayout, QFrame, QCheckBox
from PyQt5.QtGui import QImage, QFont
from PyQt5.QtCore import pyqtSlot, Qt, pyqtSignal, QCoreApplication


class ControlWindow(QWidget):

    update_signal = pyqtSignal(QImage, name="update_signal")
    changeImgIdx = pyqtSignal(int)
    # keyPressed = pyqtSignal(int)

    def __init__(self, camera, parent=None):

        super(ControlWindow, self).__init__(parent)
        self.optotune_value = 20

        self.camera = camera
        self.camera_thread = None
        self.image = None
        self.img_idx = 0
        self.make_folder = False



        # window cosmetics
        self.setWindowTitle("Microscope controller")
        self.setFixedSize(1280, 800)

        # --------------------  Arduino initial setup  -----------------------#
        self.arduino = ArduinoControl()
        self.arduino.setNSteps(self.optotune_value)
        self.arduino.LightExposure(3000)
        self.arduino.stopLiveView()
        # self.arduino.startLiveView()

        # --------------------  Optotune  -----------------------#
        optotune_lbl = QLabel("Optotune Steps")
        # optotune_lbl.setFont(QFont('SansSerif', 20))
        self.optotune_display = QLabel(self)
        self.optotune_display.setNum(self.optotune_value)

        # Optotune PushButtons
        self.optotune_btn_up = QPushButton("+")
        self.optotune_btn_up.setCheckable(True)
        self.optotune_btn_up.setFixedSize(30, 30)
        self.optotune_btn_up.clicked.connect(self.optotune_increase_num)

        self.optotune_btn_down = QPushButton("-")
        self.optotune_btn_down.setCheckable(True)
        self.optotune_btn_down.setFixedSize(30, 30)
        self.optotune_btn_down.clicked.connect(self.optotune_decrease_num)
        # self.image_num = self.optotune_sp.value()

        self.up_down_opto_layout = QHBoxLayout()
        self.up_down_opto_layout.setSpacing(0)
        self.up_down_opto_layout.addWidget(self.optotune_btn_up)
        self.up_down_opto_layout.addWidget(self.optotune_btn_down)

        optotune_num_layout = QHBoxLayout()
        optotune_num_layout.setSpacing(30)
        optotune_num_layout.addWidget(optotune_lbl)
        optotune_num_layout.addWidget(self.optotune_display)
        optotune_num_layout.addLayout(self.up_down_opto_layout)


        # --------------------  Capture Settings  -----------------------#

        self.do_save = False
        self.capturing = False

        # --------------------  Saving Settings  -----------------------#

        self.curr_action = ''
        self.Folder = 'D:\\Judith\\GUI\\DiverMicroscope\\ImageTests\\'
        self.curr_action = None
        self.save_image = False
        self.dirName = ''

        # --------------------  Display Settings  -----------------------#
        self.graphics_view = QGraphicsView(self)

        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)

        self.scene.drawBackground = self.draw_background
        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        self.update_signal.connect(self.update_image)

        display_layout = QVBoxLayout()
        display_layout.addWidget(self.graphics_view)


        self.img_idx = 0
        img_number_lbl = QLabel('Image Index')
        self.img_number_display = QLabel(self)
        self.img_number_display.setFrameShape(QFrame.Panel)
        self.img_number_display.setFixedSize(70, 25)
        self.img_number_display.setAlignment(Qt.AlignCenter)
        self.img_number_display.setNum(self.img_idx)
        self.changeImgIdx.connect(self.img_idx_valuechange)

        img_num_layout = QHBoxLayout()
        img_num_layout.setContentsMargins(0, 0, 1, 0)
        img_num_layout.setSpacing(50)
        img_num_layout.addWidget(img_number_lbl)
        img_num_layout.addWidget(self.img_number_display)

        # --------------------  exposure  -----------------------#
        exposure_lbl = QLabel("Camera Exposure")
        self.exposure_value = 3
        self.exposure_display = QLabel(self)
        # self.exposure_display.setFont(QFont('SansSerif', 20))
        self.exposure_display.setNum(self.exposure_value)

        # Exposure SpinBox
        self.exposure_btn_up = QPushButton("+")
        self.exposure_btn_up.setCheckable(True)
        self.exposure_btn_up.setFixedSize(30, 30)
        self.exposure_btn_up.clicked.connect(self.exposure_increase)

        self.exposure_btn_down = QPushButton("-")
        self.exposure_btn_down.setCheckable(True)
        self.exposure_btn_down.setFixedSize(30, 30)
        self.exposure_btn_down.clicked.connect(self.exposure_decrease)

        up_down_expo_layout = QHBoxLayout()
        up_down_expo_layout.setSpacing(0)
        up_down_expo_layout.addWidget(self.exposure_btn_up)
        up_down_expo_layout.addWidget(self.exposure_btn_down)

        exposure_layout = QHBoxLayout()
        exposure_layout.addWidget(exposure_lbl)
        exposure_layout.setSpacing(20)
        exposure_layout.addWidget(self.exposure_display)
        exposure_layout.addLayout(up_down_expo_layout)



        # --------------------  Capture button  -----------------------#
        btn_width = 85
        btn_hight = 65

        # control_window.keyPressed.connect(self.on_key)

        self.stack_btn = QPushButton("Stack")
        self.stack_btn.setCheckable(True)
        self.stack_btn.setFixedSize(btn_width, btn_hight)
        # self.hover(self.stack_btn)
        # self.activeButton(self.stack_btn)
        self.stack_btn.clicked.connect(self.stack_btn_clicked)

        self.live_view_btn = QPushButton("Live View")
        self.live_view_btn.setCheckable(True)
        self.live_view_btn.setFixedSize(btn_width, btn_hight)
        self.live_view_btn.clicked.connect(self.live_view_btn_clicked)

        self.one_shot_btn = QPushButton("One-Shot")
        self.one_shot_btn.setCheckable(True)
        self.one_shot_btn.setFixedSize(btn_width, btn_hight)
        self.one_shot_btn.clicked.connect(self.one_shot_btn_clicked)

        # ---------- Save ------------#
        self.save_btn = QPushButton("Save")
        self.save_btn.setCheckable(True)
        self.save_btn.setFixedSize(btn_width, btn_hight)
        self.save_btn.setShortcut("S")
        self.save_btn.clicked.connect(self.save_btn_clicked)

        # ---------- Step Up/Down------------#
        self.step_value = 0
        self.step_display = QLabel(self)
        # self.exposure_display.setFont(QFont('SansSerif', 20))
        self.step_display.setFrameShape(QFrame.Panel)
        self.step_display.setFixedSize(25, 25)
        self.step_display.setNum(self.step_value)
        self.img_number_display.setAlignment(Qt.AlignCenter)

        self.optotune_step_up_btn = QPushButton("+")
        self.optotune_step_up_btn.setFixedSize(25, btn_hight)
        self.optotune_step_up_btn.clicked.connect(self.optotune_step_up_btn_clicked)

        self.optotune_step_down_btn = QPushButton("-")
        self.optotune_step_down_btn.setFixedSize(25, btn_hight)
        self.optotune_step_down_btn.clicked.connect(self.optotune_step_down_btn_clicked)

        self.optotune_step_layout = QHBoxLayout()
        self.optotune_step_layout.setSpacing(0)
        self.optotune_step_layout.addWidget(self.optotune_step_up_btn)
        self.optotune_step_layout.addWidget(self.optotune_step_down_btn)

        # ------------ User Input Optotune Limits ------------- #
        self.optotune_enter_value_box = QCheckBox()
        self.optotune_enter_value_box.setMaximumSize(50, 50)
        self.optotune_enter_value_box.clicked.connect(self.enter_opto_limits_checked)

        # ------------Upper Limit------------- #
        self.opto_upper_limit = QLabel('Upper Limit')
        self.opto_upper_limit_display = QLabel(self)
        self.opto_upper_limit_value = 15
        self.opto_upper_limit_display.setFrameShape(QFrame.Panel)
        self.opto_upper_limit_display.setAlignment(Qt.AlignCenter)
        self.opto_upper_limit_display.setFixedSize(60, 30)
        self.opto_upper_limit_display.setNum(self.opto_upper_limit_value)

        self.opto_up_up_btn = QPushButton("+")
        self.opto_up_up_btn.setCheckable(True)
        self.opto_up_up_btn.setFixedSize(30, 30)
        self.opto_up_up_btn.clicked.connect(self.opto_up_up)
        self.opto_up_up_btn.setEnabled(False)

        self.opto_up_down_btn = QPushButton("-")
        self.opto_up_down_btn.setCheckable(True)
        self.opto_up_down_btn.setFixedSize(30, 30)
        self.opto_up_down_btn.clicked.connect(self.opto_up_down)
        self.opto_up_down_btn.setEnabled(False)

        # ------------Lower Limit------------- #
        self.opto_lower_limit = QLabel('Lower Limit')
        self.opto_lower_limit_display = QLabel(self)
        self.opto_lower_limit_value = 1
        self.opto_lower_limit_display.setFrameShape(QFrame.Panel)
        self.opto_lower_limit_display.setAlignment(Qt.AlignCenter)
        self.opto_lower_limit_display.setFixedSize(60, 30)
        self.opto_lower_limit_display.setNum(self.opto_lower_limit_value)

        self.opto_lower_up_btn = QPushButton("+")
        self.opto_lower_up_btn.setCheckable(True)
        self.opto_lower_up_btn.setFixedSize(30, 30)
        self.opto_lower_up_btn.clicked.connect(self.opto_lower_up)
        self.opto_lower_up_btn.setEnabled(False)

        self.opto_lower_down_btn = QPushButton("-")
        self.opto_lower_down_btn.setCheckable(True)
        self.opto_lower_down_btn.setFixedSize(30, 30)
        self.opto_lower_down_btn.clicked.connect(self.opto_lower_down)
        self.opto_lower_down_btn.setEnabled(False)

        # ------------ User Input Opto Layout ------------ #
        self.opto_up_btn_layout = QHBoxLayout()
        self.opto_up_btn_layout.addWidget(self.opto_up_up_btn)
        self.opto_up_btn_layout.addWidget(self.opto_up_down_btn)

        self.opto_user_up_layout = QVBoxLayout()
        self.opto_user_up_layout.setSpacing(0)
        self.opto_user_up_layout.addWidget(self.opto_upper_limit)
        self.opto_user_up_layout.addWidget(self.opto_upper_limit_display)
        self.opto_user_up_layout.addLayout(self.opto_up_btn_layout)

        self.opto_lower_btn_layout = QHBoxLayout()
        self.opto_lower_btn_layout.addWidget(self.opto_lower_up_btn)
        self.opto_lower_btn_layout.addWidget(self.opto_lower_down_btn)

        self.opto_user_lower_layout = QVBoxLayout()
        self.opto_user_lower_layout.setSpacing(0)
        self.opto_user_lower_layout.addWidget(self.opto_lower_limit)
        self.opto_user_lower_layout.addWidget(self.opto_lower_limit_display)
        self.opto_user_lower_layout.addLayout(self.opto_lower_btn_layout)

        # ------------ Trigger ------------------------ #
        self.trigger_btn = QPushButton("Trigger")
        self.trigger_btn.setCheckable(True)
        self.trigger_btn.setFixedSize(60, btn_hight)
        self.trigger_btn.setShortcut("T")
        self.trigger_btn.clicked.connect(self.trigger_btn_clicked)

        # ------------ Light On/Of ------------------------ #
        self.light_btn = QPushButton("Light Off")
        self.light_btn.setCheckable(True)
        self.light_btn.setFixedSize(60, btn_hight)
        self.light_btn.clicked.connect(self.light_btn_clicked)
        # ------------ Close Gui ------------------------ #
        self.exit_btn = QPushButton("Exit")
        self.exit_btn.setCheckable(True)
        self.exit_btn.setFixedSize(40, 40)
        # self.exit_btn.clicked.connect(QCoreApplication.instance().quit)
        self.exit_btn.clicked.connect(self.exit_gui)

        img_num_layout.addWidget(self.exit_btn)
        # --------------- Sub Layoutsד------------- #
        # self.live_view_btn.setChecked(True)
        # self.one_shot_btn.setEnabled(False)
        # self.stack_btn.setEnabled(False)

        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(10)
        action_layout.addWidget(self.stack_btn)
        action_layout.addWidget(self.live_view_btn)
        action_layout.addWidget(self.one_shot_btn)

        state_layout = QHBoxLayout()
        state_layout.setSpacing(10)
        state_layout.addWidget(self.save_btn)
        state_layout.addWidget(self.trigger_btn)
        state_layout.addWidget(self.light_btn)

        optotune_layout = QHBoxLayout()
        optotune_layout.addLayout(self.optotune_step_layout)
        optotune_layout.addWidget(self.step_display)
        optotune_layout.addLayout(self.opto_user_lower_layout)
        optotune_layout.addLayout(self.opto_user_up_layout)
        optotune_layout.addWidget(self.optotune_enter_value_box)

        # ---------- Button Main Layout------------#
        btn_main_layout = QVBoxLayout()
        btn_main_layout.setContentsMargins(0, 0, 50, 0)
        btn_main_layout.setSpacing(20)
        btn_main_layout.addLayout(img_num_layout)
        btn_main_layout.addLayout(optotune_num_layout)
        btn_main_layout.addLayout(exposure_layout)
        btn_main_layout.addLayout(action_layout)
        btn_main_layout.addLayout(state_layout)
        btn_main_layout.addLayout(optotune_layout)
        # ---------- Arrange Main Layout------------#
        main_layout = QGridLayout()
        # main_layout.setVerticalSpacing(20)
        # main_layout.addLayout(img_num_layout, 0, 0, Qt.AlignLeft)
        # main_layout.addLayout(optotune_layout, 1, 0, Qt.AlignLeft)
        # main_layout.addLayout(exposure_layout, 2, 0, Qt.AlignLeft)
        # main_layout.addLayout(action_layout, 3, 0, Qt.AlignLeft)
        # main_layout.addLayout(state_layout, 4, 0, Qt.AlignLeft)
        main_layout.addLayout(btn_main_layout, 0, 0)
        main_layout.addLayout(display_layout, 0, 2)
        self.setLayout(main_layout)

    def trigger_btn_clicked(self):
        if self.trigger_btn.isChecked():
            self.camera.stop_video()
            self.camera.enable_external_trigger()
            self.camera.capture_video()
            self.arduino.startLiveView()
            self.live_view_btn.setChecked(True)
        else:
            self.camera.stop_video()
            self.camera.disable_external_trigger()
            self.camera.capture_video()

    def stack_btn_clicked(self):
        if self.stack_btn.isChecked() and self.optotune_enter_value_box.isChecked():
            self.live_view_btn.setEnabled(False)
            self.one_shot_btn.setEnabled(False)
            self.img_idx = self.opto_lower_limit_value
            if self.make_folder == True:
                self.curr_action = 'LimitedStack'
                self.dirName = create_Folder(self.curr_action, self.Folder)
                self.save_image = True
            self.arduino.startFocalStack()
        elif self.stack_btn.isChecked():
            self.live_view_btn.setEnabled(False)
            self.one_shot_btn.setEnabled(False)
            if self.make_folder == True:
                self.curr_action = 'Stack'
                self.dirName = create_Folder(self.curr_action, self.Folder)
                self.save_image = True
            self.img_idx = 0
            self.arduino.startFocalStack()

        else:
            self.live_view_btn.setEnabled(True)
            self.one_shot_btn.setEnabled(True)


    def live_view_btn_clicked(self):
        if self.live_view_btn.isChecked():
            self.stack_btn.setEnabled(False)
            self.one_shot_btn.setEnabled(False)
            if self.make_folder == True:
                self.curr_action = 'LiveView'
                self.dirName = create_Folder(self.curr_action, self.Folder)
                self.save_image = True
            self.img_idx = 0
            self.arduino.startLiveView()
        else:
            self.stack_btn.setEnabled(True)
            self.one_shot_btn.setEnabled(True)

    # def one_shot_btn_clicked(self):
    #     #     if self.one_shot_btn.isChecked() and self.optotune_enter_value_box.isChecked():
    #     #         self.stack_btn.setEnabled(False)
    #     #         self.live_view_btn.setEnabled(False)
    #     #         if self.make_folder == True:
    #     #             self.curr_action = 'One-Shot'
    #     #             self.dirName = create_Folder(self.curr_action, self.Folder)
    #     #             self.save_image = True
    #     #         self.img_idx = 0
    #     #         self.arduino.startLimitedOneShot()
    #     #     elif self.one_shot_btn.isChecked():
    #     #         self.stack_btn.setEnabled(False)
    #     #         self.live_view_btn.setEnabled(False)
    #     #         if self.make_folder == True:
    #     #             self.curr_action = 'One-Shot'
    #     #             self.dirName = create_Folder(self.curr_action, self.Folder)
    #     #             self.save_image = True
    #     #         self.img_idx = 0
    #     #         self.arduino.startOneShot()
    #     #     else:
    #     #         self.stack_btn.setEnabled(True)
    #     #         self.live_view_btn.setEnabled(True)

    def one_shot_btn_clicked(self):
        if self.one_shot_btn.isChecked():
            self.stack_btn.setEnabled(False)
            self.live_view_btn.setEnabled(False)
            if self.make_folder == True:
                self.curr_action = 'OneShot'
                self.dirName = create_Folder(self.curr_action, self.Folder)
                self.save_image = True
            self.img_idx = 0
            self.arduino.startOneShot()
        else:
            self.stack_btn.setEnabled(True)
            self.live_view_btn.setEnabled(True)


    def save_btn_clicked(self):
        if self.save_btn.isChecked() and self.live_view_btn.isChecked():
            self.img_idx = 0
            self.curr_action = 'LiveView'
            self.dirName = create_Folder(self.curr_action, self.Folder)
            self.save_image = True
        elif self.save_btn.isChecked():
            self.img_idx = 0
            self.make_folder = True
        else:
            self.save_image = False
            self.make_folder = False

    def light_btn_clicked(self):
        if self.light_btn.isChecked():
            self.arduino.LightsOff()
        else:
            self.arduino.LightsOn()


    def optotune_step_up_btn_clicked(self):
        self.step_value = self.step_value - 1
        self.step_display.setNum(self.step_value)
        self.arduino.stepBackward()
        time.sleep(1)
        self.arduino.printAll()
        self.live_view_btn.setChecked(True)
        self.live_view_btn_clicked()

    def optotune_step_down_btn_clicked(self):
        self.step_value = self.step_value + 1
        self.step_display.setNum(self.step_value)
        self.arduino.stepForward()
        time.sleep(1)
        self.arduino.printAll()
        self.live_view_btn.setChecked(True)
        self.live_view_btn_clicked()

    def opto_up_up(self):
        self.opto_upper_limit_value = self.opto_upper_limit_value + 1
        self.opto_upper_limit_display.setNum(self.opto_upper_limit_value)
        self.arduino.upperOptoLimit(self.opto_upper_limit_value)
        self.live_view_btn.setChecked(True)
        self.live_view_btn_clicked()

    def opto_up_down(self):
        self.opto_upper_limit_value = self.opto_upper_limit_value - 1
        self.opto_upper_limit_display.setNum(self.opto_upper_limit_value)
        self.arduino.upperOptoLimit(self.opto_upper_limit_value)
        self.live_view_btn.setChecked(True)
        self.live_view_btn_clicked()

    def opto_lower_up(self):
        self.opto_lower_limit_value = self.opto_lower_limit_value + 1
        self.opto_lower_limit_display.setNum(self.opto_lower_limit_value)
        self.arduino.lowerOptoLimit(self.opto_lower_limit_value)
        self.live_view_btn.setChecked(True)
        self.live_view_btn_clicked()

    def opto_lower_down(self):
        self.opto_lower_limit_value = self.opto_lower_limit_value - 1
        self.opto_lower_limit_display.setNum(self.opto_lower_limit_value)
        self.arduino.lowerOptoLimit(self.opto_lower_limit_value)
        self.live_view_btn.setChecked(True)
        self.live_view_btn_clicked()

    def enter_opto_limits_checked(self):
        if self.optotune_enter_value_box.isChecked():
            self.opto_up_up_btn.setEnabled(True)
            self.opto_up_down_btn.setEnabled(True)
            self.opto_lower_up_btn.setEnabled(True)
            self.opto_lower_down_btn.setEnabled(True)
        else:
            self.opto_up_up_btn.setEnabled(False)
            self.opto_up_down_btn.setEnabled(False)
            self.opto_lower_up_btn.setEnabled(False)
            self.opto_lower_down_btn.setEnabled(False)

    def optotune_increase_num(self):
        self.optotune_value = self.optotune_value + 1
        self.optotune_display.setNum(self.optotune_value)
        self.arduino.setNSteps(self.optotune_value)
        self.live_view_btn.setChecked(True)
        self.live_view_btn_clicked()

    def optotune_decrease_num(self):
        self.optotune_value = self.optotune_value - 1
        self.optotune_display.setNum(self.optotune_value)
        self.arduino.setNSteps(self.optotune_value)
        self.live_view_btn.setChecked(True)
        self.live_view_btn_clicked()


    def exposure_increase(self):
        if self.exposure_value >= 40:
            self.exposure_value = 40
        else:
            self.exposure_value = self.exposure_value + 1
        self.exposure_display.setNum(self.exposure_value)
        self.arduino.setExposure(self.exposure_value * 1000)
        self.arduino.LightExposure(self.exposure_value * 1000)
        print(self.camera.get_gain())
        self.camera.set_exposure(self.exposure_value)
        self.live_view_btn.setChecked(True)
        self.live_view_btn_clicked()

    def exposure_decrease(self):
        if self.exposure_value <= 1:
            self.exposure_value = 1
        else:
            self.exposure_value = self.exposure_value - 1
        self.exposure_display.setNum(self.exposure_value)
        self.arduino.setExposure(self.exposure_value * 1000)
        self.arduino.LightExposure(self.exposure_value * 1000)
        self.camera.set_exposure(self.exposure_value)
        self.live_view_btn.setChecked(True)
        self.live_view_btn_clicked()

    def draw_background(self, painter, rect):
        if self.image:
            image = self.image.scaled(rect.width(), rect.height(), Qt.KeepAspectRatio)
            painter.drawImage(rect.x(), rect.y(), image)

    def exit_gui(self):
        if self.exit_btn.isChecked():
            self.arduino.LightsOff()
            camera_thread.stop()
            camera.stop_video()
            camera.exit()
            sys.exit(app.exec_())
            cv2.destroyAllWindows()



    @pyqtSlot(int)
    def img_idx_valuechange(self, image_idx):
        self.img_number_display.setNum(image_idx)
        if image_idx > self.optotune_value and self.stack_btn.isChecked():
            self.save_image = False
            self.make_folder = False
            self.save_btn.setEnabled(True)
            self.save_btn.setChecked(False)
            self.stack_btn.setEnabled(True)
            self.stack_btn.setChecked(False)
            self.one_shot_btn.setEnabled(True)
            self.live_view_btn.setEnabled(True)
            self.live_view_btn.setChecked(True)
            self.live_view_btn_clicked()
        elif image_idx >= 1 and self.one_shot_btn.isChecked():
            self.save_image = False
            self.make_folder = False
            self.save_btn.setEnabled(True)
            self.save_btn.setChecked(False)
            self.one_shot_btn.setEnabled(True)
            self.one_shot_btn.setChecked(False)
            self.live_view_btn.setEnabled(True)
            self.live_view_btn.setChecked(True)
            self.live_view_btn_clicked()
        elif image_idx > self.opto_upper_limit_value and self.optotune_enter_value_box.isChecked():
            self.save_image = False
            self.make_folder = False
            self.save_btn.setEnabled(True)
            self.save_btn.setChecked(False)
            self.one_shot_btn.setEnabled(True)
            self.one_shot_btn.setChecked(False)
            self.live_view_btn.setEnabled(True)
            self.live_view_btn.setChecked(True)
            self.live_view_btn_clicked()



    def update_image(self, image):
        self.scene.update()

    def handle(self, image_data):
        # print(camera.get_gain())
        self.image = self.process_image(image_data)
        self.update_signal.emit(self.image)
        self.img_idx = self.img_idx + 1
        self.img_idx_valuechange(self.img_idx)
        image_data.unlock()

    def process_image(self, image_data):
        image = image_data.as_1d_image()

        if self.save_image == True:
            exp = self.camera.get_exposure()
            exp_rounded = round(exp, 2)
            file = open(self.dirName + 'file' + str(self.img_idx) + 'Exp_' + str(exp_rounded)  + 'TotStepNumbers' + str(self.optotune_value) + '.bin', 'wb')
            image.tofile(file)

        image = cv2.cvtColor(image.astype('uint8'), cv2.COLOR_BAYER_GB2BGR)
        image = cv2.resize(image, (500, 500))
        height, width, ch = image.shape
        bytesPerLine = ch * width

        image = np.concatenate([image, image, image], axis=1)

        return QImage(image, width, height, bytesPerLine, QImage.Format_RGB888)

    # def hover(self, button):
    #     button.setStyleSheet("QPushButton::hover"
    #                          "{"
    #                          "background-color : lightgreen;"
    #                          "}")

    # def activeButton(self, button):
    #     QSS = """
    #     QPushButton:unchecked:focused {
    #     border: 1px solid;
    #     }
    #     """
    #     button.setStyleSheet(QSS)

    # def activeButton(self, button):
    #     QSS = """
    #     QPushButton: hover {
    #     border: 10px solid;
    #     }
    #         QPushButton: focus:hover{
    #             border: 10px solid;
    #         }
    #     """
    #     button.setStyleSheet(QSS)

    def activeButton(self, button):
        QSS = """
        QPushButton:active {
        border: 1px solid; 
        }
        """
        button.setStyleSheet(QSS)

    # def activeButton(self, button):
    #     QSS = """
    #     QPushButton:not:focus{
    #     border: 4px DarkRed inset;
    #     }
    #     QPushButton:: hover{
    #     background-color: MidnightBlue ;
    #     }
    #     QPushButton: active {
    #     border: 4px MidnightBlue inset;
    #     }
    #     """
    #     button.setStyleSheet(QSS)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # --------------------  Camera initial setup  -----------------------#
    camera = Camera()
    camera.init()
    camera.set_colormode(ueye.IS_CM_SENSOR_RAW8)
    camera.set_aoi(0, 0, 2048, 2048)
    camera.alloc()
    camera.set_exposure(3)
    camera.set_frame_rate(10)
    camera.capture_video()
    control_window = ControlWindow(camera)

    camera_thread = FrameThread(camera, control_window)
    control_window.camera_thread = camera_thread
    camera_thread.start()

    control_window.resize(800, 900)
    control_window.show()

    app.exec_()

    camera_thread.stop()
    # camera_thread.join()
    cv2.destroyAllWindows()
    camera.stop_video()
    camera.exit()
