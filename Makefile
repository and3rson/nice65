.PHONY: test
test:
	python -m nice65 ./samples/example.s | diff - ./samples/clean.s
	python -m nice65 ./samples/example2.s -l | diff - ./samples/clean2.s

.PHONY: build
build:
	rm -rf ./dist
	python3 -m build -n

.PHONY: upload
upload: build
	twine upload ./dist/*
