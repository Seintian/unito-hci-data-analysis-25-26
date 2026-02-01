
import pandas as pd
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def norm(name):
    if pd.isna(name): return str(name)
    if ',' in str(name):
        parts = str(name).split(',')
        if len(parts) >= 2:
             return f"{parts[1].strip()} {parts[0].strip()}"
    return str(name)

try:
    print("Loading data...")
    base = r"c:\Users\user\OneDrive\Desktop\IUM\Ciravegna\unito-hci-data-analysis-25-26\data\processed"
    details = pd.read_parquet(f"{base}\\details.parquet")
    print("Details cols:", details.columns.tolist())
    print("Status counts:\n", details['status'].value_counts())
    
    if 'score' in details.columns:
        print("Score in details")
    
    stats = pd.read_parquet(f"{base}\\stats.parquet")
    print("Stats cols:", stats.columns.tolist())
    
    works = pd.read_parquet(f"{base}\\person_anime_works.parquet")
    people = pd.read_parquet(f"{base}\\person_details.parquet")
    
    people['normalized_name'] = people['name'].apply(norm)
    
    # Directors
    print("\n--- Directors & Airing ---")
    targets = ['Hayao Miyazaki', 'Makoto Shinkai', 'Masaaki Yuasa', 'Hideaki Anno', 'Mamoru Hosoda', 'Naoko Yamada', 'Shinichirou Watanabe']
    
    d_works = works[works['position'].str.contains('Director', case=False, na=False)]
    d_full = d_works.merge(people, on='person_id')
    d_target = d_full[d_full['normalized_name'].isin(targets)]
    d_anime = d_target.merge(details, on='anime_id')
    
    airing_directors = d_anime[d_anime['status'] == 'Currently Airing']
    print(airing_directors[['normalized_name', 'title']])
    
    # Studios
    print("\n--- Studios & Airing ---")
    s_targets = ['Kyoto Animation', 'Madhouse', 'MAPPA', 'Bones', 'Sunrise', 'A-1 Pictures', 'J.C.Staff', 'Studio Ghibli', 'ufotable', 'Production I.G']
    for s in s_targets:
        cnt = details[details['studios'].astype(str).str.contains(s, na=False) & (details['status'] == 'Currently Airing')].shape[0]
        print(f"{s}: {cnt}")

except Exception as e:
    print(f"Error: {e}")
