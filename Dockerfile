FROM python:3.11-bullseye

WORKDIR /app

# Setup virtual env
ENV VIRTUAL_ENV=./venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$PATH:$VIRTUAL_ENV/bin"

# Install dependencies
COPY requirements.txt .
RUN pip install -r ./requirements.txt

# Copy all files
COPY . .
CMD ["./entrypoint.sh"]