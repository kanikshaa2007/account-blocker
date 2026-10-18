import urllib.request, json

q = urllib.request.urlopen('http://localhost:5001/api/monitor/queue', timeout=8).read().decode()
d = json.loads(q)
data = d.get('data', d)
print('SIGHTINGS:', len(data.get('sightings', [])))
for s in data.get('sightings', [])[:15]:
    platform = s.get('platform', '?')
    author = str(s.get('author', ''))[:28]
    tier = s.get('tier', '?')
    score = s.get('score', 0)
    text = str(s.get('text', ''))[:60]
    print(f'{platform:12} | {author:28} | {tier:8} | score={score} | {text}')
