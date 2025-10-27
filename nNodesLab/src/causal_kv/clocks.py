from dataclasses import dataclass
@dataclass
class LamportClock:
    node_id:int; counter:int=0
    def tick(self): self.counter+=1; return (self.counter,self.node_id)
    def recv(self,c): self.counter=max(self.counter,c)+1; return (self.counter,self.node_id)
