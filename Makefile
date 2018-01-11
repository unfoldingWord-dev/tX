start:
	python ./src/main.py

doc:
	cd docs && sphinx-apidoc --force -o source/ ../src/
	cd docs && make html

test:
	python ./src/main.py

dependencies:
	pip install -r requirements.txt