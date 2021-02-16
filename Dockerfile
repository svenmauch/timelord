FROM python:3.8

WORKDIR /timelord

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY timelord/ .

CMD ["python", "./timelord.py"]