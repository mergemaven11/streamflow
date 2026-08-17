FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY src ./src
COPY tests ./tests

# StreamFlow is a desktop GUI. The container is intentionally used for
# repeatable headless validation rather than pretending the app is a web service.
ENV QT_QPA_PLATFORM=offscreen
CMD ["python", "-m", "pytest", "-q"]
