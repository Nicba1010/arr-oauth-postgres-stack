# Start with a Python slim image for a smaller footprint
FROM python:3.13-alpine

# Create working directory
WORKDIR /app

# Copy just the Python script
COPY patch_config.py .

# Set executable permissions
RUN chmod +x patch_config.py

# Run the script
ENTRYPOINT ["python", "patch_config.py"]