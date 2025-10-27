import argparse
from .config import ClusterConfig
from .node import DataCenterNode
from .network import send_json

def main():
    p=argparse.ArgumentParser(prog='causal-kv')
    p.add_argument('--mode',choices=['dc','client'],required=True)
    p.add_argument('--id',type=int,required=True)
    p.add_argument('--config',type=str,default='cluster.json')
    p.add_argument('--op',choices=['read','write'])
    p.add_argument('--key'); p.add_argument('--value')
    a=p.parse_args()
    cfg=ClusterConfig.from_file(a.config)
    if a.mode=='dc':
        me,peers=cfg.get_me_and_peers(a.id)
        node=DataCenterNode(me.id,me.host,me.port,[{'id':x.id,'host':x.host,'port':x.port} for x in peers],
                            delay_lookup=lambda s,d,p: cfg.link_delay(s,d,p))
        node.start()
    else:
        t=next(n for n in cfg.nodes if n.id==a.id)
        msg={'type':'client_read','key':a.key} if a.op=='read' else {'type':'client_write','key':a.key,'value':a.value}
        print(send_json(t.host,t.port,msg))

if __name__=='__main__': main()
