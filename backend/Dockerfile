FROM python:3.12-rc-alpine3.17

WORKDIR /backend

COPY . .

RUN apk add gcc libc-dev libffi-dev

RUN pip3 install -r requirements.txt

CMD ["python", "main.py"]