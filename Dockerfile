FROM python:2

WORKDIR /tx

ADD . /tx

RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV PYTHONPATH .

CMD [ "python", "src/main.py" ]
