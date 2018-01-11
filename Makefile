start:
	python ./src/main.py

docs: clean
	sphinx-apidoc --force --full -H "tx" -v "1.0" -a -o ./docs ./src
	cd docs && make html

test:
	python ./src/main.py

dependencies:
	pip install -r requirements.txt

clean:
	rm -rf docs