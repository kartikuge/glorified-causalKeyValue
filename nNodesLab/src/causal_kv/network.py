import socket,threading
from .protocol import encode,decode

def serve(host,port,handler):
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    s.bind((host,port)); s.listen(); print(f"[server] {host}:{port}")
    try:
        while True:
            c,_=s.accept(); threading.Thread(target=handler,args=(c,),daemon=True).start()
    finally:
        s.close()

def send_json(host,port,msg,timeout=5.0):
    with socket.create_connection((host,port),timeout=timeout) as s:
        s.sendall(encode(msg)); s.shutdown(socket.SHUT_WR)
        try: return decode(s)
        except Exception: return {}
