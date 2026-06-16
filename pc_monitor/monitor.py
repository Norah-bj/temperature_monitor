#!/usr/bin/env python3
"""
Temperature Monitor — PC Side
Reads from Arduino serial -> publishes to MQTT broker on the VPS
Candidate: Mugisha Ineza Nora
"""

import serial
import paho.mqtt.client as mqtt
import time
import sys
import json
from datetime import datetime

# ================================================================
#  CONFIGURATION — edit these lines
# ================================================================
SERIAL_PORT   = "COM7"          # Windows: COM3 / COM4 / COM5 ...
                                 # Linux / Mac: /dev/ttyUSB0  or  /dev/ttyACM0
BAUD_RATE     = 9600

MQTT_BROKER   = "157.173.101.159"
MQTT_PORT     = 1883
MQTT_TOPIC    = "exam/temperature"
MQTT_USERNAME = ""               # leave empty if the broker has no auth
MQTT_PASSWORD = ""

# Prints every raw line received from the Arduino, even ones that get
# discarded. Turn this off once everything works, to keep the demo
# terminal clean.
DEBUG_RAW_LINES = True

# If no line arrives for this many seconds, print a reminder instead of
# sitting there silently — this is what makes a dead serial link obvious
# instead of looking like the script has just frozen.
NO_DATA_WARNING_SECONDS = 8
# ================================================================


# ----------------------------------------------------------------
# MQTT callbacks
# ----------------------------------------------------------------
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"  [MQTT] OK  Connected -> {MQTT_BROKER}:{MQTT_PORT}")
    else:
        print(f"  [MQTT] FAILED to connect (code: {rc})")


def on_disconnect(client, userdata, flags, rc, properties=None):
    if rc != 0:
        print(f"  [MQTT] Unexpected disconnect (rc={rc}). Reconnecting...")


def on_publish(client, userdata, mid, reason_code=None, properties=None):
    pass   # silent — the main loop already reports each send


# ----------------------------------------------------------------
# Connect MQTT
# ----------------------------------------------------------------
print("\n" + "=" * 55)
print("   Embedded Systems Exam — Temperature Monitor")
print("   Candidate: Mugisha Ineza Nora")
print("=" * 55)

# Use the modern callback API (paho-mqtt >= 2.0) to avoid the
# "Callback API version 1 is deprecated" warning. Falls back cleanly
# on older paho-mqtt installs that don't have CallbackAPIVersion yet.
try:
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="exam_monitor_01")
except AttributeError:
    mqtt_client = mqtt.Client(client_id="exam_monitor_01")

if MQTT_USERNAME:
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

mqtt_client.on_connect    = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_publish    = on_publish

print(f"\n  Connecting to MQTT broker {MQTT_BROKER}...")
try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    mqtt_client.loop_start()
    time.sleep(1.5)   # give the callback time to fire
except Exception as e:
    print(f"  [MQTT] Could not connect: {e}")
    sys.exit(1)


# ----------------------------------------------------------------
# Open Serial port
# ----------------------------------------------------------------
print(f"\n  Opening serial port {SERIAL_PORT} @ {BAUD_RATE} baud...")
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=3)
    time.sleep(2)              # Arduino resets on serial connect — wait for it
    ser.reset_input_buffer()
    print(f"  [Serial] OK  Port open\n")
except serial.SerialException as e:
    print(f"  [Serial] FAILED: {e}")
    print("  -> Check: is the Arduino IDE Serial Monitor closed? Is the COM port correct?")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    sys.exit(1)


# ----------------------------------------------------------------
# Live display header
# ----------------------------------------------------------------
print("=" * 55)
print(f"  {'Time':<10}  {'Temp (C)':<12}  {'Humidity':<12}  MQTT")
print("-" * 55)


# ----------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------
readings_count = 0
last_data_time = time.time()
warned_no_data = False

try:
    while True:
        raw = ser.readline()
        line = raw.decode("utf-8", errors="ignore").strip()

        if not line:
            if (time.time() - last_data_time > NO_DATA_WARNING_SECONDS) and not warned_no_data:
                print(f"  [Waiting] No data received for over {NO_DATA_WARNING_SECONDS}s.")
                print("            Check: Arduino uploaded? Correct COM port? Sketch printing BOOT:ready?")
                warned_no_data = True
            continue

        last_data_time = time.time()
        warned_no_data = False

        if DEBUG_RAW_LINES:
            print(f"  [raw] {line}")

        if line.startswith("TEMP:"):
            try:
                parts    = line.split(",")            # ["TEMP:25.3", "HUM:60"]
                temp_str = parts[0].split(":")[1]      # "25.3"
                hum_str  = parts[1].split(":")[1]      # "60"

                temp = float(temp_str)
                hum  = int(hum_str)

                timestamp = datetime.now().strftime("%H:%M:%S")
                readings_count += 1

                payload = json.dumps({
                    "temperature": temp,
                    "humidity":    hum,
                    "unit":        "C",
                    "timestamp":   timestamp,
                    "reading_no":  readings_count
                })

                result = mqtt_client.publish(MQTT_TOPIC, payload, qos=1)
                mqtt_ok = "sent" if result.rc == mqtt.MQTT_ERR_SUCCESS else "failed"

                print(f"  {timestamp:<10}  {temp:<6.1f} C    {hum:<6}%      {mqtt_ok}")

            except (IndexError, ValueError) as e:
                print(f"  [Parse error] '{line}' -> {e}")

        elif line.startswith("ERROR:"):
            print(f"  [Arduino] {line}")

        elif line.startswith("BOOT:"):
            print(f"  [Arduino] {line}")

except KeyboardInterrupt:
    print("\n" + "-" * 55)
    print(f"  Stopped. Total readings sent: {readings_count}")
    ser.close()
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print("  Connections closed. Goodbye!\n")
