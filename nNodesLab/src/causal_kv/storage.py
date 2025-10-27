import threading
from typing import Dict,Tuple,Optional
Version=Tuple[int,int]
class KVStore:
    def __init__(self): self._l=threading.RLock(); self._v:Dict[str,Tuple[str,Version]]={}
    def get(self,k:str):
        with self._l: return self._v.get(k)
    def get_version(self,k:str):
        v=self.get(k); return v[1] if v else None
    def put(self,k:str,val:str,ver:Version):
        with self._l:
            cur=self._v.get(k)
            if cur is None or cur[1]<ver: self._v[k]=(val,ver)
