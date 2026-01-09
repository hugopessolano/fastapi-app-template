FROM python:3.13-slim

WORKDIR /code

COPY requirements.txt /code/
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY app /code/app
COPY tools /code/tools
COPY specs /code/specs

EXPOSE 8001

CMD ["python", "-m", "tools.scaffold.api"]
