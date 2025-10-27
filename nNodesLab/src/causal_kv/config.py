import json
from dataclasses import dataclass
from typing import List,Dict
@dataclass
class NodeConfig: id:int; host:str; port:int
@dataclass
class ClusterConfig:
    nodes:List[NodeConfig]; link_delays_ms:Dict[str,int]
    @staticmethod
    def from_file(p:str)->"ClusterConfig":
        raw=json.load(open(p)); nodes=[NodeConfig(id=n['id'],host=n.get('host','127.0.0.1'),port=n['port']) for n in raw.get('nodes',raw)]
        return ClusterConfig(nodes=nodes,link_delays_ms=raw.get('link_delays_ms',{}))
    def get_me_and_peers(self,my:int):
        me=next(n for n in self.nodes if n.id==my); peers=[n for n in self.nodes if n.id!=my]; return me,peers
    def link_delay(self,src:int,dst:int,dstp:int)->int:
        return int(self.link_delays_ms.get(f"{src}->{dst}", self.link_delays_ms.get(f"{src}->{dstp}",0)))
