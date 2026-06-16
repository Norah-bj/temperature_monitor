// ============================================================
//  Temperature Monitor — Embedded Systems Practical Exam
//  Hardware : DHT11 on D2  |  16x2 I2C LCD (0x27) on A4/A5
//  Candidate: Mugisha Ineza Nora
// ============================================================

#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>

// ---------- Hardware config ----------
#define DHT_PIN   2
#define DHT_TYPE  DHT11

LiquidCrystal_I2C lcd(0x27, 16, 2);   // change to 0x3F if the screen stays blank
DHT dht(DHT_PIN, DHT_TYPE);

// ---------- Candidate name ----------
// Longer than 16 characters -> scrolls automatically on row 1
String candidateName = "Mugisha Ineza Nora";

// ---------- Scrolling state ----------
int  scrollPos   = 0;
bool needsScroll = false;

// ---------- Timing ----------
unsigned long lastScroll   = 0;
unsigned long lastTempRead = 0;

const unsigned long SCROLL_DELAY  = 350;   // ms per scroll step
const unsigned long TEMP_INTERVAL = 2000;  // DHT11 needs >=1s between reads

// ============================================================
void setup() {
  Serial.begin(9600);

  lcd.init();
  lcd.backlight();
  lcd.clear();

  dht.begin();

  needsScroll = (candidateName.length() > 16);

  // If the name fits on one row, print it once and leave it static
  if (!needsScroll) {
    lcd.setCursor(0, 0);
    lcd.print(candidateName);
  }

  // Row 2 placeholder while waiting for the first reading
  lcd.setCursor(0, 1);
  lcd.print("Temp: --.- C");

  // Lets monitor.py confirm the Arduino is alive and talking on the
  // serial line before any TEMP: readings start arriving. If you never
  // see this line on the PC side, the problem is the USB/serial link
  // itself (wrong COM port, cable, or Serial Monitor still open) rather
  // than the sensor or the code below.
  Serial.println("BOOT:ready");
}

// ============================================================
void loop() {
  unsigned long now = millis();

  // ---- Row 1 : candidate name (scrolls if > 16 chars) --------
  if (needsScroll && (now - lastScroll >= SCROLL_DELAY)) {
    lastScroll = now;

    String padded = candidateName + "                ";  // 16 trailing spaces
    String window = padded.substring(scrollPos, scrollPos + 16);

    lcd.setCursor(0, 0);
    lcd.print(window);

    scrollPos++;
    if (scrollPos > (int)candidateName.length()) {
      scrollPos = 0;
    }
  }

  // ---- Row 2 : temperature + humidity -------------------------
  if (now - lastTempRead >= TEMP_INTERVAL) {
    lastTempRead = now;

    float temp = dht.readTemperature();   // Celsius
    float hum  = dht.readHumidity();

    if (isnan(temp) || isnan(hum)) {
      lcd.setCursor(0, 1);
      lcd.print("Sensor error!   ");
      Serial.println("ERROR:sensor_read_failed");
      return;
    }

    lcd.setCursor(0, 1);
    lcd.print("Temp:");
    lcd.print(temp, 1);
    lcd.print((char)223);   // degree symbol
    lcd.print("C H:");
    lcd.print((int)hum);
    lcd.print("%  ");        // trailing spaces clear leftover characters

    // Format expected by monitor.py:  TEMP:25.3,HUM:60
    Serial.print("TEMP:");
    Serial.print(temp, 1);
    Serial.print(",HUM:");
    Serial.println((int)hum);
  }
}
