# %%
from qiandao_template import downloadTPL

tpl = downloadTPL('https://qiandao.today')
# %%
import json
with open('database.json', 'r', encoding='utf8') as f:
    tpl2 = json.load(f)
# %%
tpl_names = [i['name'] for i in tpl]
for j in tpl2:
    if j['name'] not in tpl_names:
        tpl.append((j))
        print(j['name'])
# %%
with open('database.json', 'w', encoding='utf8') as f:
    json.dump(tpl, f, indent=2)
# %%
