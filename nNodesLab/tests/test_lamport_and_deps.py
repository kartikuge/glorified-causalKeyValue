from causal_kv.clocks import LamportClock
from causal_kv.deps import DependencyTracker

def test_lamport():
    a=LamportClock(0); b=LamportClock(1)
    va=a.tick(); vb=b.recv(va[0])
    assert vb[0]>va[0]

def test_deps():
    d=DependencyTracker(); d.seen('x',(3,0))
    assert d.snapshot()['x']==(3,0)
    assert d.satisfied({'x':(2,0)}, lambda k:(3,0))
