FROM python:3.10-slim
WORKDIR /app
RUN pip install paho-mqtt requests
COPY . .
CMD ["python", "brain.py"]
