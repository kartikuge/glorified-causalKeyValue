from typing import Dict,Tuple,Optional
Version=Tuple[int,int]
class DependencyTracker:
    def __init__(self): self._d:Dict[str,Version]={}
    def seen(self,k:str,v:Version):
        cur=self._d.get(k)
        if cur is None or cur<v: self._d[k]=v
    def snapshot(self): return dict(self._d)
    def satisfied(self,req:Dict[str,Version],have):
        for k,v in req.items():
            hv:Optional[Version]=have(k)
            if hv is None or hv<v: return False
        return True
