FROM python:2

WORKDIR /tx

ADD . /tx

# Need to investigate why --no-cache-dir was included in this command???
RUN pip2 install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container (at 127.0.0.1:5000)
EXPOSE 5000

# Define environment variable
ENV PYTHONPATH src

# The following command fails coz it serves on the container's 127.0.0.1:5000
#   which doesn't get to the outside for some reason that I don't fully understand yet
#CMD [ "python2", "src/main.py" ]

ENV FLASK_APP src/main.py
ENTRYPOINT ["python2","-m","flask","run","--host=0.0.0.0"]

# NOTE: To build use: docker build -t tx .
#       To test use: docker run -p 5000:5000 tx
#           and then browse to 127.0.0.1:5000
