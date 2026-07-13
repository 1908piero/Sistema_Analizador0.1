import os, sys, threading, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))

from pyngrok import ngrok
from app import app

port = 5000
tunnel = ngrok.connect(port, bind_tls=True)
public_url = tunnel.public_url
print(f"\n{'='*55}")
print(f"  URL PUBLICA (comparte este enlace):")
print(f"  \033[92m{public_url}\033[0m")
print(f"{'='*55}")
print(f"  Presiona Ctrl+C para detener")
print(f"{'='*55}\n")

app.run(debug=False, host='0.0.0.0', port=port)
