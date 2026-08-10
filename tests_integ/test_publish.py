import sys
import time

import paho.mqtt.client as mqtt

# Hardcoded device + topic names: keep in sync with ca/issued/ when topic
# names or device IDs change. MQTT is certificate-only: no username/password.
BROKER = "localhost"
MQTT_PORT = 8883
CA_CERT = "ca/ca.pem"

CENTRAL_CERT = "ca/issued/central.pem"
CENTRAL_KEY = "ca/issued/central-key.pem"
SUBSCRIBE_TOPIC = "devices/+/telemetry/#"

DEVICE_CERT = "ca/issued/device-test-001.pem"
DEVICE_KEY = "ca/issued/device-test-001-key.pem"
PUBLISH_TOPIC = "devices/device-test-001/telemetry/temp"
PAYLOAD = '{"temp":24}'

subscriber_ready = {}
received = {}
published = {}


def central_on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        client.subscribe(SUBSCRIBE_TOPIC)
    else:
        subscriber_ready["ok"] = False
        received["ok"] = False
        client.disconnect()


def central_on_subscribe(client, userdata, mid, reason_code_list, properties=None):
    subscriber_ready["ok"] = reason_code_list[0] == 0


def central_on_message(client, userdata, msg):
    received["ok"] = (msg.topic == PUBLISH_TOPIC and msg.payload == PAYLOAD.encode())
    received["topic"] = msg.topic
    received["payload"] = msg.payload
    client.disconnect()


def device_on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        client.publish(PUBLISH_TOPIC, PAYLOAD, qos=1)
    else:
        published["ok"] = False


def device_on_publish(client, userdata, mid, reason_code, properties=None):
    published["ok"] = True
    client.disconnect()


central = mqtt.Client(client_id="central", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
central.tls_set(ca_certs=CA_CERT, certfile=CENTRAL_CERT, keyfile=CENTRAL_KEY)
central.tls_insecure_set(True)
central.on_connect = central_on_connect
central.on_subscribe = central_on_subscribe
central.on_message = central_on_message
central.connect(BROKER, MQTT_PORT, 60)
central.loop_start()

deadline = time.time() + 10
while "ok" not in subscriber_ready and time.time() < deadline:
    time.sleep(0.1)
print(f"[Central] Subscribed: {SUBSCRIBE_TOPIC}")

device = mqtt.Client(client_id="device-test-001", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
device.tls_set(ca_certs=CA_CERT, certfile=DEVICE_CERT, keyfile=DEVICE_KEY)
device.tls_insecure_set(True)
device.on_connect = device_on_connect
device.on_publish = device_on_publish
device.connect(BROKER, MQTT_PORT, 60)
device.loop_start()
print(f"[Device] Publishing: {PUBLISH_TOPIC} <- {PAYLOAD}")

deadline = time.time() + 10
while "ok" not in received and time.time() < deadline:
    time.sleep(0.1)

central.loop_stop()
device.loop_stop()

if "topic" in received:
    print(f"[Central] Received: {received['topic']} <- {received['payload']}")

ok = bool(subscriber_ready.get("ok") and published.get("ok") and received.get("ok"))
sys.exit(0 if ok else 1)
