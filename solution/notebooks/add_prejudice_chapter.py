
import json
import os

nb_path = r"c:\Users\user\OneDrive\Desktop\IUM\Ciravegna\unito-hci-data-analysis-25-26\solution\notebooks\03_midas_touch.ipynb"

try:
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    cells = nb['cells']
    insert_idx = -1

    # Find insertion point
    for i, cell in enumerate(cells):
        if cell['cell_type'] == 'markdown':
            source = "".join(cell['source'])
            if "## Conclusions: The Equation of Success" in source:
                insert_idx = i
                break

    if insert_idx != -1:
        print(f"Found insertion point at index {insert_idx}")
        
        # New Cells
        new_cells = [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Chapter 8: The Prejudice Threshold (Pre-Release vs Final Score) 🚀\n",
                    "\n",
                    "Is the public more lenient with \"Big Names\" at the beginning?\n",
                    "We compare the average score of **currently airing** anime (early impressions) vs **finished** anime for top studios/directors.\n",
                    "Hypothesis: Big Studios start with a \"Trust Bonus\" (e.g. +0.5 score) which might normalize later."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Analysis of Prejudice Threshold\n",
                    "# Filter for Big Studios\n",
                    "target_studios_extended = ['Kyoto Animation', 'Madhouse', 'MAPPA', 'Bones', 'Sunrise', \n",
                    "                           'A-1 Pictures', 'J.C.Staff', 'Studio Ghibli', 'ufotable', \n",
                    "                           'Production I.G', 'CloverWorks', 'Wit Studio']\n",
                    "\n",
                    "prejudice_data = []\n",
                    "\n",
                    "print(\"Analyzing Prejudice Threshold for Studios:\")\n",
                    "for studio in target_studios_extended:\n",
                    "    # Find works\n",
                    "    s_works = df[df['studios'].astype(str).str.contains(studio, na=False)]\n",
                    "    \n",
                    "    # Airing (Early Score) - Proxy: Status='Currently Airing'\n",
                    "    airing = s_works[s_works['status'] == 'Currently Airing']\n",
                    "    finished = s_works[s_works['status'] == 'Finished Airing']\n",
                    "    \n",
                    "    if len(airing) > 0 and len(finished) > 0:\n",
                    "        avg_airing = airing['score'].mean()\n",
                    "        avg_finished = finished['score'].mean()\n",
                    "        print(f\"{studio}: Airing N={len(airing)} ({avg_airing:.2f}) vs Finished N={len(finished)} ({avg_finished:.2f})\")\n",
                    "        \n",
                    "        prejudice_data.append({\n",
                    "            'Studio': studio,\n",
                    "            'Status': 'Airing (Early)',\n",
                    "            'Average Score': avg_airing\n",
                    "        })\n",
                    "        prejudice_data.append({\n",
                    "            'Studio': studio,\n",
                    "            'Status': 'Finished (Final)',\n",
                    "            'Average Score': avg_finished\n",
                    "        })\n",
                    "    else:\n",
                    "        pass # Skip if no comparison possible\n",
                    "\n",
                    "df_prejudice = pd.DataFrame(prejudice_data)\n",
                    "\n",
                    "if not df_prejudice.empty:\n",
                    "    fig = px.bar(df_prejudice, x='Studio', y='Average Score', color='Status', barmode='group',\n",
                    "                 title='The Prejudice Threshold: Early Impressions (Airing) vs Reality (Finished)',\n",
                    "                 color_discrete_map={'Airing (Early)': '#EF553B', 'Finished (Final)': '#636EFA'})\n",
                    "    \n",
                    "    fig.update_layout(yaxis_title='Average Score', xaxis_title='Studio', yaxis_range=[5, 10])\n",
                    "    fig.show()\n",
                    "else:\n",
                    "    print(\"Not enough airing data for selected studios to build the chart.\")"
                ]
            }
        ]
        
        # Insert
        for cell in reversed(new_cells):
            cells.insert(insert_idx, cell)
        
        # Save
        with open(nb_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=4) # indent 4 is standard for readability
        
        print("Successfully inserted Chapter 8.")
    else:
        print("Could not find insertion point 'Equation of Success'.")
except Exception as e:
    print(f"Error: {e}")
