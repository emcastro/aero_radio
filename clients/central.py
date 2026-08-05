import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 8883
CA_CERT = "ca/ca.pem"
CLIENT_CERT = "ca/issued/central.pem"
CLIENT_KEY = "ca/issued/central-key.pem"
CLIENT_ID = "central"
TOPIC = "devices/+/telemetry/#"


def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[Central] Connected: {rc}")
    if rc == 0:
        client.subscribe(TOPIC)
        print(f"[Central] Subscribed: {TOPIC}")


def on_message(client, userdata, msg):
    print(f"[Central] {msg.topic}: {msg.payload.decode()}")


def on_disconnect(client, userdata, rc, properties=None):
    print(f"[Central] Disconnected: {rc}")


client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.tls_set(ca_certs=CA_CERT, certfile=CLIENT_CERT, keyfile=CLIENT_KEY)
client.tls_insecure_set(True)
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
client.connect(BROKER, PORT, 60)

try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()
    client.loop_stop()
