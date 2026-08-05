import sys
import time

import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 8883
CA_CERT = "ca/ca.pem"
CLIENT_CERT = "ca/issued/device-test-001.pem"
CLIENT_KEY = "ca/issued/device-test-001-key.pem"
CLIENT_ID = "device-test-001"

result = {}


def on_connect(client, userdata, flags, reason_code, properties=None):
    result["reason_code"] = reason_code
    client.disconnect()


client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.tls_set(ca_certs=CA_CERT, certfile=CLIENT_CERT, keyfile=CLIENT_KEY)
client.tls_insecure_set(True)
client.username_pw_set(CLIENT_ID, CLIENT_ID)
client.on_connect = on_connect
client.connect(BROKER, PORT, 60)
client.loop_start()

deadline = time.time() + 10
while "reason_code" not in result and time.time() < deadline:
    time.sleep(0.1)

client.loop_stop()

print("CONNACK:", result["reason_code"])
sys.exit(0 if result["reason_code"] == 0 else 1)
