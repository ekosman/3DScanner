# **********************************************************************
#  FILENAME :    endlessfreeze.py
#
#  DESCRIPTION:  code conversion from c++ to python
#                Short test routine to initalize a ueye camera and capture
#                images with is_freezevideo() in a loop
#
#  NOTES :       These code was written for testing purposes only!
#
#
#  AUTHOR :      Marko Schimon     START DATE :    21 November 2017
#
#
#  VERSION      DATE            WHO     DETAIL
#  V1.0         11/21/2017      MSH
# ***********************************************************************

import msvcrt
from time import sleep
from pyueye import ueye
import time

hcam = ueye.HIDS(0)

nRet = ueye.int(0)
iWidth  = ueye.int(0)                           #will be properly initialized with the sensor info struct information
iHeight = ueye.int(0)                           #will be properly initialized with the sensor info struct information

iColorMode = ueye.IS_CM_BGRA8_PACKED            #if changed, please also check if the bit per pixel value "bpp" needs to be adjusted to fit mem alloc later IS_CM_SENSOR_RAW10
bpp = ueye.int(32)                              #set according to the color format above

dblFrameRateToSet = ueye.double(0.0)           # if set to 0.0 the max possible fps will be set

pid = ueye.c_int(0)
nMemid = ueye.c_int(0)
pc_mem = ueye.c_mem_p()
pBuffer = ueye.c_mem_p()

sensorinfo = ueye.SENSORINFO()
camerainfo = ueye.CAMINFO()

SINGLEIMAGECAPTURE = ueye.bool(True)           # set "true" to ignore the endless part of the demo...
SAVEANIMAGE = ueye.bool(True)                  # set "true" to save the last image at the end of the demo
bAOI_active = ueye.bool(False)                  # set active to use the AOI defined below

# AOI configuration that gets used when bAOI_active is TRUE
iAOI_Pos_X = ueye.int(100)
iAOI_Pos_Y = ueye.int(100)
iAOI_Width = ueye.int(32)
iAOI_Height = ueye.int(4)

nRet = ueye.is_InitCamera(hcam, None)
print("InitCamera returned " + str(nRet))
if nRet != ueye.IS_SUCCESS:
    print("Failed to open camera.\n")

nRet = ueye.is_GetCameraInfo(hcam, camerainfo)
if nRet != ueye.IS_SUCCESS:
    print("Failed to retrieve camera info.\n")
nRet = ueye.is_GetSensorInfo(hcam, sensorinfo)
if nRet != ueye.IS_SUCCESS:
    print("Failed to retrieve sensor info.\n")

print("\tSensor model " + sensorinfo.strSensorName.decode('utf-8'))
print("\tCamera serial no " + camerainfo.SerNo.decode('utf-8'))
print("\tCamera serial no " + camerainfo.SerNo.decode('utf-8'))

iWidth =  sensorinfo.nMaxWidth
iHeight = sensorinfo.nMaxHeight
print("\tImage size is  "+ str(iWidth) + " x " + str(iHeight))

nRet = ueye.is_SetColorMode(hcam, iColorMode)
# print ("SetColorMode returned \s", nRet)
print ("SetColorMode returned " + str(nRet))

param = ueye.INT(0)
nRet = ueye.is_ParameterSet(hcam, ueye.IS_PARAMETERSET_CMD_LOAD_EEPROM, param, ueye.sizeof(param))

#---------------------------------------------------------
# Pixel clock settings
#---------------------------------------------------------

nRange = (ueye.int * 3)()
#ZeroMemory(nRange, sizeof(nRange));
nPixelClock = ueye.UINT()
nPixelClockDefault  = ueye.UINT()
nPixelClockMin = ueye.UINT()
nPixelClockMax  = ueye.UINT()
nPixelClockInc = ueye.UINT()
nEnable = ueye.UINT()

# Get pixel clock range
nRet = ueye.is_PixelClock(hcam, ueye.IS_PIXELCLOCK_CMD_GET_RANGE, nRange, ueye.sizeof(nRange))
if nRet == ueye.IS_SUCCESS:
    nPixelClockMin = nRange[0]
    nPixelClockMax = nRange[1]
    nPixelClockInc = nRange[2]

