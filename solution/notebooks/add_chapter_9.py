
import json
import pandas as pd

nb_path = r"c:\Users\user\OneDrive\Desktop\IUM\Ciravegna\unito-hci-data-analysis-25-26\solution\notebooks\03_midas_touch.ipynb"

try:
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    cells = nb['cells']
    
    # Locate insertion point (Conclusion)
    insert_idx = -1
    for i, cell in enumerate(cells):
        source = "".join(cell['source'])
        if "## Conclusions: The Equation of Success" in source:
            insert_idx = i
            break
            
    if insert_idx != -1:
        # Chapter 9 Content
        new_cells = [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Chapter 9: Longevity of Success (Trend over Time) ⏳\n",
                    "\n",
                    "How does the popularity of an author's work grow over the years?\n",
                    "We visualize the **Cumulative Members** count for top directors, animated by year of release.\n",
                    "Do Miyazaki's classics accumulate fans faster than modern hits? Does a director's career accelerate over time?"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Analysis of Longevity (Cumulative Members)\n",
                    "import plotly.express as px\n",
                    "\n",
                    "# Filter for Target Directors (same list as before)\n",
                    "target_directors = ['Hayao Miyazaki', 'Makoto Shinkai', 'Masaaki Yuasa', 'Hideaki Anno', \n",
                    "                    'Mamoru Hosoda', 'Naoko Yamada', 'Shinichirou Watanabe']\n",
                    "\n",
                    "# Get Director Works with Date\n",
                    "director_works = df_person_works[df_person_works['position'].str.contains('Director', case=False, na=False)]\n",
                    "director_full = director_works.merge(df_person_details[['person_id', 'normalized_name']], \n",
                    "                                     left_on='person_id', right_on='person_id')\n",
                    "director_target = director_full[director_full['normalized_name'].isin(target_directors)]\n",
                    "director_anime = director_target.merge(df[['anime_id', 'title', 'members', 'start_date']], on='anime_id')\n",
                    "\n",
                    "# Extract Year\n",
                    "director_anime['year'] = pd.to_datetime(director_anime['start_date'], errors='coerce').dt.year\n",
                    "director_anime = director_anime.dropna(subset=['year'])\n",
                    "director_anime['year'] = director_anime['year'].astype(int)\n",
                    "\n",
                    "# Calculate Cumulative Members per Director over Years\n",
                    "# We want: Year X -> Total Members for Director D up to Year X\n",
                    "min_year = director_anime['year'].min()\n",
                    "max_year = director_anime['year'].max()\n",
                    "all_years = list(range(min_year, max_year + 1))\n",
                    "\n",
                    "longevity_data = []\n",
                    "\n",
                    "for director in target_directors:\n",
                    "    d_df = director_anime[director_anime['normalized_name'] == director]\n",
                    "    current_members = 0\n",
                    "    \n",
                    "    # Iterate through all years to ensure continuity for animation\n",
                    "    for year in all_years:\n",
                    "        # Add members of anime released in this year\n",
                    "        new_members = d_df[d_df['year'] == year]['members'].sum()\n",
                    "        current_members += new_members\n",
                    "        \n",
                    "        # Only add data point if the director has started their career\n",
                    "        # Or just show flat line? Flat line is better to show 'dormant' periods.\n",
                    "        # Check if year >= director's first year\n",
                    "        if not d_df.empty and year >= d_df['year'].min():\n",
                    "            longevity_data.append({\n",
                    "                'Director': director,\n",
                    "                'Year': year,\n",
                    "                'Cumulative Members': current_members\n",
                    "            })\n",
                    "\n",
                    "df_longevity = pd.DataFrame(longevity_data)\n",
                    "\n",
                    "if not df_longevity.empty:\n",
                    "    fig = px.line(df_longevity, x=\"Year\", y=\"Cumulative Members\", color=\"Director\", \n",
                    "                  animation_frame=\"Year\", animation_group=\"Director\",\n",
                    "                  title=\"Longevity of Success: Cumulative Audience Growth over Career\",\n",
                    "                  range_x=[min_year, max_year],\n",
                    "                  range_y=[0, df_longevity['Cumulative Members'].max()*1.1])\n",
                    "    \n",
                    "    # Improve trace visibility\n",
                    "    fig.update_traces(mode='lines+markers')\n",
                    "    fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 100 # Speed up animation\n",
                    "    fig.show()\n",
                    "else:\n",
                    "    print(\"Not enough data for Longevity Analysis.\")"
                ]
            }
        ] # End new cells
        
        # Insert
        for cell in reversed(new_cells):
            cells.insert(insert_idx, cell)
            
        # Save
        with open(nb_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=4)
        print("Inserted Chapter 9.")

except Exception as e:
    print(f"Error: {e}")
