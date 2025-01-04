import os
import boto3
import json
import re
import uuid

sagemaker = boto3.client('sagemaker')

def handler(event, context):
    s3_info = event['Records'][0]['s3']
    bucket_name = s3_info['bucket']['name']
    file_key = s3_info['object']['key']

    file_name = file_key.split("/")[-1]
    unique_file_name = f'{file_name}_{uuid.uuid4()}'
    cleaned_file_name = re.sub(r'[^a-zA-Z0-9-]', '-', unique_file_name)
    
    training_job_name = f'stock-data-training-{cleaned_file_name}'[:63]
    s3_input_data = f's3://{bucket_name}/{file_key}'
    
    response = sagemaker.create_training_job(
        TrainingJobName=training_job_name,
        AlgorithmSpecification={
            'TrainingImage': os.getenv('SAGEMAKER_IMAGE_URI'),
            'TrainingInputMode': 'File'
        },
        RoleArn=os.getenv('SAGEMAKER_ROLE_ARN'),
        InputDataConfig=[
            {
                'ChannelName': 'training',
                'DataSource': {
                    'S3DataSource': {
                        'S3DataType': 'S3Prefix',
                        'S3Uri': s3_input_data,
                        'S3DataDistributionType': 'FullyReplicated'
                    }
                },
                'ContentType': 'text/csv',
                'InputMode': 'File'
            }
        ],
        OutputDataConfig={
            'S3OutputPath': f's3://{bucket_name}/model_output/'
        },
        ResourceConfig={
            'InstanceType': 'ml.m5.large',
            'InstanceCount': 1,
            'VolumeSizeInGB': 10
        },
        StoppingCondition={
            'MaxRuntimeInSeconds': 3600
        },
        Environment={
            'FILE_KEY': file_key,
            'BUCKET_NAME': bucket_name
        }
    )

    return {
        'statusCode': 200,
        'body': json.dumps(f'Training job {training_job_name} created successfully!')
    }
