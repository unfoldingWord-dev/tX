doc:
	cd docs && sphinx-apidoc --force -o source/ ../src/
	cd docs && make html

run:
	python ./src/main.py

test:
	python -m unittest discover

dependencies:
	pip install -r requirements.txt