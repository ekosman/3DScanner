from pyueye import ueye

hcam = ueye.HIDS(0)
pccmem = ueye.c_mem_p()
memID = ueye.c_int(0)
ueye.is_InitCamera(hcam, None)
sensorinfo = ueye.SENSORINFO()
ueye.is_GetSensorInfo(hcam, sensorinfo)
ueye.is_AllocImageMem(
    hcam, sensorinfo.nMaxWidth, sensorinfo.nMaxHeight, 24, pccmem, memID
)
ueye.is_SetImageMem(hcam, pccmem, memID)
nret = ueye.is_FreezeVideo(hcam, ueye.IS_WAIT)
print(nret)
FileParams = ueye.IMAGE_FILE_PARAMS()
FileParams.pwchFileName = "d:\python-test-image.bmp"
FileParams.nFileType = ueye.IS_IMG_BMP
FileParams.ppcImageMem = None
FileParams.pnImageID = None
nret = ueye.is_ImageFile(
    hcam, ueye.IS_IMAGE_FILE_CMD_SAVE, FileParams, ueye.sizeof(FileParams)
)
print(nret)
ueye.is_FreeImageMem(hcam, pccmem, memID)
ueye.is_ExitCamera(hcam)
