PY ?= python3

.PHONY: test demo run compile clean

test:
	$(PY) -m unittest discover -s tests -p 'test_*.py' -v

demo:
	$(PY) cli.py demo

run:
	$(PY) cli.py run examples/hello.bada

compile:
	$(PY) cli.py compile examples/hello.bada

silent-edit:
	$(PY) cli.py silent-edit examples/frames/hello_program --run

clean:
	rm -rf generated
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
