/*
   SI4735 + ESP32 UART Control (Raspberry Pi Ready)

   Updated:
   - Touch buttons removed
   - Uses UART commands only
   - Updated GPIO pins per your configuration
*/

#include <SI4735.h>
#include <Wire.h>

#define RESET_PIN 5              // GPIO5

// I2C bus pins on ESP32 (UPDATED)
#define ESP32_I2C_SDA 7          // GPIO7
#define ESP32_I2C_SCL 6          // GPIO6

#define AM_FUNCTION 1
#define FM_FUNCTION 0

uint16_t currentFrequency;
uint16_t previousFrequency;

SI4735 si4735;

bool currentModeFM = true;

// ------------------ HELP ------------------
void showHelp()
{
  Serial.println("Available commands:");
  Serial.println("VOLUP");
  Serial.println("VOLDN");
  Serial.println("MODE FM");
  Serial.println("MODE AM");
  Serial.println("TUNE <value>");
  Serial.println("STEPUP <value>");
  Serial.println("STEPDN <value>");
  Serial.println("SEEKUP");
  Serial.println("SEEKDN");
  Serial.println("STATUS");
  Serial.println("HELP");
  Serial.println("==============================");
}

// ------------------ STATUS ------------------
void showStatus()
{
  currentFrequency = si4735.getCurrentFrequency();

  si4735.getStatus();
  si4735.getCurrentReceivedSignalQuality();

  Serial.print("Tuned: ");

  if (si4735.isCurrentTuneFM())
  {
    Serial.print(String(currentFrequency / 100.0, 2));
    Serial.print(" MHz ");
    Serial.print((si4735.getCurrentPilot()) ? "STEREO" : "MONO");
  }
  else
  {
    Serial.print(currentFrequency);
    Serial.print(" kHz");
  }

  Serial.print(" | SNR: ");
  Serial.print(si4735.getCurrentSNR());

  Serial.print(" | RSSI: ");
  Serial.println(si4735.getCurrentRSSI());
}

// ------------------ VALIDATION ------------------
bool isValidFrequency(uint16_t freq)
{
  if (currentModeFM)
    return (freq >= 6400 && freq <= 10800);  // FM
  else
    return (freq >= 520 && freq <= 1710);    // AM
}

// ------------------ COMMAND PARSER ------------------
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
  else if (cmd == "TUNE")
  {
    uint16_t freq = (uint16_t)arg.toInt();

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
  else if (cmd == "STEPUP")
  {
    int delta = arg.toInt();
    uint16_t next = si4735.getCurrentFrequency() + delta;

    if (isValidFrequency(next))
    {
      si4735.setFrequency(next);
      Serial.println("OK STEPUP");
    }
    else
    {
      Serial.println("ERR RANGE");
    }
  }
  else if (cmd == "STEPDN")
  {
    int delta = arg.toInt();
    int next = si4735.getCurrentFrequency() - delta;

    if (next > 0 && isValidFrequency((uint16_t)next))
    {
      si4735.setFrequency((uint16_t)next);
      Serial.println("OK STEPDN");
    }
    else
    {
      Serial.println("ERR RANGE");
    }
  }
  else if (cmd == "SEEKUP")
  {
    si4735.seekStationUp();
    Serial.println("OK SEEKUP");
  }
  else if (cmd == "SEEKDN")
  {
    si4735.seekStationDown();
    Serial.println("OK SEEKDN");
  }
  else if (cmd == "STATUS")
  {
    showStatus();
  }
  else if (cmd == "HELP")
  {
    showHelp();
  }
  else
  {
    Serial.println("ERR UNKNOWN");
  }
}

// ------------------ SETUP ------------------
void setup()
{
  Serial.begin(115200);
  delay(1000);

  pinMode(RESET_PIN, OUTPUT);
  digitalWrite(RESET_PIN, HIGH);

  Serial.println("SI4735 UART Radio Ready");
  showHelp();

  Wire.begin(ESP32_I2C_SDA, ESP32_I2C_SCL);

  delay(500);

  si4735.setup(RESET_PIN, FM_FUNCTION);
  si4735.setFM(8400, 10800, 8990, 10);

  currentModeFM = true;

  currentFrequency = previousFrequency = si4735.getCurrentFrequency();

  si4735.setVolume(45);

  showStatus();
}

// ------------------ LOOP ------------------
void loop()
{
  if (Serial.available() > 0)
  {
    String line = Serial.readStringUntil('\n');
    line.trim();

    if (line.length() > 0)
    {
      handleCommand(line);
    }
  }

  delay(100);

  currentFrequency = si4735.getCurrentFrequency();
  if (currentFrequency != previousFrequency)
  {
    previousFrequency = currentFrequency;
    showStatus();
    delay(200);
  }
}