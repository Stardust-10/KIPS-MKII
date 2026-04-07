#include <SI4735.h>
#include <Wire.h>

#define RESET_PIN 12

#define ESP32_I2C_SDA 18
#define ESP32_I2C_SCL 17

#define AM_FUNCTION 1
#define FM_FUNCTION 0

SI4735 si4735;

uint16_t currentFrequency;
uint16_t previousFrequency;

bool currentModeFM = true;

void showStatus()
{
  currentFrequency = si4735.getCurrentFrequency();

  si4735.getStatus();
  si4735.getCurrentReceivedSignalQuality();

  Serial.print("TUNED ");

  if (si4735.isCurrentTuneFM())
  {
    Serial.print(String(currentFrequency / 100.0, 2));
    Serial.print(" MHz ");
  }
  else
  {
    Serial.print(currentFrequency);
    Serial.print(" kHz ");
  }

  Serial.print(" SNR:");
  Serial.print(si4735.getCurrentSNR());
  Serial.print(" RSSI:");
  Serial.println(si4735.getCurrentRSSI());
}

bool isValidFrequency(uint16_t freq)
{
  if (currentModeFM)
    return (freq >= 6400 && freq <= 10800);
  else
    return (freq >= 520 && freq <= 1710);
}

void handleCommand(String cmdLine)
{
  cmdLine.trim();

  int spaceIndex = cmdLine.indexOf(' ');
  String cmd = cmdLine;
  String arg = "";

  if (spaceIndex != -1)
  {
    cmd = cmdLine.substring(0, spaceIndex);
    arg = cmdLine.substring(spaceIndex + 1);
    arg.trim();
  }

  cmd.toUpperCase();

  // ---------- VOLUME ----------
  if (cmd == "VOLUP")
  {
    si4735.volumeUp();
    Serial.println("OK VOLUP");
  }
  else if (cmd == "VOLDN")
  {
    si4735.volumeDown();
    Serial.println("OK VOLDN");
  }

  // ---------- MODE ----------
  else if (cmd == "MODE")
  {
    arg.toUpperCase();

    if (arg == "FM")
    {
      si4735.setFM(8400, 10800, 8990, 10);
      currentModeFM = true;
      Serial.println("OK MODE FM");
    }
    else if (arg == "AM")
    {
      si4735.setAM(570, 1710, 810, 10);
      currentModeFM = false;
      Serial.println("OK MODE AM");
    }
    else
    {
      Serial.println("ERR BAD_MODE");
    }
  }

  // ---------- DIRECT TUNE ----------
  else if (cmd == "TUNE")
  {
    if (arg.length() == 0)
    {
      Serial.println("ERR NO_VALUE");
      return;
    }

    uint16_t freq = arg.toInt();

    if (isValidFrequency(freq))
    {
      si4735.setFrequency(freq);
      Serial.print("OK TUNED ");
      Serial.println(freq);
    }
    else
    {
      Serial.println("ERR BAD_FREQ");
    }
  }

  // ---------- STEP ----------
  else if (cmd == "STEPUP")
  {
    int delta = arg.toInt();
    if (delta <= 0)
    {
      Serial.println("ERR BAD_STEP");
      return;
    }

    uint16_t next = si4735.getCurrentFrequency() + delta;

    if (isValidFrequency(next))
    {
      si4735.setFrequency(next);
      Serial.print("OK FREQ ");
      Serial.println(next);
    }
    else
    {
      Serial.println("ERR RANGE");
    }
  }
  else if (cmd == "STEPDN")
  {
    int delta = arg.toInt();
    if (delta <= 0)
    {
      Serial.println("ERR BAD_STEP");
      return;
    }

    int next = si4735.getCurrentFrequency() - delta;

    if (next > 0 && isValidFrequency((uint16_t)next))
    {
      si4735.setFrequency(next);
      Serial.print("OK FREQ ");
      Serial.println(next);
    }
    else
    {
      Serial.println("ERR RANGE");
    }
  }

  // ---------- SEEK ----------
  else if (cmd == "SEEKUP")
  {
    si4735.seekStationUp();
    Serial.print("OK FREQ ");
    Serial.println(si4735.getCurrentFrequency());
  }
  else if (cmd == "SEEKDN")
  {
    si4735.seekStationDown();
    Serial.print("OK FREQ ");
    Serial.println(si4735.getCurrentFrequency());
  }

  // ---------- STATUS ----------
  else if (cmd == "STATUS")
  {
    Serial.print("MODE ");
    Serial.print(currentModeFM ? "FM " : "AM ");
    Serial.print("FREQ ");
    Serial.print(si4735.getCurrentFrequency());
    Serial.print(" VOL ");
    Serial.println(si4735.getCurrentVolume());
  }

  else
  {
    Serial.println("ERR UNKNOWN");
  }
}

void setup()
{
  Serial.begin(115200);

  pinMode(RESET_PIN, OUTPUT);
  digitalWrite(RESET_PIN, HIGH);

  Wire.begin(ESP32_I2C_SDA, ESP32_I2C_SCL);

  delay(500);

  si4735.setup(RESET_PIN, FM_FUNCTION);
  si4735.setFM(8400, 10800, 8990, 10);

  currentModeFM = true;

  si4735.setVolume(45);

  Serial.println("RADIO READY");
}

void loop()
{
  if (Serial.available())
  {
    String line = Serial.readStringUntil('\n');
    line.trim();

    if (line.length() > 0)
      handleCommand(line);
  }
}