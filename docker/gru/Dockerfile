FROM python:3.8-slim

# Install required Python packages
RUN pip install --no-cache-dir \
    tensorflow==2.13.0 \
    numpy \
    pandas \
    boto3 \
    joblib

# Copy your training script into the container
COPY src/train.py /opt/ml/code/

# Set environment variables expected by SageMaker
ENV SAGEMAKER_PROGRAM train.py  # Your main training script

# Default command to run your script when the container starts
ENTRYPOINT ["python", "/opt/ml/code/train.py"]