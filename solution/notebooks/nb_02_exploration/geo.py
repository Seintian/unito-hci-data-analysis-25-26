import pandas as pd

def generate_user_map(df_profiles: pd.DataFrame) -> None:
    """
    Stub for creating user density map.
    Full implementation requires cleaning 'location' string to ISO codes.
    For now, we will print a summary of top locations.
    """

    print("Generating location summary...")

    if 'location' not in df_profiles.columns:
        print("No 'location' column found.")
        return

    # Basic cleaning

    top_locs = df_profiles['location'].value_counts().head(20)

    # Check for empty entries
    missing = df_profiles['location'].isna().sum()
    print(f"Missing locations: {missing}")

    print("Top 20 User Locations:")
    return top_locs
