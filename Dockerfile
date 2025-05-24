FROM python:3.9-alpine as base
FROM base as builder
RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install --prefix=/install -r /requirements.txt

FROM base
COPY --from=builder /install /usr/local
COPY protocol_gateway.py /app/
COPY config.cfg /app/
COPY defs/ /app/defs/
COPY classes /app/classes/
COPY protocols /app/protocols/
WORKDIR /app
CMD ["python3", "protocol_gateway.py"] 
