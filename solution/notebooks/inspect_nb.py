
import json
nb = json.load(open('03_midas_touch.ipynb', encoding='utf-8'))
for i in range(len(nb['cells'])):
    c = nb['cells'][i]
    src = "".join(c['source'])
    first_line = c['source'][0].strip() if c['source'] else ""
    print(f"{i}: {c['cell_type']} | {first_line[:50]}")