print("IS_PIXELCLOCK_CMD_GET_RANGE returned " + str(nRet)+ ".")
print("\tmin = " + str(nPixelClockMin) + ", max = " + str(nPixelClockMax) + ", inc= " + str(nPixelClockInc))

# Get default pixel clock
nRet = ueye.is_PixelClock(hcam, ueye.IS_PIXELCLOCK_CMD_GET_DEFAULT, nPixelClockDefault, ueye.sizeof(nPixelClockDefault))
print("IS_PIXELCLOCK_CMD_GET_DEFAULT returned " + str(nRet)+ ".")
print("\tDefault pixel clock is = " + str(nPixelClockDefault))

# Set default pixel clock
nRet = ueye.is_PixelClock(hcam, ueye.IS_PIXELCLOCK_CMD_SET, nPixelClockDefault, ueye.sizeof(nPixelClockDefault))
print("IS_PIXELCLOCK_CMD_SET returned " + str(nRet)+ ".")
print("\ttried to set pixel clock to = " + str(nPixelClockDefault))

# Get current pixel clock
nRet = ueye.is_PixelClock(hcam, ueye.IS_PIXELCLOCK_CMD_GET, nPixelClock, ueye.sizeof(nPixelClock))
print("IS_PIXELCLOCK_CMD_GET returned " + str(nRet)+ ".")
print("\tThe current pixel clock is =  " + str(nPixelClock))

#---------------------------------------------------------
# Memory Allocation
# ---------------------------------------------------------

nRet = ueye.is_AllocImageMem(hcam, iWidth, iHeight, bpp, pc_mem, pid)
print("is_AllocImageMem returned " + str(nRet)+ ".")
print("\tpc_mem = " + str(pc_mem) +", pid = " + str(pid))

nRet = ueye.is_SetImageMem(hcam, pc_mem, pid)
print("SetImageMem returned " + str(nRet)+ ".")

#---------------------------------------------------------
# AOI Settings (if bAOI_active = true)
#---------------------------------------------------------

if bAOI_active:
    print("AOI is activated!")
    rectAOI = ueye.IS_RECT()
    rectAOI.s32X = iAOI_Pos_X
    rectAOI.s32Y = iAOI_Pos_Y
    rectAOI.s32Width = iAOI_Width
    rectAOI.s32Height = iAOI_Width

    nRet = ueye.is_AOI(hcam, ueye.IS_AOI_IMAGE_SET_AOI, rectAOI, ueye.sizeof(rectAOI))
    print("IS_AOI_IMAGE_SET_AOI returned " + str(nRet) + ".")
    print("IS_AOI_IMAGE_SET_AOI tried to set the following AOI:")
    print("\tPos(X/Y) = " + str(rectAOI.s32X) +" / " + str(rectAOI.s32Y) +", Size(X/Y) = " + str(rectAOI.s32Width) +" / " + str(rectAOI.s32Height))

    nRet = ueye.is_AOI(hcam, ueye.IS_AOI_IMAGE_GET_AOI, rectAOI, ueye.sizeof(rectAOI))
    print("IS_AOI_IMAGE_GET_AOI returned " + str(nRet) + ".")
    print("IS_AOI_IMAGE_GET_AOI verified the following AOI:")
    print("\tPos(X/Y) = " + str(rectAOI.s32X) +" / " + str(rectAOI.s32Y) +", Size(X/Y) = " + str(rectAOI.s32Width) +" / " + str(rectAOI.s32Height))


#---------------------------------------------------------
# FPS and Frametiming (AOI and Pixelclock need to be set first!)
#---------------------------------------------------------

dblMinFrameTime = ueye.double(0.0)
dblMaxFrameTime = ueye.double(0.0)
dblFrameTimeInterval = ueye.double(0.0)
dblNewFrameRate = ueye.double(0.0)
dblframerate = ueye.double(0.0)

