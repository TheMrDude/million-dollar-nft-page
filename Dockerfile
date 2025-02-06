# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Create uploads directory
RUN mkdir -p /app/src/static/uploads

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn
RUN pip install gunicorn

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable to ensure Python output is sent directly to terminal
ENV PYTHONUNBUFFERED=1

# Run the application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--chdir", "src", "app:app"]
