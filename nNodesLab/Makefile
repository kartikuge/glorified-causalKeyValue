.PHONY: n0 n1 n2 test

n0:
	python -m causal_kv.cli --mode dc --id 0 --config cluster.json
n1:
	python -m causal_kv.cli --mode dc --id 1 --config cluster.json
n2:
	python -m causal_kv.cli --mode dc --id 2 --config cluster.json

test:
	python -m pytest -q