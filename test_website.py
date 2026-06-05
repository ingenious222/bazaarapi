import urllib.request, sys, time, json
sys.stdout.reconfigure(encoding='utf-8')
time.sleep(2)

BASE = 'http://localhost:5001'

print('=' * 50)
print('  BazaarAPI Website Test')
print('=' * 50)

# Test 1: Root serves HTML
r = urllib.request.urlopen(BASE + '/', timeout=5)
content = r.read().decode('utf-8')[:100]
is_html = '<!DOCTYPE html>' in content or '<html' in content
print('[1] Root (HTML)  :', 'REAL WEBSITE SERVED!' if is_html else 'JSON (not HTML)')

# Test 2: Products API
r = urllib.request.urlopen(BASE + '/api/v1/products', timeout=5)
data = json.loads(r.read())
total = data.get('total', 0)
first = data.get('products', [{}])[0].get('name', '?')
print('[2] Products API :', total, 'products | first:', first)

# Test 3: Swagger
r = urllib.request.urlopen(BASE + '/swagger.json', timeout=5)
data = json.loads(r.read())
title = data.get('info', {}).get('title', '?')
print('[3] Swagger      :', title)

# Test 4: Docs
r = urllib.request.urlopen(BASE + '/docs', timeout=5)
docs = r.read().decode()[:50]
print('[4] Docs page    :', docs.strip())

print()
print('  Open in browser: http://localhost:5001')
print('  You will see the Indian shopping website!')
print('=' * 50)
