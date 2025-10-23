# Stage 1: Builder stage to install dependencies
# This creates a lean base for dependencies
FROM python:3.11-slim AS builder

# Set environment variables for optimal performance in Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
# Build "wheels" (pre-compiled packages) for faster installation in the next stage
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# Stage 2: Final production stage
# This is the image we'll actually use
FROM python:3.11-slim

# Create a non-root user for better security
RUN useradd -m appuser
WORKDIR /home/appuser/web

# Copy installed dependencies from the builder stage
COPY --from=builder /wheels /wheels
COPY --from=builder /app/requirements.txt .
# Install the pre-compiled packages
RUN pip install --no-cache /wheels/*

# Copy the application source code from our local 'src' folder
# into the image's working directory
COPY ./src .

# Change ownership of all files to our non-root user
RUN chown -R appuser:appuser /home/appuser

# Switch to the non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000