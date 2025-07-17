from waitress import serve
from onlinexam.wsgi import application
import socket

# Get local IP address
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

if __name__ == '__main__':
    print(f"\nServer running on:\n")
    print(f"Local: http://localhost:8000")
    print(f"LAN: http://{local_ip}:8000\n")
    print(f"LAN: http://192.168.0.2:8000")
    
    serve(
        application,
        host='0.0.0.0', 
        port=8000,
        threads=16,  
        url_scheme='http',
        # channel_timeout=120 
    )