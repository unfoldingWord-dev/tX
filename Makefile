doc: clean_doc
	echo 'building docs...'
	cd docs && sphinx-apidoc --force -M -P -e -o source/ ../src
	cd docs && make html

clean_doc:
	echo 'cleaning docs...'
	cd docs && rm -f source/src.rst
	cd docs && rm -f source/src.*.rst

run:
	python2 src/main.py

test:
	python2 -m unittest discover -s tests/

dependencies:
	pip2 install -r requirements.txt
