FROM python:3.9-alpine as base
FROM base as builder
RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install --prefix=/install -r /requirements.txt

FROM base
COPY --from=builder /install /usr/local
COPY protocol_settings.py /app/
COPY protocol_gateway.py /app/
COPY inverter.py /app/
COPY config.cfg /app/
WORKDIR /app
CMD ["python3", "protocol_gateway.py"] 