nRet = ueye.is_GetFrameTimeRange(hcam, dblMinFrameTime, dblMaxFrameTime, dblMinFrameTime)
print("is_GetFrameTimeRange returned " + str(nRet) + ".")
print("\tMin = " + str(dblMinFrameTime) +", Max = " + str(dblMaxFrameTime) +", interval = " + str(dblFrameTimeInterval))

if dblFrameRateToSet == 0.0:
    nRet = ueye.is_SetFrameRate(hcam, 1.0 / dblMinFrameTime, dblNewFrameRate)

else:
    nRet = ueye.is_SetFrameRate(hcam, dblFrameRateToSet, dblNewFrameRate)

print("SetFrameRate returned " + str(nRet) + ".")
print("\tNew framerate = " + str(dblNewFrameRate))


nRet = ueye.is_SetFrameRate (hcam, ueye.IS_GET_FRAMERATE, dblframerate)
print("GetFrameRate returned " + str(nRet) + ".")
print("\tApplied framerate = " + str(dblframerate))

# ---------------------------------------------------------
# The IMAGE Aquisition Part
# ---------------------------------------------------------

intRunCounter = ueye.int(0)
intErrCounter = ueye.int(0)

print("Start Capture Images Process")

if SINGLEIMAGECAPTURE:

    print("SINGLE IMAGE CAPTURE.....")

    # prepare 13 Mpixel snapshots
    nRet = ueye.is_SetExternalTrigger(hcam, ueye.IS_SET_TRIGGER_SOFTWARE)
    print("is_SetExternalTrigger returned " + str(nRet) + ".")

    count = ueye.UINT()

    nRet = ueye.is_ImageFormat(hcam, ueye.IMGFRMT_CMD_GET_NUM_ENTRIES, count, ueye.sizeof(count))
    format_list = ueye.IMAGE_FORMAT_LIST(ueye.IMAGE_FORMAT_INFO * count.value)
    format_list.nSizeOfListEntry = ueye.sizeof(ueye.IMAGE_FORMAT_INFO)
    format_list.nNumListElements = count.value
    nRet = ueye.is_ImageFormat(hcam, ueye.IMGFRMT_CMD_GET_LIST, format_list, ueye.sizeof(format_list))

    # Search a 13Mpixel format (or apply format 34 - that is the 13MPixel format)
    formatInfo = ueye.IMAGE_FORMAT_INFO

    # print("formatlist:", format_list)
    # print("formatInfo:", formatInfo)


    for i, formatInfo in enumerate(format_list.FormatInfo):

        # formatInfo = formatInfo[i]
        width = ueye.int(formatInfo.nWidth)
        height = ueye.int(formatInfo.nHeight)

        if ((width * height) > 12800000):

            #  Allocate image mem for current format, set format
            nRet = ueye.is_FreeImageMem(hcam, pc_mem, pid)
            print("is_FreeImageMem returned " + str(nRet) + ".")

            nRet = ueye.is_AllocImageMem(hcam, width, height, bpp, pc_mem, pid)
            print("is_AllocImageMem returned " + str(nRet) + ".")
            nRet = ueye.is_SetImageMem(hcam, pc_mem, pid)
            print("is_SetImageMem returned " + str(nRet) + ".")
            nRet = ueye.is_ImageFormat(hcam, ueye.IMGFRMT_CMD_SET_FORMAT, ueye.int(formatInfo.nFormatID), 4)
            print("is_ImageFormat returned " + str(nRet) + ".")
            print("formatInfo.nFormatID", formatInfo.nFormatID)

    # nRet = ueye.is_ImageFormat(hcam, ueye.IMGFRMT_CMD_SET_FORMAT, ueye.int(34), 4)
    # print("is_ImageFormat returned " + str(nRet) + ".")

    nRet = ueye.is_SetTimeout(hcam, ueye.IS_TRIGGER_TIMEOUT, ueye.UINT(200))
    print("is_SetTimeout returned " + str(nRet) + ".")
    nRet = ueye.is_FreezeVideo(hcam, ueye.IS_WAIT)
    print("is_FreezeVideo returned " + str(nRet) + ".")

    # ---------------------------------------------------------
    # OPTIONAL:  saving an image to e.g. "Test Memory Alloc Parameters"
    # ---------------------------------------------------------
    if SAVEANIMAGE:
        print("save image")
            # FileParams = ueye.IMAGE_FILE_PARAMS()
            # FileParams.pwchFileName = "C:\python-test-image.png"
            # FileParams.nFileType = ueye.IS_IMG_PNG
            # FileParams.ppcImageMem = pc_mem
            # FileParams.pnImageID = pid
            # print("FileParams finished")
            #
            # nRet = ueye.is_ImageFile(hcam, ueye.IS_IMAGE_FILE_CMD_SAVE, FileParams, ueye.sizeof(FileParams))
            # print("is_ImageFile returned " + str(nRet) + ".")
        time.sleep(5)
        # Test Bild speichern
        FileParams = ueye.IMAGE_FILE_PARAMS()
        FileParams.pwchFileName = "Endlessfreeze.png"
        FileParams.nFileType = ueye.IS_IMG_PNG
        FileParams.ppcImageMem = None
        FileParams.pnImageID = None
        nRet = ueye.is_ImageFile(hcam, ueye.IS_IMAGE_FILE_CMD_SAVE, FileParams, ueye.sizeof(FileParams))
        print("is_ImageFile returned: {}".format(nRet))

