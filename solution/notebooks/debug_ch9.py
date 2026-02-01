
import pandas as pd
import json

# Paths
base_data = r"c:\Users\user\OneDrive\Desktop\IUM\Ciravegna\unito-hci-data-analysis-25-26\data\processed"
nb_path = r"c:\Users\user\OneDrive\Desktop\IUM\Ciravegna\unito-hci-data-analysis-25-26\solution\notebooks\03_midas_touch.ipynb"

try:
    # Mimic notebook state
    df_details = pd.read_parquet(f"{base_data}\\details.parquet")
    df_stats = pd.read_parquet(f"{base_data}\\stats.parquet")
    df = df_details.merge(df_stats, on="anime_id", how="inner")
    
    df_person_works = pd.read_parquet(f"{base_data}\\person_anime_works.parquet")
    df_person_details = pd.read_parquet(f"{base_data}\\person_details.parquet")
    
    # Simple normalization Logic like in NB
    def norm_name(name):
        if pd.isna(name): return name
        name = str(name)
        if ',' in name:
            parts = name.split(',')
            if len(parts) >= 2:
                return f"{parts[1].strip()} {parts[0].strip()}"
        return name
    
    df_person_details['normalized_name'] = df_person_details['name'].apply(norm_name)
    
    # Chapter 9 Logic
    target_directors = ['Hayao Miyazaki', 'Makoto Shinkai', 'Masaaki Yuasa', 'Hideaki Anno', 
                        'Mamoru Hosoda', 'Naoko Yamada', 'Shinichirou Watanabe']

    director_works = df_person_works[df_person_works['position'].str.contains('Director', case=False, na=False)]
    director_full = director_works.merge(df_person_details[['person_id', 'normalized_name']], on='person_id')
    director_target = director_full[director_full['normalized_name'].isin(target_directors)]
    
    print(f"Directors found in targets: {director_target['normalized_name'].unique()}")
    
    director_anime = director_target.merge(df[['anime_id', 'title', 'members', 'start_date']], on='anime_id')
    print(f"Anime count after merge: {len(director_anime)}")
    
    director_anime['year'] = pd.to_datetime(director_anime['start_date'], errors='coerce').dt.year
    print(f"NaT years: {director_anime['year'].isna().sum()}")
    print(director_anime[['title', 'start_date', 'year']].head())
    
    director_anime = director_anime.dropna(subset=['year'])
    director_anime['year'] = director_anime['year'].astype(int)
    
    min_year = director_anime['year'].min()
    max_year = director_anime['year'].max()
    print(f"Year range: {min_year} - {max_year}")
    
    # Check if df_longevity gets populated
    longevity_data = []
    all_years = list(range(int(min_year), int(max_year) + 1))
    
    for director in target_directors:
        d_df = director_anime[director_anime['normalized_name'] == director]
        current_members = 0
        for year in all_years:
            new_members = d_df[d_df['year'] == year]['members'].sum()
            current_members += new_members
            if not d_df.empty and year >= d_df['year'].min():
                longevity_data.append({
                    'Director': director,
                    'Year': year,
                    'Cumulative Members': current_members
                })
    
    df_longevity = pd.DataFrame(longevity_data)
    print(f"Longevity data rows: {len(df_longevity)}")
    if not df_longevity.empty:
        print(df_longevity.head())
        print(df_longevity.groupby('Director').size())

except Exception as e:
    print(f"Error: {e}")
