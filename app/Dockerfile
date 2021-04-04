FROM python:3.7.4
RUN pip install pipenv

WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pipenv install
RUN pipenv --rm
ENV FLASK_APP api.py

EXPOSE 4444


COPY . .

CMD [ "pipenv", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:4444", "--workers", "2", "--threads", "2", "--timeout", "120", "app:app" ]