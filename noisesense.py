#!/usr/bin/python3

import pyaudio
import numpy as np
import sys
import datetime
import ambient
import requests
import wave

def line_notify(cnt):
    token = "nPQEoC190nfvydJRbQmY75SY00Ygvt0CxsaXWoLTUUH"
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": "Bearer " + token}
    payload = {"message": '80dBを{}回記録しました'.format(cnt)}
    requests.post(url, headers=headers, data=payload)

# check args
if (len(sys.argv) < 2) or (not sys.argv[1].isdecimal()):
    print("Please specify input_device_index in integer")
    sys.exit(-1)

interval = 1

p = pyaudio.PyAudio()

# set prams
INPUT_DEVICE_INDEX = int(sys.argv[1])
CHUNK = 2 ** 10 # 1024
FORMAT = pyaudio.paInt16
CHANNELS = int(p.get_device_info_by_index(INPUT_DEVICE_INDEX)["maxInputChannels"])
SAMPLING_RATE = int(p.get_device_info_by_index(INPUT_DEVICE_INDEX)["defaultSampleRate"])
RECORD_SECONDS = 1

WAV_DIR = '/home/pi/public_html/flask/noisesense/static/wav'

# amp to db
def to_db(x, base=1):
    y=20*np.log10(x/base)
    return y

# main loop
def main():
    cnt = [0] * 6
    wave_data = []
    now2 = None
    ambi = ambient.Ambient(43750, "d4af625dc13007b1")
    while True:
        now = datetime.datetime.now()
        if (now2 is not None) and (now.minute // interval != now2.minute // interval):
            try:
                cnts = {}
                for i in range(5):
                    if cnt[i] > 0:
                        d = 2 + i
                        cnts['d{}'.format(d)] = cnt[i]
                if len(cnts) > 0:
                    ambi.send(cnts)
                if cnts[5] > 0:
                    line_notify(cnt[5])
            except:
                pass
            cnt = [0] * 6

        stream = p.open(format = FORMAT,
                        channels = CHANNELS,
                        rate = SAMPLING_RATE,
                        input = True,
                        frames_per_buffer = CHUNK,
                        input_device_index = INPUT_DEVICE_INDEX
                )

        # get specified range of data. size of data equals (CHUNK * (SAMPLING_RATE / CHUNK) * RECORD_SECONDS)
        data = np.empty(0)

        wave_write = (now2 is not None) and (now.minute != now2.minute) and now.minute == 0

        if wave_write:
            wavFile = wave.open('{}/{:02}.wav'.format(WAV_DIR, now.hour), 'wb')
            wavFile.setnchannels(CHANNELS)
            wavFile.setsampwidth(p.get_sample_size(FORMAT))
            wavFile.setframerate(SAMPLING_RATE)
            wavFile.writeframes(b"".join(wave_data)) #Python3用
            wavFile.close()

            wave_data = []

        wave_data_new = []
        for i in range(0, int(SAMPLING_RATE / CHUNK * RECORD_SECONDS)):
            elm = stream.read(CHUNK, exception_on_overflow = False)
            wave_data_new.append(elm)
            elm = np.frombuffer(elm, dtype="int16")/float((np.power(2,16)/2)-1)
            data = np.hstack([data, elm])
        # calc RMS
        rms = np.sqrt(np.mean([elm * elm for elm in data]))
        # RMS to db
        db = to_db(rms, 20e-6)
        stream.close()

        # 55-60 / 60-65 / 65-70 / 70-
        if db >= 55:
            if db > 80:
                db = 80
            cnt[int((db - 55) // 5)] += 1
            wave_data += wave_data_new

        now2 = now

try:
    main()
except KeyboardInterrupt:
    pass
finally:
    p.terminate()
