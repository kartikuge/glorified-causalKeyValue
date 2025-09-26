# glorified-causalKeyValue
A tiny distributed datastore with causal consistency (Lamport clocks) for CMPSC 497: Distributed Systems

a teaching-scale system that runs 3 “data centers,” accepts concurrent client reads/writes, and replicates with causal ordering using Lamport clocks + dependency tracking. built with bare-bones sockets & threads to make all the distributed-systems ideas visible.

<br>
✨ highlights

Causal Consistency: tracks and enforces “happens-before” using Lamport clocks and a per-key dependency map.

Active-Active data centers: any node can accept reads/writes, then replicates to others.

Deterministic replication delays: configurable sleeps emulate real-world network jitter to surface reordering.

Tiny codebase: a single Python file you can read in ~10 minutes; great for demos, labs, or interviews.

No frameworks: pure socket, threading, and a little time.

Design/behavior summarized from my lab write-up and the source code in this repo. 


<br>
🧠 concept map

Goal: accept client operations at any data center, propagate writes, and only commit a replicated write once its dependencies (observed earlier writes) are satisfied.

Lamport clock: a per-DC logical counter (version_counter) gives each write a version (counter, dataCenterId).

DependencyTracker: maps key → latest observed version. Every write carries the sender’s dependency snapshot.

Admission control for replicas: a receiver loops until check_dependencies() returns true, then commits.

this shows causal consistency: if y happened before z, then every DC will wait to commit z until it has seen y. 


<br>
🧩 architecture (3 DCs + clients)
flowchart LR
  subgraph Client Terminals
    C0[Client → DC0]
    C1[Client → DC1]
    C2[Client → DC2]
  end

  subgraph Data Centers
    DC0((DC0 :8000))
    DC1((DC1 :8001))
    DC2((DC2 :8002))
  end

  C0 -- read/write --> DC0
  C1 -- read/write --> DC1
  C2 -- read/write --> DC2

  DC0 <--> DC1
  DC1 <--> DC2
  DC0 <--> DC2


Replication path: on local write, DC packages (key, version, dependencies) and ships it to peers; receivers delay commit until dependencies satisfied. Artificial sleeps create different inter-DC latencies to demonstrate reordering. 


<br>
📦 quickstart

requirements: Python 3.9+ (no external libs)

Start data centers (3 terminals):

python serverAndPeer.py 0 8000
python serverAndPeer.py 1 8001
python serverAndPeer.py 2 8002


Issue client ops (new terminals; examples):

python serverAndPeer.py client 8000 "write x lost_ring"
python serverAndPeer.py client 8000 "write y found_ring"
python serverAndPeer.py client 8001 "write z glad"


Each local write responds immediately; replica commits may appear later depending on inter-DC delay.

You’ll see logs like “Write z delayed … until dependency y arrives,” then “committed”—that’s causal ordering in action. 

<br>
🗂️ code tour

serverAndPeer.py — everything lives here:

DependencyTracker: update_dependency(), check_dependencies()

handle_client(): parses read/write vs replicate-* messages, bumps Lamport clock, and kicks off replication

replicate_write(): spins threads to contact peers, injects per-link delays with time.sleep()

handle_replication(): waits while dependencies unmet; once satisfied, commits and updates Lamport clock

start_data_center(): TCP accept loop with per-connection threads

client_behavior(): tiny TCP client for read/write commands
(see in-code comments for the exact message formats and port wiring) 


<br>
🧪 what to observe

Reordering: with asymmetric delays (e.g., DC0→DC2 slower than DC1→DC2), you’ll see different arrival orders.

Causal gating: replicas do not commit a write until all its referenced earlier versions are present.

Monotonic reads (per-client session): once you’ve seen a version for a key at a DC, later reads won’t “go back in time.”

(These match the lab’s intended behavior and sample traces.) 

<br>
📉 current limitations (by design for the lab)

No write-write conflict resolution (e.g., LWW/CRDTs not implemented).

Fixed to 3 data centers without code edits.

In-memory state only (no persistence, no GC).

Security: plaintext sockets; not intended for untrusted networks.
(These constraints are acknowledged in the lab brief.) 


<br>
🛣️ roadmap (nice next steps if you want to extend it)

 Pluggable topologies & N nodes via a config file / CLI.

 Replace Lamport with vector clocks for tighter causality checks.

 Conflict handling: LWW option, or demo a simple CRDT (e.g., LWW-register).

 Durability: snapshot to disk; add a write-ahead log and recovery.

 Back-pressure queue for pending replicas instead of while loops + sleep.

 Switch to asyncio sockets, or a tiny RPC veneer for readability.

 Optional observability: Prometheus counters and a Grafana dashboard.

<br>
🧪 sample commands to reproduce the classic demo

replicate the write ordering + dependency wait seen in the lab handout:

# terminal A (DC0)
python serverAndPeer.py 0 8000
# terminal B (DC1)
python serverAndPeer.py 1 8001
# terminal C (DC2)
python serverAndPeer.py 2 8002

# terminal D (client to DC0)
python serverAndPeer.py client 8000 "write x lost_ring"
python serverAndPeer.py client 8000 "write y found_ring"

# terminal E (client to DC1)
python serverAndPeer.py client 8001 "write z glad"


With the provided artificial delays, DC2 will see arrivals like x, z, y, then delay z until y shows up—after which it commits both in causal order. 


<br>
🧾 message formats

Client → DC (local):

read <key> <placeholder> → replies with (key, version, value)

write <key> <value> → returns ack and triggers replication

DC → DC (replication):

replicate-<key>-<version>-<dependencies>

where <version> is a tuple like (lamport, dcId) and <dependencies> is a dict {key: version}. 

<br>
📝 license

MIT — do whatever, just keep the notice.

<br>
🙌 credits

design + implementation: Kartik Ugemuge

guided by a CMPSC 497 lab on causal consistency; write-up and screenshots summarized here. 
