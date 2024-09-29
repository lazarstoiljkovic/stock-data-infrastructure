import json
import boto3
import joblib
import pandas as pd
import os

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

# Funckija za predikciju
def predict(model, input_data):
    return model.predict(input_data)

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

    # Pretvori input podatke u DataFrame
    df_input = pd.DataFrame(input_data)

    # Napravi predikciju
    try:
        predictions = predict(model, df_input)
        response = {
            'predictions': predictions.tolist()  # Pretvori u listu za JSON odgovor
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
