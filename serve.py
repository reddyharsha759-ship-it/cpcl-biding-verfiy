"""
CPCL GeM Compliance Copilot - Production Server Runner
Hosts the application on 0.0.0.0:8000 accessible locally and across the network/LAN.
"""

import socket
import sys
import uvicorn


def get_network_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    local_ip = get_network_ip()
    port = 8000

    print("=" * 72)
    print("  CHENNAI PETROLEUM CORPORATION LIMITED (CPCL)")
    print("  GeM Compliance Copilot & Scrutiny Portal - Host Server")
    print("=" * 72)
    print(f"  * Local Host Access:     http://127.0.0.1:{port}/dashboard")
    print(f"  * Local Login Portal:    http://127.0.0.1:{port}/login")
    print(f"  * Network/LAN Access:    http://{local_ip}:{port}/dashboard")
    print(f"  * API Docs (Swagger):    http://127.0.0.1:{port}/docs")
    print("=" * 72)
    print("  Server is live and listening on 0.0.0.0:8000 ... (Press Ctrl+C to stop)")
    print("=" * 72)

    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info", access_log=True)
