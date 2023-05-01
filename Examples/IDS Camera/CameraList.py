from pyueye import ueye
from beautifultable import BeautifulTable


num_cameras = ueye.is_GetNumberOfDevices()
print ("Number of Cameras: " + str(num_cameras))
camera_info_list = ueye.UEYE_CAMERA_LIST(ueye.UEYE_CAMERA_INFO * num_cameras)
camera_info_list.dwCount = num_cameras

ueye.is_GetCameraList(camera_info_list)

table = BeautifulTable()

table.column_headers =["camera_list", "CameraID", "DeviceID", "InUse", "SensorID", "Model", "SN", "Status"]


camera_list = []
for i in range(camera_info_list.dwCount.value):

  # print("camera_list: ", i)
  # print("\tdwCameraID " , camera_info_list.uci[i].dwCameraID.value)
  # print("\tdwDeviceID ", camera_info_list.uci[i].dwDeviceID.value)
  # print("\tdwInUse " , camera_info_list.uci[i].dwInUse.value)
  # print("\tdwSensorID " , camera_info_list.uci[i].dwSensorID.value)
  # print("\tModel " , camera_info_list.uci[i].SerNo.decode('utf-8'))
  # print("\tStatus " , camera_info_list.uci[i].dwStatus.value)

  table.append_row([i,camera_info_list.uci[i].dwCameraID.value,
                    camera_info_list.uci[i].dwDeviceID.value,
                    camera_info_list.uci[i].dwInUse.value,
                    camera_info_list.uci[i].dwSensorID.value,
                    camera_info_list.uci[i].Model.decode('utf-8'),
                    camera_info_list.uci[i].SerNo.decode('utf-8'),
                    camera_info_list.uci[i].dwStatus.value])

print(table)
