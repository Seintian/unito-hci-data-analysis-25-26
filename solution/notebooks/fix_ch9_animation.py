
import json
import pandas as pd

nb_path = r"c:\Users\user\OneDrive\Desktop\IUM\Ciravegna\unito-hci-data-analysis-25-26\solution\notebooks\03_midas_touch.ipynb"

try:
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    cells = nb['cells']
    
    for cell in cells:
        if cell['cell_type'] == 'code' and "Analysis of Longevity (Cumulative Members)" in "".join(cell['source']):
            new_source = [
                "# Analysis of Longevity (Cumulative Members)\n",
                "import plotly.express as px\n",
                "import pandas as pd\n",
                "\n",
                "# Filter for Target Directors\n",
                "target_directors = ['Hayao Miyazaki', 'Makoto Shinkai', 'Masaaki Yuasa', 'Hideaki Anno', \n",
                "                    'Mamoru Hosoda', 'Naoko Yamada', 'Shinichirou Watanabe']\n",
                "\n",
                "# Get Director Works with Date\n",
                "director_works = df_person_works[df_person_works['position'].str.contains('Director', case=False, na=False)]\n",
                "director_full = director_works.merge(df_person_details[['person_id', 'normalized_name']], on='person_id')\n",
                "director_target = director_full[director_full['normalized_name'].isin(target_directors)]\n",
                "director_anime = director_target.merge(df[['anime_id', 'title', 'members', 'start_date']], on='anime_id')\n",
                "\n",
                "# Extract Year\n",
                "director_anime['year'] = pd.to_datetime(director_anime['start_date'], errors='coerce').dt.year\n",
                "director_anime = director_anime.dropna(subset=['year'])\n",
                "director_anime['year'] = director_anime['year'].astype(int)\n",
                "\n",
                "# 1. Create a complete grid (Director x Year) to ensure smooth animation frames\n",
                "all_years = sorted(director_anime['year'].unique())\n",
                "grid = pd.MultiIndex.from_product([target_directors, all_years], names=['Director', 'Year']).to_frame(index=False)\n",
                "\n",
                "# 2. Aggregate members per director/year\n",
                "yearly_stats = director_anime.groupby(['normalized_name', 'year'])['members'].sum().reset_index()\n",
                "yearly_stats.columns = ['Director', 'Year', 'Yearly_Members']\n",
                "\n",
                "# 3. Merge grid with stats and calculate Cumulative Growth\n",
                "df_longevity = grid.merge(yearly_stats, on=['Director', 'Year'], how='left').fillna(0)\n",
                "df_longevity = df_longevity.sort_values(['Director', 'Year'])\n",
                "df_longevity['Cumulative Members'] = df_longevity.groupby('Director')['Yearly_Members'].cumsum()\n",
                "\n",
                "if not df_longevity.empty:\n",
                "    # Create binary feature to only show traces after their debut (optional, but let's keep traces from 0 for consistency)\n",
                "    fig = px.line(df_longevity, \n",
                "                  x=\"Year\", \n",
                "                  y=\"Cumulative Members\", \n",
                "                  color=\"Director\",\n",
                "                  line_group=\"Director\", # Vital for line animations\n",
                "                  animation_frame=\"Year\", \n",
                "                  title=\"Longevity of Success: Cumulative Audience Growth over Career\",\n",
                "                  range_x=[min(all_years), max(all_years)],\n",
                "                  range_y=[0, df_longevity['Cumulative Members'].max() * 1.1])\n",
                "\n",
                "    # Set markers to see data points\n",
                "    fig.update_traces(mode='lines+markers')\n",
                "    \n",
                "    # Adjust animation settings for smoother playback\n",
                "    fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 200\n",
                "    fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 100\n",
                "    \n",
                "    fig.show()\n",
                "else:\n",
                "    print(\"Not enough data for Longevity Analysis.\")\n"
            ]
            cell['source'] = new_source
            print("Fixed Chapter 9 cell.")
            break

    with open(nb_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=4)
    print("Notebook saved.")

except Exception as e:
    print(f"Error: {e}")
