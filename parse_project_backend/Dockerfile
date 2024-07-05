FROM python:3.12

WORKDIR /parse_project_backend

COPY requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

COPY . /parse_project_backend

CMD uvicorn app:app --host 0.0.0.0 --port 8000
