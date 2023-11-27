FROM python:3.11

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set work directory
WORKDIR /app

# copy project
COPY . .

# install dependencies
RUN pip install poetry

RUN poetry install
