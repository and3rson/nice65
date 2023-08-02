.PHONY: test
test:
	./nice65.py ./samples/example.s | diff - ./samples/clean.s

.PHONY: build
build:
	rm -rf ./dist
	python3 -m build -n

.PHONY: upload
upload: build
	twine upload ./dist/*
