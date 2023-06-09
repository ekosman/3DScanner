# ===========================================================================#
#                                                                           #
#  Copyright (C) 2006 - 2018                                                #
#  IDS Imaging GmbH           q                                              #
#  Dimbacherstr. 6-8                                                        #
#  D-74182 Obersulm-Willsbach                                               #
#                                                                           #
#  The information in this document is subject to change without            #
#  notice and should not be construed as a commitment by IDS Imaging GmbH.  #
#  IDS Imaging GmbH does not assume any responsibility for any errors       #
#  that may appear in this document.                                        #
#                                                                           #
#  This document, or source code, is provided solely as an example          #
#  of how to utilize IDS software libraries in a sample application.        #
#  IDS Imaging GmbH does not assume any responsibility for the use or       #
#  reliability of any portion of this document or the described software.   #
#                                                                           #
#  General permission to copy or modify, but not for profit, is hereby      #
#  granted,  provided that the above copyright notice is included and       #
#  reference made to the fact that reproduction privileges were granted     #
#  by IDS Imaging GmbH.                                                     #
#                                                                           #
#  IDS cannot assume any responsibility for the use or misuse of any        #
#  portion of this software for other than its intended diagnostic purpose  #
#  in calibrating and testing IDS manufactured cameras and software.        #
#                                                                           #
# ===========================================================================#

# Developer Note: I tried to let it as simple as possible.
# Therefore there are no functions asking for the newest driver software or freeing memory beforehand, ect.
# This program is solely here to show one of the simplest ways to interact with an IDS Camera through the uEye API.
# (XS Cameras are not supported)
# ---------------------------------------------------------------------------------------------------------------------------------------


import cv2
import numpy as np

# Libraries
from pyueye import ueye

# ---------------------------------------------------------------------------------------------------------------------------------------

# Variables
hCam = ueye.HIDS(
    0
)  # 0: first available camera;  1-254: The camera with the specified camera ID
sInfo = ueye.SENSORINFO()
cInfo = ueye.CAMINFO()
pcImageMemory = ueye.c_mem_p()
MemID = ueye.int()
rectAOI = ueye.IS_RECT()
pitch = ueye.INT()
nBitsPerPixel = ueye.INT(
    24
)  # 24: bits per pixel for colormode; Take 8 bits per pixel for monochrome
channels = 3  # 3: channels for colormode(RGB); Take 1 channel for monochrome
m_nColorMode = ueye.INT()  # Y8/RGB16/RGB24/REG32
bytes_per_pixel = int(nBitsPerPixel / 8)
# ---------------------------------------------------------------------------------------------------------------------------------------
print("START")
print()


# starts the driver and establishes the connection to the camera
nRet = ueye.is_InitCamera(hCam, None)
if nRet != ueye.IS_SUCCESS:
    print("is_InitCamera ERROR")

# reads out the data hard-coded in the non-volatile camera memory and writes it to the data structure that cInfo points to
nRet = ueye.is_GetCameraInfo(hCam, cInfo)
if nRet != ueye.IS_SUCCESS:
    print("is_GetCameraInfo ERROR")

# you can query additional information about the sensor type used in the camera
nRet = ueye.is_GetSensorInfo(hCam, sInfo)
if nRet != ueye.IS_SUCCESS:
    print("is_GetSensorInfo ERROR")

nRet = ueye.is_ResetToDefault(hCam)
if nRet != ueye.IS_SUCCESS:
    print("is_ResetToDefault ERROR")

# Set display mode to DIB
nRet = ueye.is_SetDisplayMode(hCam, ueye.IS_SET_DM_DIB)

# set the right colormode
if int.from_bytes(sInfo.nColorMode.value, byteorder="big") == ueye.IS_COLORMODE_BAYER:
    # setup the color depth to the current windows setting
    ueye.is_GetColorDepth(hCam, nBitsPerPixel, m_nColorMode)
    bytes_per_pixel = int(nBitsPerPixel / 8)
    print(
        "IS_COLORMODE_BAYER: ",
    )
    print("\tm_nColorMode: \t\t", m_nColorMode)
    print("\tnBitsPerPixel: \t\t", nBitsPerPixel)
    print("\tbytes_per_pixel: \t\t", bytes_per_pixel)
    print()

