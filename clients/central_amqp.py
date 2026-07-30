import pika

BROKER = "localhost"
PORT = 5672
USERNAME = "central"
PASSWORD = "central"


def callback(ch, method, properties, body):
    routing_key = method.routing_key.replace(".", "/")
    print(f"[Central-AMQP] {routing_key}: {body.decode()}")


conn = pika.BlockingConnection(pika.ConnectionParameters(
    host=BROKER, port=PORT,
    credentials=pika.PlainCredentials(USERNAME, PASSWORD),
))
channel = conn.channel()

result = channel.queue_declare(queue="", exclusive=True, auto_delete=True)
queue_name = result.method.queue

channel.queue_bind(exchange="amq.topic", queue=queue_name, routing_key="devices.#")
print(f"[Central-AMQP] Connected, bound to amq.topic with routing_key=devices.#")

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    conn.close()
