FROM python:3.9-alpine as base
FROM base as builder
RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install --prefix=/install -r /requirements.txt

FROM base
COPY --from=builder /install /usr/local
COPY growatt2mqtt.py /app/
COPY growatt.py /app/
COPY growatt2mqtt.cfg /app/
WORKDIR /app
CMD ["python3", "growatt2mqtt.py"] 