# Lightweight Python base image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install dependencies first so this layer is cached when only the code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code and the serialized model
COPY app.py superkart_model.joblib ./

# Port on which the API is served
EXPOSE 7860

# Start the API with Gunicorn
# - `-w 2`: 2 worker processes to serve concurrent requests
# - `-b 0.0.0.0:7860`: listen on port 7860 on all interfaces
# - `app:superkart_api`: the Flask instance `superkart_api` in app.py
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:7860", "--timeout", "120", "app:superkart_api"]
