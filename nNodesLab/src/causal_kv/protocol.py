import json

def encode(m:dict)->bytes: return (json.dumps(m,separators=(",",":"))+"\n").encode()

def decode(conn):
    buf=b""
    while True:
        ch=conn.recv(1)
        if not ch: break
        buf+=ch
        if ch==b"\n": break
    return json.loads(buf.decode()) if buf else {}
