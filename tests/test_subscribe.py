import sys
import time

import paho.mqtt.client as mqtt

# Hardcoded device + topic name: keep in sync with ca/issued/ when topic names
# or device IDs change. MQTT is certificate-only: no username/password.
BROKER = "localhost"
PORT = 8883
CA_CERT = "ca/ca.pem"
CLIENT_CERT = "ca/issued/device-test-001.pem"
CLIENT_KEY = "ca/issued/device-test-001-key.pem"
CLIENT_ID = "device-test-001"
TOPIC = "devices/device-test-001/commands/#"

result = {}


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        client.subscribe(TOPIC)
    else:
        result["granted_qos"] = -1
        client.disconnect()


def on_subscribe(client, userdata, mid, reason_code_list, properties=None):
    result["granted_qos"] = reason_code_list[0]
    client.disconnect()


client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.tls_set(ca_certs=CA_CERT, certfile=CLIENT_CERT, keyfile=CLIENT_KEY)
client.tls_insecure_set(True)
client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.connect(BROKER, PORT, 60)
client.loop_start()

deadline = time.time() + 10
while "granted_qos" not in result and time.time() < deadline:
    time.sleep(0.1)

client.loop_stop()

print(f"SUBACK ({TOPIC}): QoS {result['granted_qos']}")
sys.exit(0 if result["granted_qos"] == 0 else 1)
