FROM python:2

WORKDIR /tx

ADD . /tx

RUN pip2 install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV PYTHONPATH .

CMD [ "python2", "src/main.py" ]

# NOTE: To build use: docker build -t txContainer .
#       To test use: docker run --net="host" -p 5000:5000 --rm txContainer
#           and then browse to 127.0.0.1:5000
