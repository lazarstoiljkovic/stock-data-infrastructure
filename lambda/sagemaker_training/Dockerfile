FROM public.ecr.aws/lambda/python:3.8

RUN pip install --no-cache-dir boto3 

# Copy all files in ./src
COPY src/ ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler.
CMD [ "index.handler" ]