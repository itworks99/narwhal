FROM python:alpine

LABEL Name=narwhal Version=0.2
EXPOSE 3000

WORKDIR /narwhal
ADD . /narwhal

RUN apk add linux-headers
RUN apk add libc-dev libffi-dev openssl-dev openssl bash tzdata
RUN apk add gcc

RUN cp /usr/share/zoneinfo/Australia/Sydney /etc/localtime

RUN python3 -m pip install -r requirements.txt

RUN bash localhostca.sh

CMD ["python3", "-u", "narwhal.py"]
