FROM python:3.9-slim

# Install supervisor
RUN apt-get update && apt-get install -y supervisor && apt-get clean

WORKDIR /opt/quizapp

# Copy requirements first to leverage Docker cache
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ../app/ ./app/

# Create supervisor configuration directory
RUN mkdir -p /etc/supervisor/conf.d

# Add supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN python3 app/database.py
# Create instance directory and set permissions
RUN mkdir -p /opt/quizapp/instance && \
    chgrp -R root /opt/quizapp && \
    chmod -R g=u /opt/quizapp

# Run supervisor instead of gunicorn directly
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]