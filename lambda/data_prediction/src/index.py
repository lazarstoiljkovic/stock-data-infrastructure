import json
import boto3
import joblib
import pandas as pd
import os
import uuid
from io import StringIO

# Preuzimanje modela iz S3
def download_model_from_s3(bucket_name, model_key):
    s3_client = boto3.client('s3')
    model_local_path = '/tmp/linear_regression_model.joblib'
    
    # Preuzmi model u privremeni direktorijum /tmp (Lambda ima pristup samo tom direktorijumu)
    s3_client.download_file(bucket_name, model_key, model_local_path)
    print(f"Model preuzet sa s3://{bucket_name}/{model_key}")

    return model_local_path

# Učitavanje modela iz lokalnog fajla
def load_model(model_path):
    model = joblib.load(model_path)
    return model

# Preuzimanje test skupa iz S3
def download_test_data_from_s3(bucket_name, test_data_key):
    s3_client = boto3.client('s3')
    csv_local_path = '/tmp/test_data.csv'
    
    # Preuzmi test skup u privremeni direktorijum
    s3_client.download_file(bucket_name, test_data_key, csv_local_path)
    print(f"Test data preuzet sa s3://{bucket_name}/{test_data_key}")
    
    # Učitaj podatke u DataFrame
    test_data = pd.read_csv(csv_local_path)
    
    # Ukloni kolone 'close' i 'date' iz test skupa za predikciju, ali ih zadrži za kasnije
    date_column = test_data['date']
    close_column = test_data['close']
    test_data = test_data.drop(columns=['close', 'date'], errors='ignore')
    
    return test_data, date_column, close_column

# Funckija za predikciju
def predict(model, input_data):
    return model.predict(input_data)

# Čuvanje predikcija u S3
def save_predictions_to_s3(bucket_name, dates, predictions, key_prefix='predictions/'):
    s3_client = boto3.client('s3')
    csv_buffer = StringIO()
    
    # Kreiraj DataFrame sa predikcijama, datumima i stvarnim vrednostima
    predictions_df = pd.DataFrame({
        'date': dates,
        'close': predictions,
    })
    
    # Snimi predikcije u CSV
    predictions_df.to_csv(csv_buffer, index=False)
    
    # Generiši jedinstveno ime fajla
    file_key = f"{key_prefix}predictions_{uuid.uuid4()}.csv"
    
    # Snimi fajl u S3
    s3_client.put_object(Bucket=bucket_name, Key=file_key, Body=csv_buffer.getvalue())
    print(f"Predictions saved to s3://{bucket_name}/{file_key}")
    return file_key

# Čuvanje stvarnih podataka u S3
def save_actuals_to_s3(bucket_name, dates, closes, key_prefix='actuals/'):
    s3_client = boto3.client('s3')
    csv_buffer = StringIO()
    
    # Kreiraj DataFrame sa stvarnim vrednostima
    actuals_df = pd.DataFrame({
        'date': dates,
        'close': closes
    })
    
    # Snimi stvarne vrednosti u CSV
    actuals_df.to_csv(csv_buffer, index=False)
    
    # Generiši jedinstveno ime fajla
    file_key = f"{key_prefix}actuals_{uuid.uuid4()}.csv"
    
    # Snimi fajl u S3
    s3_client.put_object(Bucket=bucket_name, Key=file_key, Body=csv_buffer.getvalue())
    print(f"Actuals saved to s3://{bucket_name}/{file_key}")
    return file_key


# Lambda handler funkcija
def handler(event, context):
    # S3 parametri (menjaj prema potrebi)
    bucket_name = os.getenv('BUCKET_NAME')
    model_key = 'models/linear_regression_model.joblib'

    # Preuzmi i učitaj model
    model_path = download_model_from_s3(bucket_name, model_key)
    model = load_model(model_path)

    # Dobijanje input podataka iz API Gateway-a (u JSON formatu)
    try:
        input_data = json.loads(event['body'])
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps(f"Invalid input format: {e}")
        }

    test_data_key = input_data.get('test_data_key')

    # Preuzmi test skup
    try:
        test_data, dates, closes = download_test_data_from_s3(bucket_name, test_data_key)
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error loading test data: {e}")
        }

    # Napravi predikciju
    try:
        predictions = predict(model, test_data)
        
        # Sačuvaj predikcije i stvarne vrednosti u S3
        predictions_key = save_predictions_to_s3(bucket_name, dates, predictions)
        actuals_key = save_actuals_to_s3(bucket_name, dates, closes)
        
        response = {
            'predictions_s3_key': predictions_key,
            'actuals_s3_key': actuals_key
        }
        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error during prediction: {e}")
        }