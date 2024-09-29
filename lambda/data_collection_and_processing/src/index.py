import os
import json
import csv
import requests
import boto3
import pandas as pd
from io import StringIO
from datetime import datetime
import uuid

s3 = boto3.client('s3')

def calculate_sma(data, window):
    return data['close'].rolling(window=window).mean()

def calculate_ema(data, window):
    return data['close'].ewm(span=window, adjust=False).mean()

def calculate_rsi(data, window):
    delta = data['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_volatility(data, window):
    return data['close'].rolling(window=window).std()

def handler(event, context):
    polygon_api_key = os.getenv('POLYGON_API_KEY')
    s3_bucket = os.getenv('S3_BUCKET')

    body = json.loads(event['body'])
    
    multiplier = body.get('multiplier', 1)
    timespan = body.get('timespan', 'day')
    from_date = body.get('from', '2024-08-01')
    to_date = body.get('to', '2024-08-31')
    stock_symbol = body.get('stock_symbol', 'AAPL')

    polygon_url = f"https://api.polygon.io/v2/aggs/ticker/{stock_symbol}/range/{multiplier}/{timespan}/{from_date}/{to_date}?adjusted=true&apiKey={polygon_api_key}"

    response = requests.get(polygon_url)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': json.dumps('Greška prilikom preuzimanja podataka.')
        }

    data = response.json()

    cleaned_data = []
    for result in data.get('results', []):
        if 'c' in result and 'h' in result and 'l' in result and 'o' in result and 't' in result and 'v' in result:
            timestamp = result['t']
            result['date'] = datetime.utcfromtimestamp(timestamp / 1000.0).strftime('%Y-%m-%d')
            cleaned_data.append({
                'open': result['o'],  # Open
                'high': result['h'],  # High
                'low': result['l'],   # Low
                'close': result['c'],  # Close
                'volume': result['v'],  # Volume
                'date': result['date']  # Date
            })

    df = pd.DataFrame(cleaned_data)
    df.columns = ['open', 'high', 'low', 'close', 'volume', 'date']

    df['sma_14'] = calculate_sma(df, 14)
    df['ema_14'] = calculate_ema(df, 14)
    df['rsi'] = calculate_rsi(df, 14)
    df['volatility'] = calculate_volatility(df, 14)

    df = df.dropna(subset=['sma_14', 'ema_14', 'rsi', 'volatility'])

    original_file_name = f'training/raw/stock_data_{stock_symbol}_{datetime.utcnow().strftime("%Y-%m-%d")}_{uuid.uuid4()}.json'
    s3.put_object(
        Bucket=s3_bucket,
        Key=original_file_name,
        Body=json.dumps(data),
        ContentType='application/json'
    )

    csv_buffer = StringIO()
    csv_writer = csv.writer(csv_buffer)

    csv_writer.writerow(['date', 'open', 'high', 'low', 'close', 'volume', 'sma_14', 'ema_14', 'rsi', 'volatility'])

    for index, result in df.iterrows():
        csv_writer.writerow([
            result.get('date'),
            result.get('open'),  # Open
            result.get('high'),  # High
            result.get('low'),  # Low
            result.get('close'),  # Close
            result.get('volume'),  # Volume
            result.get('sma_14'),
            result.get('ema_14'),
            result.get('rsi'),
            result.get('volatility')
        ])

    processed_file_name = f'training/processed/stock_data_{stock_symbol}_{datetime.utcnow().strftime("%Y-%m-%d")}_{uuid.uuid4()}.csv'
    s3.put_object(
        Bucket=s3_bucket,
        Key=processed_file_name,
        Body=csv_buffer.getvalue(),
        ContentType='text/csv'
    )

    original_file_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': s3_bucket, 'Key': original_file_name},
        ExpiresIn=3600
    )

    processed_file_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': s3_bucket, 'Key': processed_file_name},
        ExpiresIn=3600
    )

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Podaci uspešno sačuvani.',
            'original_file_url': original_file_url,
            'processed_file_url': processed_file_url
        })
    }
