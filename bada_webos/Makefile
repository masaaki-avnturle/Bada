PY ?= python3

.PHONY: test boot qec ultranet android wm clean

test:
	$(PY) -m unittest discover -s tests -p 'test_*.py' -v

boot:
	$(PY) webos.py

qec:
	$(PY) cli.py qec --all

ultranet:
	$(PY) cli.py ultranet

android:
	$(PY) cli.py android

wm:
	$(PY) cli.py wm

clean:
	rm -rf generated
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
