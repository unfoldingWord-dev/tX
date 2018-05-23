FROM python:2

WORKDIR /tx

ADD . /tx

# NOTE: Check why --no-cache-dir is specified in the next line (what advantage?)
RUN pip2 install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV PYTHONPATH .

# NOTE: The following environment variables are also expected to be set:
#	TX_PREFIX (optional)
#	TX_DATABASE_PW
#	AWS_ACCESS_KEY_ID
#	AWS_SECRET_KEY

CMD [ "python2", "src/main.py" ]

# NOTE: To build use: docker build -t txcontainer .
#       To test use: docker run --net="host" -p 5000:5000 --rm txcontainer
#           and then browse to 127.0.0.1:5000
