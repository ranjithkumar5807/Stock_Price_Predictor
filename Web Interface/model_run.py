import sys
import json
import joblib
import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
import os

# Get stock name from command-line argument
stock = sys.argv[1].upper()

# Define stock-specific folder path
stock_folder = os.path.join("./models", stock)

# Load Model
model = load_model(os.path.join(stock_folder, f'GRU_model.h5'))

# Load Scaler
scaler = joblib.load(os.path.join(stock_folder, f'scaler.pkl'))

# Load Features List
with open(os.path.join(stock_folder, f'features.json'), 'r') as f:
    features = json.load(f)

# Load Sequence Length
with open(os.path.join(stock_folder, f'sequence_length.txt'), 'r') as f:
    sequence_length = int(f.read().strip())

# Load dataset
data = pd.read_csv(f"https://raw.githubusercontent.com/ranjithkumar5807/stock-prediction/refs/heads/main/technical%20indicators/{stock}.NS_indicators.csv")

# Ensure 'close' column exists
if 'close' not in data.columns:
    raise ValueError(f"'close' column not found in dataset for {stock}")

# Select relevant features
selected_features = features

# Compute missing indicators
if 'SMA_10' not in data.columns:
    data['SMA_10'] = data['close'].rolling(window=10).mean()
if 'SMA_21' not in data.columns:
    data['SMA_21'] = data['close'].rolling(window=21).mean()

# Drop NaN values caused by rolling calculations
data.dropna(inplace=True)

# Normalize the data
scaled_data = scaler.transform(data[selected_features])

# Extract the last `sequence_length` rows for prediction
X_latest = np.array([scaled_data[-sequence_length:]])  # Shape (1, sequence_length, num_features)

# Predict next-day close price
y_pred = model.predict(X_latest)

# Reconstruct the original approach for inverse transformation
y_pred_rescaled = np.zeros_like(scaled_data[-1:])  # Create zero-filled array
y_pred_rescaled[:, 0] = y_pred[:, 0]  # Assign predicted close price to first column

# Inverse transform only the close price
y_pred_actual = scaler.inverse_transform(y_pred_rescaled)[:, 0][0]

# Get the last closing price
last_close = data['close'].iloc[-1]

# Calculate actual 5-day and 10-day percentage changes
if len(data) >= 10:  # Ensure enough data exists
    close_5_days_ago = data['close'].iloc[-6]  # 5 days ago (including current day)
    close_10_days_ago = data['close'].iloc[-11]  # 10 days ago

    change_5_days = ((last_close - close_5_days_ago) / close_5_days_ago) * 100
    change_10_days = ((last_close - close_10_days_ago) / close_10_days_ago) * 100
else:
    change_5_days, change_10_days = None, None  # Not enough data

# Store results in a dictionary
output_data = {
    "predicted_close": round(y_pred_actual, 2),
    "change_5_days": round(change_5_days, 2) if change_5_days is not None else None,
    "change_10_days": round(change_10_days, 2) if change_10_days is not None else None
}

# Write results to a JSON file
output_file = os.path.join('./output', f'{stock}.json')
with open(output_file, "w") as f:
    json.dump(output_data, f, indent=4)

print(f"Prediction saved to {output_file}")