elif (
    int.from_bytes(sInfo.nColorMode.value, byteorder="big") == ueye.IS_COLORMODE_CBYCRY
):
    # for color camera models use RGB32 mode
    m_nColorMode = ueye.IS_CM_BGRA8_PACKED
    nBitsPerPixel = ueye.INT(32)
    bytes_per_pixel = int(nBitsPerPixel / 8)
    print(
        "IS_COLORMODE_CBYCRY: ",
    )
    print("\tm_nColorMode: \t\t", m_nColorMode)
    print("\tnBitsPerPixel: \t\t", nBitsPerPixel)
    print("\tbytes_per_pixel: \t\t", bytes_per_pixel)
    print()

elif (
    int.from_bytes(sInfo.nColorMode.value, byteorder="big")
    == ueye.IS_COLORMODE_MONOCHROME
):
    # for color camera models use RGB32 mode
    m_nColorMode = ueye.IS_CM_MONO8
    nBitsPerPixel = ueye.INT(8)
    bytes_per_pixel = int(nBitsPerPixel / 8)
    print(
        "IS_COLORMODE_MONOCHROME: ",
    )
    print("\tm_nColorMode: \t\t", m_nColorMode)
    print("\tnBitsPerPixel: \t\t", nBitsPerPixel)
    print("\tbytes_per_pixel: \t\t", bytes_per_pixel)
    print()

else:
    # for monochrome camera models use Y8 mode
    m_nColorMode = ueye.IS_CM_MONO8
    nBitsPerPixel = ueye.INT(8)
    bytes_per_pixel = int(nBitsPerPixel / 8)
    print("else")

# can be used to set the size and position of an "area of interest"(AOI) within an image
nRet = ueye.is_AOI(hCam, ueye.IS_AOI_IMAGE_GET_AOI, rectAOI, ueye.sizeof(rectAOI))
if nRet != ueye.IS_SUCCESS:
    print("is_AOI ERROR")

width = rectAOI.s32Width
height = rectAOI.s32Height

# prints out some information about the camera and the sensor
print("Camera model:\t\t", sInfo.strSensorName.decode("utf-8"))
print("Camera serial no.:\t", cInfo.SerNo.decode("utf-8"))
print("Maximum image width:\t", width)
print("Maximum image height:\t", height)
print()

# ---------------------------------------------------------------------------------------------------------------------------------------

# allocates an image memory for an image having its dimensions defined by width and height and its color depth defined by nBitsPerPixel
nRet = ueye.is_AllocImageMem(hCam, width, height, nBitsPerPixel, pcImageMemory, MemID)
if nRet != ueye.IS_SUCCESS:
    print("is_AllocImageMem ERROR")
else:
    # makes the specified image memory the active memory
    nRet = ueye.is_SetImageMem(hCam, pcImageMemory, MemID)
    if nRet != ueye.IS_SUCCESS:
        print("is_SetImageMem ERROR")
    else:
        # set the desired color mode
        nRet = ueye.is_SetColorMode(hCam, m_nColorMode)


# activates the camera's live video mode (free run mode)
nRet = ueye.is_CaptureVideo(hCam, ueye.IS_DONT_WAIT)
if nRet != ueye.IS_SUCCESS:
    print("is_CaptureVideo ERROR")

# enables the queue mode for existing image memory sequences
nRet = ueye.is_InquireImageMem(
    hCam, pcImageMemory, MemID, width, height, nBitsPerPixel, pitch
)
if nRet != ueye.IS_SUCCESS:
    print("is_InquireImageMem ERROR")
else:
    print("Press q to leave the programm")

# ---------------------------------------------------------------------------------------------------------------------------------------

# continuous image display
while nRet == ueye.IS_SUCCESS:
    # in order to display the image in an OpenCV window we need to...
    # ...extract the data of our image memory
    array = ueye.get_data(
        pcImageMemory, width, height, nBitsPerPixel, pitch, copy=False
    )

    # bytes_per_pixel = int(nBitsPerPixel / 8)

    # ...reshape it in an numpy array...
    frame = np.reshape(array, (height.value, width.value, bytes_per_pixel))

    # resize the image by a half
    frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

    # ---------------------------------------------------------------------------------------------------------------------------------------
    # Include image data processing here

    # ---------------------------------------------------------------------------------------------------------------------------------------

    # ...and finally display it
    cv2.imshow("SimpleLive_Python_uEye_OpenCV", frame)

    # press q if you want to end the loop
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
# ---------------------------------------------------------------------------------------------------------------------------------------

# releases an image memory that was allocated using is_AllocImageMem() and removes it from the driver management
ueye.is_FreeImageMem(hCam, pcImageMemory, MemID)

# disables the hCam camera handle and releases the data structures and memory areas taken up by the uEye camera
ueye.is_ExitCamera(hCam)

# destroys the OpenCv windows
cv2.destroyAllWindows()

print()
print("END")
