.PHONY: test
test:
	python -m nice65 ./samples/example.s | diff - ./samples/clean.s

.PHONY: build
build:
	rm -rf ./dist
	python3 -m build -n

.PHONY: upload
upload: build
	twine upload ./dist/*
