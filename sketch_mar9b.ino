#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <time.h>

/* WIFI */

const char* ssid = "Chitchat";
const char* password = "123456789";

/* MQTT */

const char* mqtt_server = "192.168.1.6";
const int mqtt_port = 1883;
const char* mqtt_topic = "building/apt101/flow";

/* DEVICE */

const char* APT_ID = "APT_101";

/* NTP */

const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 19800;
const int daylightOffset_sec = 0;

/* PINS */

/* CHANGE 1 → Use GPIO27 instead of GPIO34 */

#define FLOW_SENSOR_PIN 27
#define TRIG_PIN 5
#define ECHO_PIN 18

/* VARIABLES */

volatile int pulseCount = 0;

float flowRate = 0;
float totalLitres = 0;

unsigned long oldTime = 0;

bool isFlowing = false;
unsigned long flowStartTime = 0;

const float TANK_HEIGHT_CM = 120.0;

/* WIFI + MQTT */

WiFiClient espClient;
PubSubClient client(espClient);

/* FLOW INTERRUPT */

void IRAM_ATTR pulseCounter()
{
  pulseCount++;
}

/* WIFI */

void setup_wifi()
{
  Serial.println("Connecting WiFi");

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");

  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);

  Serial.println("Waiting for NTP");

  time_t now = time(nullptr);

  while (now < 100000)
  {
    delay(500);
    Serial.print(".");
    now = time(nullptr);
  }

  Serial.println("");
  Serial.println("Time synced");
}

/* MQTT */

void reconnect()
{
  while (!client.connected())
  {
    Serial.print("Connecting MQTT...");

    if (client.connect("ESP32_APT101"))
    {
      Serial.println("connected");
    }
    else
    {
      Serial.println("failed");
      delay(5000);
    }
  }
}

/* ULTRASONIC */

float readDistance()
{
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);

  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);

  /* CHANGE 2 → Prevent blocking when sensor disconnected */

  if (duration <= 0)
  {
    return -1;
  }

  float distance = duration * 0.034 / 2;

  return distance;
}

float getTankPercent()
{
  float distance = readDistance();

  Serial.print("Distance: ");
  Serial.println(distance);

  if (distance < 0)
  {
    return 0;
  }

  float waterHeight = TANK_HEIGHT_CM - distance;

  float percent = (waterHeight / TANK_HEIGHT_CM) * 100;

  if (percent < 0) percent = 0;
  if (percent > 100) percent = 100;

  return percent;
}

/* SETUP */

void setup()
{
  Serial.begin(115200);

  pinMode(FLOW_SENSOR_PIN, INPUT_PULLUP);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  attachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_PIN), pulseCounter, FALLING);

  setup_wifi();

  client.setServer(mqtt_server, mqtt_port);
}

/* LOOP */

void loop()
{
  if (!client.connected())
  {
    reconnect();
  }

  client.loop();

  if ((millis() - oldTime) > 10000)
  {

    /* CHANGE 3 → safer pulse reading */

    noInterrupts();
    int pulses = pulseCount;
    pulseCount = 0;
    interrupts();

    Serial.print("Pulse Count: ");
    Serial.println(pulses);

    /* FLOW CALCULATION */

    flowRate = (pulses / 450.0) * 6.0;

    float litres = pulses / 450.0;

    totalLitres += litres;

    if (flowRate > 0.1 && !isFlowing)
    {
      isFlowing = true;
      flowStartTime = millis();
    }

    else if (flowRate <= 0.1 && isFlowing)
    {
      isFlowing = false;
    }

    long duration = isFlowing ? (millis() - flowStartTime) / 1000 : 0;

    float tankPercent = getTankPercent();

    int rssi = WiFi.RSSI();

    time_t now = time(nullptr);

    char timeStr[30];

    strftime(timeStr, sizeof(timeStr), "%Y-%m-%d %H:%M:%S", localtime(&now));

    StaticJsonDocument<256> doc;

    doc["apt_id"] = APT_ID;
    doc["timestamp"] = timeStr;
    doc["flow_rate_lpm"] = flowRate;
    doc["volume_l"] = totalLitres;
    doc["duration_s"] = duration;
    doc["tank_pct"] = tankPercent;
    doc["wifi_rssi"] = rssi;

    char buffer[256];

    serializeJson(doc, buffer);

    client.publish(mqtt_topic, buffer);

    Serial.println("Data Sent:");
    Serial.println(buffer);

    oldTime = millis();
  }
}