.PHONY: test
test:
	./nice65.py example.s | diff - clean.s
