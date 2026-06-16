# 🌡️ Temperature Monitor — Embedded Systems Practical Exam

**Candidate:** Mugisha Ineza Nora

A complete embedded system that reads temperature and humidity from a **DHT11 sensor**, displays them on a **16×2 I2C LCD**, sends the readings over **USB Serial** to a PC, and publishes them to an **MQTT broker** on a VPS — with a live web dashboard.

---

## 📐 System Architecture

```
DHT11 Sensor
    │  (single-wire digital signal, pin D2)
    ▼
Arduino UNO ──────► 16×2 I2C LCD  (name on row 1, temp/humidity on row 2)
    │
    │  USB Serial, 9600 baud
    ▼
PC — monitor.py
    │
    │  MQTT over TCP (port 1883)
    ▼
VPS — Mosquitto broker ──► Web Dashboard (MQTT over WebSocket, port 9001)
```

---

## 🔌 Wiring

### DHT11 → Arduino UNO
| DHT11 Pin | Arduino Pin |
|---|---|
| S (signal) | D2 |
| + (power) | 3.3V |
| − (ground) | GND |

### 16×2 I2C LCD → Arduino UNO
| LCD Pin | Arduino Pin |
|---|---|
| VCC | 5V |
| GND | GND |
| SDA | A4 |
| SCL | A5 |

---

## 📁 Repository Structure

```
temperature_monitor/
├── arduino/
│   └── temperature_monitor.ino
├── pc_monitor/
│   └── monitor.py
├── dashboard/
│   └── index.html
├── screenshots/
│   └── (add your screenshots here)
└── README.md
```

---

## 🛠️ Libraries Required

### Arduino IDE (install via Tools → Manage Libraries)
| Library | Author |
|---|---|
| DHT sensor library | Adafruit |
| Adafruit Unified Sensor | Adafruit |
| LiquidCrystal_I2C | Frank de Brabander |

### Python
```bash
pip install pyserial paho-mqtt
```

---

## 🚀 How to Run

### 1. Arduino
1. Open `arduino/temperature_monitor.ino`.
2. `candidateName` is already set to `"Mugisha Ineza Nora"`.
3. Select board **Arduino UNO**, the correct COM port, then **Upload**.
4. Briefly open the Serial Monitor (9600 baud) to confirm you see `BOOT:ready` followed by lines like `TEMP:23.4,HUM:55`, then **close it** — only one program can hold the COM port at a time, and `monitor.py` needs it next.

### 2. PC Monitor
```bash
cd pc_monitor
# open monitor.py and check SERIAL_PORT matches your Arduino's COM port
python monitor.py
```
You should see the MQTT connection confirmation, then the serial port opening, then a printed row roughly every 2 seconds.

### 3. Dashboard (local test)
Open `dashboard/index.html` directly in your browser — no server required for a local check. It connects automatically to `157.173.101.159` on load.

### 4. Dashboard (on the VPS)
```bash
scp dashboard/index.html <your-vps-username>@157.173.101.159:~/dashboard/
ssh <your-vps-username>@157.173.101.159
cd ~/dashboard
nohup python3 -m http.server 8080 &
```
Dashboard URL: `http://157.173.101.159:8080`

---

## 📡 Communication Protocols

| Link | Protocol | Details |
|---|---|---|
| DHT11 → Arduino | Single-wire digital | Pin D2 |
| Arduino → LCD | I2C (TWI) | SDA=A4, SCL=A5, address 0x27 |
| Arduino → PC | UART Serial | USB, 9600 baud |
| PC → VPS Broker | MQTT over TCP | Port 1883, topic `exam/temperature` |
| Browser → Broker | MQTT over WebSocket | Port 9001 |

### Serial format (Arduino → PC)
```
TEMP:25.3,HUM:60
```

### MQTT payload (PC → Broker)
```json
{
  "temperature": 25.3,
  "humidity": 60,
  "unit": "C",
  "timestamp": "14:32:01",
  "reading_no": 42
}
```

### MQTT Topic
```
exam/temperature
```

---

## ⚙️ VPS Broker Setup (Mosquitto) — one time

```bash
sudo apt update && sudo apt install -y mosquitto mosquitto-clients

sudo tee /etc/mosquitto/conf.d/exam.conf > /dev/null <<EOF
listener 1883
allow_anonymous true

listener 9001
protocol websockets
allow_anonymous true
EOF

sudo systemctl restart mosquitto
sudo systemctl enable mosquitto

# Test it:
mosquitto_sub -h localhost -t "exam/temperature"
```

---

## 🩺 Troubleshooting

**Dashboard shows `NaN°C`**
This happens when a payload on the topic isn't the expected JSON — for example a stray test message like `23.0` sent manually, or a leftover retained message from an earlier run. The dashboard in this repo already guards against that: any non-JSON payload is parsed as a plain number instead of breaking, so `NaN` should no longer appear. If it still shows up, check that only one copy of `monitor.py` is running, and clear any retained message with:
```bash
mosquitto_pub -h 157.173.101.159 -t exam/temperature -n -r
```

**`monitor.py` connects but prints nothing**
The script now prints a `[Waiting] No data received...` message after a few seconds of silence, so it's never just a blank, frozen-looking terminal. If you see that warning:
- Make sure the Arduino IDE Serial Monitor is fully closed.
- Confirm the sketch was actually re-uploaded after your last edit.
- `DEBUG_RAW_LINES` is `True` by default in `monitor.py` — it prints every raw line received so you can see exactly what's arriving (or confirm nothing is).
- Double-check `SERIAL_PORT` matches Arduino IDE → Tools → Port.
- If even `BOOT:ready` never shows up, the issue is the serial link itself (cable, port, or board), not the sensor code.

**LCD shows nothing or garbled characters**
Try changing the I2C address in the sketch from `0x27` to `0x3F` — these are the two most common addresses for I2C LCD backpacks.

---

## 🖥️ Screenshots

Add these to `screenshots/` before submitting:
- LCD showing your name and temperature
- Terminal output of `monitor.py`
- Web dashboard with live chart and recent readings
- `mosquitto_sub` terminal receiving JSON messages

---

## 👤 Candidate Information

- **Name:** Mugisha Ineza Nora
- **Exam:** Embedded Systems Practical
- **MQTT Broker:** 157.173.101.159
- **MQTT Topic:** exam/temperature
- **Dashboard URL:** http://157.173.101.159:8080
