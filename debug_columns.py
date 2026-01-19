import pandas as pd

details_path = r'data\processed\details.parquet'
stats_path = r'data\processed\stats.parquet'

print(f"Checking {details_path}...")
try:
    df_details = pd.read_parquet(details_path)
    print("--- df_details ---")
    print(f"Index name: {df_details.index.name}")
    print(f"Columns relevant: {[c for c in df_details.columns if 'anime' in c]}")
    print(f"Is 'anime_id' in columns? {'anime_id' in df_details.columns}")
except Exception as e:
    print(f"Error: {e}")

print(f"\nChecking {stats_path}...")
try:
    df_stats = pd.read_parquet(stats_path)
    print("--- df_stats ---")
    print(f"Index name: {df_stats.index.name}")
    print(f"Columns relevant: {[c for c in df_stats.columns if 'anime' in c]}")
    print(f"Is 'anime_id' in columns? {'anime_id' in df_stats.columns}")
except Exception as e:
    print(f"Error: {e}")
