
import json
import pandas as pd

nb_path = r"c:\Users\user\OneDrive\Desktop\IUM\Ciravegna\unito-hci-data-analysis-25-26\solution\notebooks\03_midas_touch.ipynb"

try:
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    cells = nb['cells']
    
    for cell in cells:
        if cell['cell_type'] == 'code' and "Analysis of Longevity" in "".join(cell['source']):
            new_source = [
                "# Analysis of Longevity (Cumulative Members) - Robust go.Figure Animation\n",
                "import plotly.graph_objects as go\n",
                "import pandas as pd\n",
                "import numpy as np\n",
                "\n",
                "# 1. Data Preparation\n",
                "target_directors = ['Hayao Miyazaki', 'Makoto Shinkai', 'Masaaki Yuasa', 'Hideaki Anno', \n",
                "                    'Mamoru Hosoda', 'Naoko Yamada', 'Shinichirou Watanabe']\n",
                "\n",
                "def local_normalize(name):\n",
                "    if pd.isna(name): return \"Unknown\"\n",
                "    name = str(name).strip()\n",
                "    if ',' in name:\n",
                "        parts = name.split(',')\n",
                "        if len(parts) >= 2:\n",
                "            return f\"{parts[1].strip()} {parts[0].strip()}\"\n",
                "    return name\n",
                "\n",
                "# Normalize again locally to be 100% sure\n",
                "df_p_details = df_person_details.copy()\n",
                "df_p_details['norm_name'] = df_p_details['name'].apply(local_normalize)\n",
                "\n",
                "director_works = df_person_works[df_person_works['position'].str.contains('Director', case=False, na=False)]\n",
                "director_full = director_works.merge(df_p_details[['person_id', 'norm_name']], on='person_id')\n",
                "director_target = director_full[director_full['norm_name'].isin(target_directors)]\n",
                "director_anime = director_target.merge(df[['anime_id', 'title', 'members', 'start_date']], on='anime_id')\n",
                "\n",
                "director_anime['year'] = pd.to_datetime(director_anime['start_date'], errors='coerce').dt.year\n",
                "director_anime = director_anime.dropna(subset=['year'])\n",
                "director_anime['year'] = director_anime['year'].astype(int)\n",
                "\n",
                "print(f\"Found {len(director_anime)} titles for {len(director_anime['norm_name'].unique())} target directors.\")\n",
                "\n",
                "# Aggregate\n",
                "yearly_stats = director_anime.groupby(['norm_name', 'year'])['members'].sum().reset_index()\n",
                "yearly_stats.columns = ['Director', 'Year', 'Yearly_Members']\n",
                "\n",
                "# Build Cumulative Table\n",
                "all_years = sorted(director_anime['year'].unique())\n",
                "grid = pd.MultiIndex.from_product([target_directors, all_years], names=['Director', 'Year']).to_frame(index=False)\n",
                "df_longevity = grid.merge(yearly_stats, on=['Director', 'Year'], how='left').fillna(0)\n",
                "df_longevity = df_longevity.sort_values(['Director', 'Year'])\n",
                "df_longevity['Cumulative Members'] = df_longevity.groupby('Director')['Yearly_Members'].cumsum()\n",
                "\n",
                "# 2. Create Figure with plotly.graph_objects (More stable for lines)\n",
                "max_y = df_longevity['Cumulative Members'].max() * 1.1\n",
                "fig = go.Figure(\n",
                "    layout=go.Layout(\n",
                "        title=\"Longevity of Success: Cumulative Audience Growth over Career\",\n",
                "        xaxis=dict(range=[min(all_years), max(all_years)], title=\"Year\"),\n",
                "        yaxis=dict(range=[0, max_y], title=\"Cumulative Members\"),\n",
                "        updatemenus=[dict(\n",
                "            type=\"buttons\",\n",
                "            buttons=[dict(label=\"Play\", method=\"animate\", args=[None, {\"frame\": {\"duration\": 50, \"redraw\": True}, \"fromcurrent\": True}]),\n",
                "                     dict(label=\"Pause\", method=\"animate\", args=[[None], {\"frame\": {\"duration\": 0, \"redraw\": False}, \"mode\": \"immediate\", \"transition\": {\"duration\": 0}}])]\n",
                "        )]\n",
                "    )\n",
                ")\n",
                "\n",
                "# Add Initial Traces (first year)\n",
                "first_year = min(all_years)\n",
                "for director in target_directors:\n",
                "    d_data = df_longevity[(df_longevity['Director'] == director) & (df_longevity['Year'] <= first_year)]\n",
                "    fig.add_trace(go.Scatter(x=d_data['Year'], y=d_data['Cumulative Members'], name=director, mode='lines+markers'))\n",
                "\n",
                "# Add Frames\n",
                "frames = []\n",
                "for y in all_years:\n",
                "    frame_traces = []\n",
                "    for director in target_directors:\n",
                "        d_data = df_longevity[(df_longevity['Director'] == director) & (df_longevity['Year'] <= y)]\n",
                "        frame_traces.append(go.Scatter(x=d_data['Year'], y=d_data['Cumulative Members']))\n",
                "    frames.append(go.Frame(data=frame_traces, name=str(y)))\n",
                "\n",
                "fig.frames = frames\n",
                "fig.show()"
            ]
            cell['source'] = new_source
            print("Implemented go.Figure logic for Chapter 9.")
            break

    with open(nb_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=4)
    print("Notebook saved.")

except Exception as e:
    print(f"Error: {e}")
