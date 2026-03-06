import json
import threading
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import paho.mqtt.client as mqtt
import serial
import re


BROKER   = "localhost"   
PORT     = "COM5"          
TOPIC    = "sensors/data"   
MAX_PTS  = 300         
INTERVAL = 100
BAUD     = 115200

RPM_MAX = 7000

timestamps = deque(maxlen=MAX_PTS)
rpm = deque(maxlen=MAX_PTS)

def parse_line(line):
    rpm = re.search(r"RPM:\s*(\d+\.?\d*)", line)

    if rpm:
        return float(rpm.group(1))
    return None

lock=threading.Lock()

counter = 0

def start_serial():
    global counter
    ser = serial.Serial(PORT, BAUD, timeout=1)
    print(f"Connected to {PORT} at {BAUD} baud")

    while True:
        try:
            line = ser.readline().decode("utf-8").strip()
            if not line:
                continue

            result = parse_line(line)
            if result is None:
                continue

            with lock:
                timestamps.append(counter)
                rpm.append(result)
                counter += 1

        except (UnicodeDecodeError) as e:
            print(f"bad payload: {e}")
        except serial.SerialException as e:
            print(f"serial error: {e}")
            break


serial_thread = threading.Thread(target=start_serial, daemon=True)
serial_thread.start()

#Plotting
fig, ax1 = plt.subplots(1, 1)

# #Plot animation
# def update(frame):

#     with lock:
#         xs = list(timestamps)
#         ys1 = list(rpm)

#     if(len(xs) < 2):
#         return

#     ax1.clear()
#     ax1.plot(xs, ys1, label="RPM", color='red')
#     ax1.set_title("Vehicle RPM")
#     ax1.set_xlabel("Time")
#     ax1.set_ylabel("RPM")
#     fig.tight_layout()

# ani = animation.FuncAnimation(fig, update, interval=INTERVAL, cache_frame_data=False)
# plt.show()

def update(frame):

    with lock:
        current_rpm = rpm[-1] if rpm else 0

    current_rpm = min(current_rpm, RPM_MAX)
    remaining   = RPM_MAX - current_rpm
    if current_rpm < 2000:
        colors=["green", "lightgrey"]
    elif current_rpm < 5000:
        colors=["yellow", "lightgrey"]
    else:
        colors=["red", "lightgrey"]
    ax1.clear()
    ax1.pie(
        [current_rpm, remaining],
        labels=[f"RPM: {current_rpm:.0f}", f"Remaining: {remaining:.0f}"],
        colors=colors,
        startangle=90,
        counterclock=False
    )
    ax1.set_title("Vehicle RPM")

ani = animation.FuncAnimation(fig, update, interval=INTERVAL, cache_frame_data=False)
plt.show()
