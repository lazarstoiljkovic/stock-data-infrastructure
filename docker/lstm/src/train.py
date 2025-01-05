import os
import argparse
import boto3
import pandas as pd
import io
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import numpy as np
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
    model_local_path = '/tmp/lstm_model.joblib'
    joblib.dump(model, model_local_path)
    
    # Upload the model to S3
    with open(model_local_path, 'rb') as model_file:
        s3_client.upload_fileobj(model_file, bucket_name, model_key)
    
    
    print(f"Model uploaded to s3://{bucket_name}/{model_key}")

def train_lstm(data):
    # Priprema podataka
    X = data[['open', 'high', 'low', 'volume', 'sma_14', 'ema_14', 'rsi', 'volatility']].values
    y = data['close'].values
    
    # Pretvaranje podataka u sekvencijalni oblik
    X = np.array([X[i:i+30] for i in range(len(X)-30)])  # 30 dana unazad
    y = y[30:]
    
    # Definisanje LSTM modela
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
        LSTM(50),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    
    # Treniranje modela
    model.fit(X, y, epochs=10, batch_size=32)
    
    # Define the S3 key for the model
    model_key = 'training/models/lstm_model.joblib'
    
    # Upload the trained model to S3
    upload_model_to_s3(model, bucket_name, model_key)

if __name__ == '__main__':
    train()