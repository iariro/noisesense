#!/usr/bin/python3

import pyaudio
import numpy as np
import sys
import datetime
import ambient

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

# amp to db
def to_db(x, base=1):
    y=20*np.log10(x/base)
    return y

# main loop
def main():
    cnt = [0] * 3
    now2 = None
    ambi = ambient.Ambient(11405, "29f2d72e4d415732")
    while True:
        now = datetime.datetime.now()
        if (now2 is not None) and (now.minute // interval != now2.minute // interval):
            try:
                cnts = {}
                if cnt[0] > 0:
                    cnts['d5'] = cnt[0]
                if cnt[1] > 0:
                    cnts['d6'] = cnt[1]
                if cnt[2] > 0:
                    cnts['d7'] = cnt[2]
                if len(cnts) > 0:
                    ambi.send(cnts)
            except:
                pass
            cnt = [0] * 3

        stream = p.open(format = FORMAT,
                        channels = CHANNELS,
                        rate = SAMPLING_RATE,
                        input = True,
                        frames_per_buffer = CHUNK,
                        input_device_index = INPUT_DEVICE_INDEX
                )

        # get specified range of data. size of data equals (CHUNK * (SAMPLING_RATE / CHUNK) * RECORD_SECONDS)
        data = np.empty(0)
        for i in range(0, int(SAMPLING_RATE / CHUNK * RECORD_SECONDS)):
            elm = stream.read(CHUNK, exception_on_overflow = False)
            elm = np.frombuffer(elm, dtype="int16")/float((np.power(2,16)/2)-1)
            data = np.hstack([data, elm])
        # calc RMS
        rms = np.sqrt(np.mean([elm * elm for elm in data]))
        # RMS to db
        db = to_db(rms, 20e-6)
        stream.close()

        if 55 <= db < 60:
            cnt[0] += 1
        if 60 <= db < 65:
            cnt[1] += 1
        if 65 <= db:
            cnt[2] += 1
        now2 = now

try:
    main()
except KeyboardInterrupt:
    pass
finally:
    p.terminate()
