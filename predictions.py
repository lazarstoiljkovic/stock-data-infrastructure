import boto3
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# AWS S3 konfiguracija
bucket_name = 'stock-data-607282882839-us-east-1'
#longer period for training data set (1-day interval)
#predictions_file_key = 'predictions/predictions_88d190db-52a0-424d-ad6a-f6fc8cd7cce4.csv'
#actuals_file_key = 'actuals/actuals_38be0d76-d431-4643-b520-bc16a81f2374.csv'

#shorter period training data set(1-day interval)
#predictions_file_key = 'predictions/predictions_c7118619-5461-4ecc-9465-951caec4571e.csv'
#actuals_file_key = 'actuals/actuals_aaddcb66-b1f3-480f-9952-3f501fd4a824.csv'

#(1-hour interval)
#predictions_file_key = 'predictions/predictions_01a7be34-4fad-44ee-9f21-93976cc4d303.csv'
#actuals_file_key = 'actuals/actuals_316ddbff-6714-45d4-a0f4-cd22f75de4f6.csv'

#(1-week interval)
predictions_file_key = 'predictions/predictions_1a2cba20-8f22-42f9-9793-b2c41b652337.csv'
actuals_file_key = 'actuals/actuals_39d793b2-485d-493c-b36f-9b4ba84f6b7a.csv'

# Funkcija za preuzimanje CSV fajla sa S3
def download_csv_from_s3(bucket_name, file_key):
    s3_client = boto3.client('s3')
    obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    return pd.read_csv(obj['Body'])

# Funkcija za evaluaciju modela
def evaluate_model(actuals, predictions):
    # Računanje MSE, MAE i R2
    mse = mean_squared_error(actuals, predictions)
    mae = mean_absolute_error(actuals, predictions)
    r2 = r2_score(actuals, predictions)

    # Ispisivanje rezultata
    print(f"Mean Squared Error: {mse:.4f}")
    print(f"Mean Absolute Error: {mae:.4f}")
    print(f"R2 Score: {r2:.4f}")


# Preuzimanje podataka sa S3
predictions_df = download_csv_from_s3(bucket_name, predictions_file_key)
actuals_df = download_csv_from_s3(bucket_name, actuals_file_key)

# Konvertujte 'date' kolonu u datetime format
predictions_df['date'] = pd.to_datetime(predictions_df['date'])
actuals_df['date'] = pd.to_datetime(actuals_df['date'])

# Prikaz podataka
print("Predictions Data:")
print(predictions_df.head())
print("\nActuals Data:")
print(actuals_df.head())

# Vizualizacija predikcija i stvarnih vrednosti
plt.figure(figsize=(12, 8))

# Plot za predikcije
plt.plot(predictions_df['date'], predictions_df['close'], marker='o', linestyle='-', color='b', markersize=4, linewidth=2, label='Predictions')

# Plot za stvarne vrednosti
plt.plot(actuals_df['date'], actuals_df['close'], marker='x', linestyle='--', color='r', markersize=6, linewidth=2, label='Actuals')

# Naslovi i oznake sa većim fontovima
plt.title('Predictions vs Actuals Over Time', fontsize=16, fontweight='bold')
plt.xlabel('Date', fontsize=14)
plt.ylabel('Value', fontsize=14)

# Povećajte kontrast mreže
plt.grid(True, which='both', linestyle='--', linewidth=0.5)

# Podesite oznake na x-osi ako imate puno podataka (ako je potrebno)
if len(predictions_df) > 50:
    plt.xticks(rotation=45, fontsize=12)
else:
    plt.xticks(fontsize=12)

# Povećajte font za y-osi
plt.yticks(fontsize=12)

# Dodajte legendu
plt.legend(fontsize=12)

# Prikazivanje grafikona
plt.tight_layout()  # Podesite raspored da se izbegne preklapanje
plt.show()

# Evaluacija modela
# Ako su predikcije i stvarni podaci iste duzine, možemo izračunati evaluacijske metrike
if len(predictions_df) == len(actuals_df):
    y_true = actuals_df['close']
    y_pred = predictions_df['close']

    evaluate_model(y_true, y_pred)
else:
    print("Warning: The number of predictions and actuals do not match!")




