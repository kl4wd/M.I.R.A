FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bridge.py .

ENV MQTT_BROKER=mira-mosquitto
ENV MQTT_PORT=1883
ENV UART_PORT=/dev/ttyUSB0
ENV UART_BAUD=115200

CMD ["python", "-u", "bridge.py"]
