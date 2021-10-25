import pyaudio
p = pyaudio.PyAudio()

for index in range(0, p.get_device_count()):
    device_info = p.get_device_info_by_index(index)
    print("DEVICE_INDEX:{}, DEVICE_NAME:{}".format(device_info["index"], device_info["name"]))

p.terminate()
