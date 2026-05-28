import urllib.request
import urllib.error

req = urllib.request.Request(
    'https://multi-agent-system-promptpal.onrender.com/ask',
    method='OPTIONS',
    headers={
        'Origin': 'https://prompt-pal-six.vercel.app',
        'Access-Control-Request-Method': 'POST'
    }
)
try:
    response = urllib.request.urlopen(req)
    print("Status:", response.status)
    print("Headers:", response.headers)
except urllib.error.HTTPError as e:
    print("Status:", e.code)
    print("Headers:", e.headers)
    print("Body:", e.read().decode())
