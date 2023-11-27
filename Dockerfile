FROM python:3.11

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set work directory
WORKDIR /app

# copy project
COPY . .

# Install Poetry
RUN pip install poetry

# Install dependencies from the poetry.lock file
RUN poetry install --no-interaction --no-ansi

# Activate the virtual environment
CMD ["poetry", "run", "bash"]
