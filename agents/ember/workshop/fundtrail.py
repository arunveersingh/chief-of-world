import json
n=s=k=0
for l in open('logs/events.jsonl'):
    e=json.loads(l)
    if e['type']=='deposit':
        n+=1
        if 'agent' in e and 'amount' in e: k+=1; s+=e['amount']
print(f"deposit events {n}, with agent+amount {k}, credits {s}")
st=json.load(open('world/state.json'))
f=[i for i in st['institutions'] if i['id']=='voluntary_project_fund'][0]
print("contributors total", sum(f['contributors'].values()))
print("LAW-0026 in spending_rules:", 'LAW-0026' in f['spending_rules'])
