# Set function directory
ARG FUNCTION_DIR="/home/app"

# Use a base image with Uvicorn for FastAPI
FROM python:3.10-slim AS build-image

# Install build dependencies
RUN apt-get update && apt-get install -y build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set the working directory to the function directory
ARG FUNCTION_DIR
RUN mkdir -p ${FUNCTION_DIR}
WORKDIR ${FUNCTION_DIR}

# Install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir --no-compile -r requirements.txt \
    && rm -rf /root/.cache

# Expose the port the app runs on
EXPOSE 8000

# Copy the function code
COPY src ${FUNCTION_DIR}/src

# Set the CMD to run Uvicorn, binding to 0.0.0.0 and port 8000
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]
