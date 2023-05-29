from __future__ import division

import time

import serial  # conda install pyserial


class ArduinoControl(object):
    def __init__(self, timeout=20):  #
        # def __init__(self, com = '/dev/ttyACM0',  timeout = 20):
        print("Connecting to arduino...")
        # self.ser = serial.Serial(com, 9600, timeout=timeout)
        self.ser = serial.Serial("COM3", 9600, timeout=timeout)
        time.sleep(1)
        print(self.ser.read_all())
        # self.ser.reset_output_buffer()

    def close(self):
        self.ser.close()
        print("Closing serial port")

    def writeCmd(self, cmd):
        self.ser.write(cmd.encode())

    def printAll(self):
        print(self.ser.read_all())

    def startLiveView(self):
        cmd = "cl\n"
        self.writeCmd(cmd)
        time.sleep(0.1)
        print(self.ser.read_all())

    def stopLiveView(self):
        cmd = "cb\n"
        self.writeCmd(cmd)
        time.sleep(0.1)
        print(self.ser.read_all())

    def startFocalStack(self):
        cmd = "cf\n"
        self.writeCmd(cmd)
        time.sleep(0.001)
        print(self.ser.read_all())

    def startLimitedFocalStack(self):
        cmd = "ca\n"
        self.writeCmd(cmd)
        time.sleep(0.1)
        print(self.ser.read_all())

    def startOneShot(self):
        cmd = "cs\n"
        self.writeCmd(cmd)
        time.sleep(0.001)
        print(self.ser.read_all())

    def startLimitedOneShot(self):
        cmd = "co\n"
        self.writeCmd(cmd)
        time.sleep(0.1)
        print(self.ser.read_all())

    def startCaptureSingle(self):
        cmd = "cm\n"
        self.writeCmd(cmd)
        time.sleep(0.1)
        print(self.ser.read_all())

    def setNSteps(self, x):
        cmd = "os" + str(x) + "\n"
        # self.writeCmd(str.encode(cmd))
        self.writeCmd(cmd)
        time.sleep(0.1)
        print(self.ser.read_all())

    def setExposure(self, x):
        cmd = "pe" + str(x) + "\n"
        self.writeCmd(cmd)
        time.sleep(0.1)
        print(self.ser.read_all())

    def LightsOn(self):
        cmd = "le1" + "\n"
        self.writeCmd(cmd)
        time.sleep(0.1)
        print(self.ser.read_all())

    def LightsOff(self):
        cmd = "le0" + "\n"
        self.writeCmd(cmd)
        time.sleep(0.1)
        print(self.ser.read_all())

    def LightExposure(self, x):
        cmd = "le" + str(x) + "\n"
        self.writeCmd(cmd)
        time.sleep(0.1)
        print(self.ser.read())

    def setMaxCurrent(self, x):
        cmd = "pc" + str(x) + "\n"
        self.writeCmd(cmd)
        time.sleep(1)
        print(self.ser.read_all())

    def setUseLED(self, x):
        cmd = "pl" + str(x) + "\n"
        self.writeCmd(cmd)
        time.sleep(1)
        print(self.ser.read_all())

    def setExposureProj(self, x):
        cmd = "pp" + str(x) + "\n"
        self.writeCmd(cmd)
        time.sleep(1)
        print(self.ser.read_all())

    def setStep(self, x):
        cmd = "oc" + str(x) + "\n"
        self.writeCmd(cmd)

    def stepForward(self):
        cmd = "of\n"
        self.writeCmd(cmd)

    def stepBackward(self):
        cmd = "ob\n"
        self.writeCmd(cmd)

    def upperOptoLimit(self, x):
        cmd = "ou" + str(x) + "\n"
        self.writeCmd(cmd)

    def lowerOptoLimit(self, x):
        cmd = "ol" + str(x) + "\n"
        self.writeCmd(cmd)

    def advanceProjector(self):
        cmd = "dp\n"
        self.writeCmd(cmd)

    def advanceCamera(self):
        cmd = "cr\n"
        self.writeCmd(cmd)

    def reportValues(self):
        cmd = "R\n"
        self.writeCmd(cmd)
        time.sleep(0.2)
        self.printAll()


if __name__ == "__main__":
    ard = ArduinoControl()
    ard.startLiveView()
    time.sleep(10)
    ard.stopLiveView()
    ard.stepForward()
    ard.reportValues()
    time.sleep(2)
    ard.printAll()
    ard.close()
