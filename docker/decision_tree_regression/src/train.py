import os
import argparse
import boto3
import pandas as pd
import io
from sklearn.tree import DecisionTreeRegressor
import joblib

def load_csv_from_s3(bucket_name, file_key):
    s3_client = boto3.client('s3')
    csv_obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    
    body = csv_obj['Body'].read().decode('utf-8')
    data = pd.read_csv(io.StringIO(body))
    
    return data
    
def upload_model_to_s3(model, bucket_name, model_key):
    s3_client = boto3.client('s3')
    
    # Save the model to a local file
    model_local_path = '/tmp/decision_tree_model.joblib'
    joblib.dump(model, model_local_path)
    
    # Upload the model to S3
    with open(model_local_path, 'rb') as model_file:
        s3_client.upload_fileobj(model_file, bucket_name, model_key)
    
    
    print(f"Model uploaded to s3://{bucket_name}/{model_key}")

def train():
    file_key = os.getenv('FILE_KEY')
    bucket_name = os.getenv('BUCKET_NAME')

    # Load the dataset from S3
    data = load_csv_from_s3(bucket_name, file_key)
    
    # Feature selection and target variable
    X = data[['open', 'high', 'low', 'volume', 'sma_14', 'ema_14', 'rsi', 'volatility']]
    y = data['close']

    # Create and train the decision tree regression model
    model = DecisionTreeRegressor(max_depth=10, random_state=42)
    model.fit(X, y)

    # Define the S3 key for the model
    model_key = 'training/models/decision_tree_model.joblib'
    
    # Upload the trained model to S3
    upload_model_to_s3(model, bucket_name, model_key)

if __name__ == '__main__':
    train()