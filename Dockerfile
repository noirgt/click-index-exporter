FROM alpine:3.15.0

ENV PYTHONUNBUFFERED=1
ENV PYCURL_SSL_LIBRARY=openssl

WORKDIR /click-index-exporter
COPY exporter.py .
COPY requirements.txt .

RUN apk add --no-cache libcurl
RUN apk --update add python3 curl-dev \
    && apk add --update --no-cache --virtual \
    .build-dependencies py3-pip python3-dev build-base \
    && pip install -r requirements.txt \
    && apk del .build-dependencies \
    && rm -rf /var/cache/apk/*

RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools

ENTRYPOINT ["python3"]
CMD ["exporter.py"]
