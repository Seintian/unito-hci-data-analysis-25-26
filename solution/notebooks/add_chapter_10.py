
import json
import pandas as pd

nb_path = r"c:\Users\user\OneDrive\Desktop\IUM\Ciravegna\unito-hci-data-analysis-25-26\solution\notebooks\03_midas_touch.ipynb"

try:
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    cells = nb['cells']
    
    # Locate insertion point (before Conclusions)
    insert_idx = -1
    for i, cell in enumerate(cells):
        source = "".join(cell['source'])
        if "## Conclusions: The Equation of Success" in source:
            insert_idx = i
            break
            
    if insert_idx != -1:
        new_cells = [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Chapter 10: The Dream Team (Consistency Analysis) 🌟\n",
                    "\n",
                    "Success is rarely a solo act. It's often the result of a **\"Dream Team\"** combination.\n",
                    "We visualize the hierarchy of success: **Director → Studio → Composer**.\n",
                    "The Sunburst chart below allows us to explore which combinations produce the most high-rated content (Score > 8.0). Larger segments indicate more hits."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Analysis of The Dream Team (Sunburst)\n",
                    "# We need a dataframe: [Director, Studio, Composer, Count/Score]\n",
                    "# Filter only high rated anime (> 7.5 or 8.0) to see \"Success\"\n",
                    "success_threshold = 8.0\n",
                    "df_hits = df[df['score'] >= success_threshold].copy()\n",
                    "\n",
                    "# We need to parse roles. \n",
                    "# df_person_works has Director and Music roles.\n",
                    "# We merge: Anime -> Studio (in df) -> Director (in works) -> Composer (in works)\n",
                    "\n",
                    "# Prepare roles dataframe\n",
                    "roles = df_person_works[df_person_works['position'].str.contains('Director|Music', case=False, na=False)]\n",
                    "roles = roles.merge(df_person_details[['person_id', 'normalized_name']], on='person_id')\n",
                    "\n",
                    "# Pivot/Group to get Director and Composer per Anime\n",
                    "# Note: An anime can have multiple directors or composers. We'll take the first/primary or explode.\n",
                    "# For simplicity in Sunburst, we'll try to find primary pairs.\n",
                    "\n",
                    "# Get Directors per anime\n",
                    "dirs = roles[roles['position'].str.contains('Director', case=False, na=False)]\n",
                    "dirs_agg = dirs.groupby('anime_id')['normalized_name'].first().reset_index(name='Director')\n",
                    "\n",
                    "# Get Composers per anime\n",
                    "comps = roles[roles['position'].str.contains('Music', case=False, na=False)]\n",
                    "comps_agg = comps.groupby('anime_id')['normalized_name'].first().reset_index(name='Composer')\n",
                    "\n",
                    "# Merge with hits\n",
                    "dream_team = df_hits[['anime_id', 'title', 'studios', 'score']].merge(dirs_agg, on='anime_id', how='left')\n",
                    "dream_team = dream_team.merge(comps_agg, on='anime_id', how='left')\n",
                    "\n",
                    "# Clean\n",
                    "dream_team['Director'] = dream_team['Director'].fillna('Unknown Director')\n",
                    "dream_team['Composer'] = dream_team['Composer'].fillna('Unknown Composer')\n",
                    "dream_team['studios'] = dream_team['studios'].fillna('Unknown Studio')\n",
                    "\n",
                    "# Simplify Studios (take first if list)\n",
                    "def clean_studio(s):\n",
                    "    if pd.isna(s): return \"Unknown\"\n",
                    "    s = str(s).replace(\"['\", \"\").replace(\"']\", \"\").replace(\"'\", \"\")\n",
                    "    return s.split(',')[0].strip()\n",
                    "\n",
                    "dream_team['Studio_Simple'] = dream_team['studios'].apply(clean_studio)\n",
                    "\n",
                    "# Filter for our Target Directors or just Top Directors to avoid clutter?\n",
                    "# Let's use the extended target list + any other high profile ones.\n",
                    "# Or just show the top 20 Directors by number of hits.\n",
                    "top_directors = dream_team['Director'].value_counts().head(15).index.tolist()\n",
                    "dt_filtered = dream_team[dream_team['Director'].isin(top_directors)]\n",
                    "\n",
                    "# Group for Sunburst: Director -> Studio -> Composer\n",
                    "# Value = count of hits\n",
                    "dt_grouped = dt_filtered.groupby(['Director', 'Studio_Simple', 'Composer']).size().reset_index(name='Hits')\n",
                    "\n",
                    "if not dt_grouped.empty:\n",
                    "    fig = px.sunburst(dt_grouped, path=['Director', 'Studio_Simple', 'Composer'], values='Hits',\n",
                    "                      title=f'The Dream Team: Staff Combinations for Hits (Score >= {success_threshold})',\n",
                    "                      color='Hits', color_continuous_scale='RdBu_r')\n",
                    "    fig.show()\n",
                    "else:\n",
                    "    print(\"Not enough data for Sunburst.\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### 💡 Insight: The Winning Formula\n",
                    "- **Director-Centric**: The central ring shows who drives the success.\n",
                    "- **Studio Loyalty**: Interpretation of the second ring. Does the director stick to one studio (e.g., Miyazaki/Ghibli) or move around?\n",
                    "- **Musical Partners**: The outer ring reveals frequent collaborations. A large segment for a specific Composer (e.g., Shinkai/Radwimps) indicates a deeply integrated creative partnership."
                ]
            }
        ] # End new cells
        
        for cell in reversed(new_cells):
            cells.insert(insert_idx, cell)
            
        with open(nb_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=4)
        print("Inserted Chapter 10.")

except Exception as e:
    print(f"Error: {e}")
