
import json

nb_path = r"c:\Users\user\OneDrive\Desktop\IUM\Ciravegna\unito-hci-data-analysis-25-26\solution\notebooks\03_midas_touch.ipynb"

# Dictionary of interpretations to append after specific section headers or code blocks
interpretations = {
    "## Chapter 2: The Hype Factor": {
        "text": "### 💡 Insight: Hype vs Reality\n- **High Correlation**: Generally, popular shows score well.\n- **Disappointment Sector**: Notice the points in the bottom-right (High Members, Low Score). These are the 'overhyped' failures.\n- **Hidden Gems**: Top-left remains sparse, as great shows usually attract at least some audience eventually."
    },
    "## Chapter 3:": {
        "text": "### 💡 Insight: The Seal of Quality\n- **Consistent Excellence**: Directors like Miyazaki and Shinkai show 'fat' distributions at the top (8-9 range), indicating they rarely miss.\n- **Variance**: Some prolific directors have stretched distributions, showing they take more risks or accept lower-tier projects."
    },
    "## Chapter 4: One Hit Wonders": {
        "text": "### 💡 Insight: Curse of the Masterpiece\n- **Prestige Drop**: Removing the masterpiece often drops a director's average significantly.\n- **One-Hit Wonders**: High 'Drop' values suggest the career relies heavily on a single success."
    },
    "## VORD": {
        "text": "### 💡 Insight: Value Over Replacement Director (VORD)\n- **Positive VORD**: The director adds value *above* the studio's average. A VORD of +1.0 means the director lifts a 7.0 studio anime to an 8.0.\n- **Negative VORD**: The director might be weighing down the studio's reputation."
    },
    "## Chapter 5: Composers": { 
        "text": "### 💡 Insight: The Sound of Success\n- **Score Uplift**: Shows with top composers often see a score boost, likely due to the 'epic factor' music brings to emotional scenes."
    },
    "## Studio DNA": {
        "text": "### 💡 Insight: Studio Identity\n- **Consistency**: Studios like KyoAni are bunched tightly at the top (Quality Control).\n- **Factory Model**: Studios with wide spread might prioritize quantity over consistent quality."
    },
    "## Risk Analysis": {
        "text": "### 💡 Insight: Risk Profile\n- **Originals**: High variance (High Risk, High Reward). Without a fanbase, they either flop or become cult classics.\n- **Adaptations**: Safer bets, usually hovering around the mean, but constrained by the source material."
    },
    "## Chapter 8: The Prejudice Threshold": {
        "text": "### 💡 Insight: The Trust Bonus\n- **Downward Slope**: A line sloping down from 'Airing' to 'Finished' suggests the initial hype wasn't sustained.\n- **Flat Line**: The studio delivers exactly what was promised."
    },
    "## Chapter 9: Longevity of Success": {
        "text": "### 💡 Insight: Legacy Building\n- **Steep Growth**: A steep curve indicates a period of rapid fanbase acquisition (a 'Golden Age').\n- **Continued Growth**: Classics that keep accumulating members decades later show true 'Timelessness'."
    }
}

try:
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    cells = nb['cells']
    new_cells_list = []
    
    # We iterate and rebuild the list to insert safely
    i = 0
    while i < len(cells):
        cell = cells[i]
        new_cells_list.append(cell)
        
        # Check if this cell is a header matching our keys
        # OR if it's the code cell *following* the header (usually better to put insight after the chart)
        # Strategy: Find header, identify it as "Pending Interpretation", then insert after the NEXT Code cell?
        # Simpler: Insert immediately after the code cell that produces the plot for that chapter.
        
        # Heuristic: If cell_type is code and we are inside a specific chapter...
        # But tracking "Inside Chapter" is hard.
        # Let's just insert after the Header cell for now? No, user wants interpretation of the *Result* (Graph).
        # So it should be after the graph.
        
        # Alternative: We modify the Notebook content to include these Mardown cells.
        # I will simpler match unique keywords in the Code source to identify the end of the analysis block.
        
        source_str = "".join(cell['source']) if 'source' in cell else ""
        
        # Logic to map code context to interpretation
        matched_key = None
        
        # Hype vs Reality (Scatter)
        if "px.scatter" in source_str and "Members vs Score" in source_str:
            matched_key = "## Chapter 2: The Hype Factor"
            
        # Seal of Quality (Ridgeline)
        elif "go.Violin" in source_str or "Ridgeline" in source_str:
            matched_key = "## Chapter 3:"
            
        # One Hit Wonder (Bar)
        elif "Prestige Drop" in source_str and "px.bar" in source_str:
            matched_key = "## Chapter 4: One Hit Wonders"
            
        # VORD (Bar)
        elif "VORD" in source_str and "px.bar" in source_str:
            matched_key = "## VORD"
            
        # Composers (Bar)
        elif "Score Uplift" in source_str and "px.bar" in source_str:
            matched_key = "## Chapter 5: Composers"
            
        # Studio DNA (Strip/Dot)
        elif "Studio DNA" in source_str:
            matched_key = "## Studio DNA"
            
        # Risk (Box)
        elif "Risk Profile" in source_str and "px.box" in source_str:
            matched_key = "## Risk Analysis"
            
        # Prejudice (Slope)
        elif "Prejudice Threshold" in source_str and "go.Scatter" in source_str:
            matched_key = "## Chapter 8: The Prejudice Threshold"
            
        # Longevity (Line Animation)
        elif "Longevity of Success" in source_str and "px.line" in source_str:
             matched_key = "## Chapter 9: Longevity of Success"

        if matched_key and matched_key in interpretations:
            # Check if interpretation already exists (avoid duplicates)
            # Look ahead at i+1
            already_exists = False
            if i + 1 < len(cells):
                next_source = "".join(cells[i+1]['source'])
                if "💡 Insight" in next_source:
                    already_exists = True
            
            if not already_exists:
                insight_cell = {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [interpretations[matched_key]["text"]]
                }
                new_cells_list.append(insight_cell)
                print(f"Added insight for {matched_key}")
        
        i += 1
        
    nb['cells'] = new_cells_list
    
    with open(nb_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=4)
    print("Notebook updated with interpretations.")

except Exception as e:
    print(f"Error: {e}")
