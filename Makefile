doc: clean_doc
	echo 'building docs...'
	cd docs && sphinx-apidoc --force -M -P -e -o source/ ../src
	cd docs && make html

clean_doc:
	echo 'cleaning docs...'
	cd docs && rm -f source/src.rst
	cd docs && rm -f source/src.*.rst

dependencies:
	pip install -r requirements.txt

# NOTE: The following environment variables are expected to be set:
#	TX_PREFIX (optional)
#	TX_DATABASE_PW
#	AWS_ACCESS_KEY_ID
#	AWS_SECRET_ACCESS_KEY

test:
	PYTHONPATH="src/" python2 -m unittest discover -s tests/
	PYTHONPATH="src/" python3 -m unittest discover -s tests/

run:
	python src/main.py
#           and then browse to 127.0.0.1:5000
