import os
import argparse
import boto3
import pandas as pd
import io
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
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
    model_local_path = '/tmp/linear_regression_model.joblib'
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

    # Split data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Create and train the linear regression model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Evaluate the model
    score = model.score(X_test, y_test)
    print(f"Model R^2 score: {score}")

    # Define the S3 key for the model
    model_key = 'training/models/linear_regression_model.joblib'  # Change the path as needed
    
    # Upload the trained model to S3
    upload_model_to_s3(model, bucket_name, model_key)

if __name__ == '__main__':
    train()
