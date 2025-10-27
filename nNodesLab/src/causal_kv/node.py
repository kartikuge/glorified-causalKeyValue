import threading,time
from typing import Dict
from .clocks import LamportClock
from .deps import DependencyTracker,Version
from .storage import KVStore
from .protocol import decode,encode
from .network import serve,send_json
class DataCenterNode:
    def __init__(self,node_id,host,port,peers,delay_lookup=None):
        self.node_id=node_id; self.host=host; self.port=port; self.peers=peers
        self.delay_lookup=delay_lookup or (lambda s,d,p:0)
        self.clock=LamportClock(node_id=node_id); self.deps=DependencyTracker(); self.store=KVStore()
        self._pending={}; self._plock=threading.RLock()
    def start(self): serve(self.host,self.port,self._handle)
    def client_read(self,key):
        got=self.store.get(key)
        return {"type":"client_read_ok","key":key,"value":(got[0] if got else None),"version":(list(got[1]) if got else None)}
    def client_write(self,key,val):
        ver=self.clock.tick(); self.deps.seen(key,ver); self.store.put(key,val,ver)
        deps=self.deps.snapshot(); self._fanout(key,val,ver,deps)
        return {"type":"client_write_ok","key":key,"version":list(ver)}
    def _handle(self,conn):
        try:
            m=decode(conn); t=m.get("type")
            if t=="client_read": conn.sendall(encode(self.client_read(m["key"])) )
            elif t=="client_write": conn.sendall(encode(self.client_write(m["key"],m["value"])) )
            elif t=="replicate": self._handle_repl(m); conn.sendall(encode({"type":"replicate_ok"}))
            else: conn.sendall(encode({"type":"error","error":"unknown"}))
        finally:
            try: conn.shutdown(1)
            except: pass
            conn.close()
    def _fanout(self,key,val,ver:Version,deps:Dict[str,Version]):
        for p in self.peers:
            threading.Thread(target=self._send_one,args=(p,key,val,ver,deps),daemon=True).start()
    def _send_one(self,p,key,val,ver,deps):
        d=self.delay_lookup(self.node_id, getattr(p,'id',p.get('id',-1)), getattr(p,'port',p.get('port')))
        if d: time.sleep(d/1000.0)
        host=getattr(p,'host',p.get('host')); port=getattr(p,'port',p.get('port'))
        send_json(host,port,{"type":"replicate","src":self.node_id,"key":key,"value":val,"version":list(ver),"deps":{k:list(v) for k,v in deps.items()}})
    def _handle_repl(self,m:dict):
        key=m['key']; val=m['value']; ver=tuple(int(x) for x in m['version'])
        deps={k:(int(v[0]),int(v[1])) for k,v in m.get('deps',{}).items()}
        self.clock.recv(ver[0])
        if not self.deps.satisfied(deps, self.store.get_version):
            tok=(key,ver)
            with self._plock: self._pending[tok]=(val,deps)
            threading.Thread(target=self._await,args=(tok,),daemon=True).start(); return
        self._commit(key,val,ver,deps)
    def _await(self,tok):
        key,ver=tok
        while not self.deps.satisfied(self._pending[tok][1], self.store.get_version):
            time.sleep(0.02)
        val,deps=self._pending.pop(tok,(None,{}))
        if val is not None: self._commit(key,val,ver,deps)
    def _commit(self,key,val,ver,deps):
        self.store.put(key,val,ver)
        for k,v in deps.items(): self.deps.seen(k,v)
        self.deps.seen(key,ver)
