# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Update pip to the latest version and install system dependencies
RUN pip install --upgrade pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define an environment variable to prevent Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Define an environment variable to buffer the stdout
ENV PYTHONUNBUFFERED=1

# Change the working directory to padelscraper to be able to run scrapy crawl
WORKDIR /usr/src/app/padelscraper