else:
    # a key press (ENTER) of the user will exit the test
    print('(Hit any key to exit)')
    while not msvcrt.kbhit():
        pass
        sleep(0.5)

        #intRunCounter += 1
        print("intRunCounter" + str(intRunCounter))
        print("intErrCounter" + str(intErrCounter))
        nRet = ueye.is_FreezeVideo(hcam, ueye.IS_DONT_WAIT)
        print("is_FreezeVideo returned " + str(nRet) + ".")
        if nRet != ueye.IS_SUCCESS:
            #print("is_FreezeVideo returned " + str(nRet) + ".")
            intErrCounter += 1
            ueye.is_FreeImageMem(hcam, pc_mem, pid)
            ueye.is_ExitCamera(hcam)

        intRunCounter += 1


        if (camerainfo.Type == ueye.IS_CAMERA_TYPE_UEYE_ETH) or \
                (camerainfo.Type == ueye.IS_CAMERA_TYPE_UEYE_ETH_SE) or \
                (camerainfo.Type == ueye.IS_CAMERA_TYPE_UEYE_ETH_SE_R4) or \
                (camerainfo.Type == ueye.IS_CAMERA_TYPE_UEYE_ETH_RE) or \
                (camerainfo.Type == ueye.IS_CAMERA_TYPE_UEYE_ETH_CP) or \
                (camerainfo.Type == ueye.IS_CAMERA_TYPE_UEYE_ETH_CP_R2) or \
                (camerainfo.Type == ueye.IS_CAMERA_TYPE_UEYE_ETH_LE):
            #struct for ETH cameras
            nDeviceId = ueye.UINT(1001)
            deviceInfo = ueye.UEYE_ETH_DEVICE_INFO()
            cameratype = "ETH device: "
        else:
            # struct for USB cameras
            nDeviceId = ueye.UINT(1)
            deviceInfo = ueye.IS_DEVICE_INFO()
            cameratype = "USB device: "

        nRet = ueye.is_DeviceInfo(nDeviceId | ueye.IS_USE_DEVICE_ID, ueye.IS_DEVICE_INFO_CMD_GET_DEVICE_INFO, deviceInfo,
                              ueye.sizeof(deviceInfo))
        if nRet != ueye.IS_SUCCESS:
            print("Get DeviceInfo returned successfully: " + str(nRet))
        print("Current Temperatur " + cameratype + str(deviceInfo.infoDevHeartbeat.wTemperature / 16.0))




#---------------------------------------------------------
# Free allocated memory and camera handle before quiting the programm
#---------------------------------------------------------


nRet = ueye.is_FreeImageMem(hcam, pc_mem, pid)
print("is_FreeImageMem returned " + str(nRet) + ".")
nRet = ueye.is_ExitCamera(hcam)
print("is_ExitCamera returned " + str(nRet) + ".")
