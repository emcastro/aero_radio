import time
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 8883
CA_CERT = "ca/ca.pem"
CLIENT_CERT = "ca/issued/device-test-001.pem"
CLIENT_KEY = "ca/issued/device-test-001-key.pem"
CLIENT_ID = "device-test-001"
TOPIC = "devices/device-test-001/telemetry/value"


def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[IoT] Connected: {rc}")


def on_disconnect(client, userdata, rc, properties=None):
    print(f"[IoT] Disconnected: {rc}")


client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.tls_set(ca_certs=CA_CERT, certfile=CLIENT_CERT, keyfile=CLIENT_KEY)
client.tls_insecure_set(True)
client.username_pw_set(CLIENT_ID, CLIENT_ID)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.connect(BROKER, PORT, 60)
client.loop_start()

value = 0
direction = 1
try:
    while True:
        client.publish(TOPIC, str(value))
        print(f"[IoT] Published: {value}")
        value += direction
        if value >= 100:
            direction = -1
        elif value <= 0:
            direction = 1
        time.sleep(0.5)
except KeyboardInterrupt:
    client.disconnect()
    client.loop_stop()
