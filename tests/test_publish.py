import ssl, socket, struct

ctx = ssl.create_default_context(cafile="ca/ca.pem")
ctx.load_cert_chain(
    certfile="ca/issued/device-test-001.pem",
    keyfile="ca/issued/device-test-001-key.pem",
)
ctx.check_hostname = False

sock = socket.create_connection(("localhost", 8883), timeout=5)
ssock = ctx.wrap_socket(sock)

cid = b"device-test-001"
un = b"device-test-001"
pw = b"device-test-001"
payload = (
    struct.pack(">H", len(cid)) + cid
    + struct.pack(">H", len(un)) + un
    + struct.pack(">H", len(pw)) + pw
)
var = b"\x00\x04MQTT" + bytes([4, 0xC2]) + struct.pack(">H", 60) + payload
ssock.sendall(bytes([0x10, len(var)]) + var)
resp = ssock.recv(4)
assert resp[3] == 0, "CONNECT FAIL"

topic = b"devices/device-test-001/telemetry/temp"
pub = struct.pack(">H", len(topic)) + topic + b'{"temp":24}'
ssock.sendall(bytes([0x30, len(pub)]) + pub)
ssock.close()
print("PUBLISH OK")
