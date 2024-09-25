FROM python:3.9

RUN python3 -m pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

CMD ["sh", "entrypoint.sh"]
