import pandas as pd
try:
    df = pd.read_parquet(r'data\processed\stats.parquet')
    print(f"COLUMNS: {df.columns.tolist()}")
except Exception as e:
    print(e)
