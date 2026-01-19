import pandas as pd
try:
    df = pd.read_parquet(r'data\processed\details.parquet')
    print(f"INDEX_NAME: {df.index.name}")
    print(f"COLUMNS: {df.columns.tolist()}")
except Exception as e:
    print(e)
