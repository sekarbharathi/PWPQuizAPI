FROM python:3.9-slim

WORKDIR /opt/quizapp

# Copy requirements first to leverage Docker cache
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ../app/ ./app/

RUN python3 app/database.py
# Create instance directory and set permissions
RUN mkdir -p /opt/quizapp/instance && \
    chgrp -R root /opt/quizapp && \
    chmod -R g=u /opt/quizapp

# Run Gunicorn with 3 workers, binding to 0.0.0.0:8000
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:8000", "app.app:app"]