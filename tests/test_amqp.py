import sys
import time

import paho.mqtt.client as mqtt
import pika

# Hardcoded device + topic names: keep in sync with ca/issued/ when topic
# names or device IDs change. MQTT is certificate-only: no username/password.
BROKER = "localhost"
AMQP_PORT = 5672
AMQP_USER = "central"
AMQP_PASSWORD = "central"
BINDING_KEY = "devices.#"

MQTT_PORT = 8883
CA_CERT = "ca/ca.pem"
CLIENT_CERT = "ca/issued/device-test-001.pem"
CLIENT_KEY = "ca/issued/device-test-001-key.pem"
MQTT_CLIENT_ID = "device-test-001"
MQTT_TOPIC = "devices/device-test-001/telemetry/value"
MQTT_PAYLOAD = b"42"

received = {}


def on_amqp_message(ch, method, properties, body):
    received["routing_key"] = method.routing_key
    received["body"] = body
    ch.stop_consuming()


amqp_conn = pika.BlockingConnection(pika.ConnectionParameters(
    host=BROKER, port=AMQP_PORT,
    credentials=pika.PlainCredentials(AMQP_USER, AMQP_PASSWORD),
))
channel = amqp_conn.channel()
result = channel.queue_declare(queue="", exclusive=True, auto_delete=True)
queue_name = result.method.queue
channel.queue_bind(exchange="amq.topic", queue=queue_name, routing_key=BINDING_KEY)
channel.basic_consume(queue=queue_name, on_message_callback=on_amqp_message, auto_ack=True)
print(f"[AMQP] Bound {AMQP_USER} to amq.topic with {BINDING_KEY}")

mqtt_state = {}


def on_mqtt_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        client.publish(MQTT_TOPIC, MQTT_PAYLOAD, qos=1)
    else:
        mqtt_state["done"] = True
        mqtt_state["ok"] = False


def on_mqtt_publish(client, userdata, mid, reason_code, properties=None):
    mqtt_state["done"] = True
    mqtt_state["ok"] = reason_code == 0
    client.disconnect()


client = mqtt.Client(client_id=MQTT_CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.tls_set(ca_certs=CA_CERT, certfile=CLIENT_CERT, keyfile=CLIENT_KEY)
client.tls_insecure_set(True)
client.on_connect = on_mqtt_connect
client.on_publish = on_mqtt_publish
client.connect(BROKER, MQTT_PORT, 60)
client.loop_start()
print(f"[MQTT] Publishing {MQTT_TOPIC} <- {MQTT_PAYLOAD.decode()}")

mqtt_deadline = time.time() + 10
while not mqtt_state.get("done") and time.time() < mqtt_deadline:
    time.sleep(0.1)
    amqp_conn.process_data_events(time_limit=0)

client.loop_stop()

amqp_deadline = time.time() + 10
while not received and time.time() < amqp_deadline:
    amqp_conn.process_data_events(time_limit=1)

amqp_conn.close()

routing_key = received.get("routing_key", "").replace(".", "/")
body = received.get("body", b"")
print(f"[AMQP] Received {routing_key} <- {body.decode()}")

ok = bool(mqtt_state.get("ok") and routing_key == MQTT_TOPIC and body == MQTT_PAYLOAD)
sys.exit(0 if ok else 1)
