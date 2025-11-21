import os
import pandas as pd
from fredapi import Fred
from dotenv import load_dotenv

# Load keys from .env file
load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")

fred = Fred(api_key=FRED_API_KEY)

# Example: 10-Year Treasury Yield
series_id = "DGS10"

print("Downloading data...")
data = fred.get_series(series_id)

# Clean the data
df = pd.DataFrame(data, columns=["value"])
df.index.name = "date"
df.reset_index(inplace=True)

# Save
df.to_csv("10yr_treasury_yield.csv", index=False)

print("Saved 10yr_treasury_yield.csv")

