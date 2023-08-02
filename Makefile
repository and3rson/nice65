.PHONY: test
test:
	./nice65.py ./samples/example.s | diff - ./samples/clean.s
