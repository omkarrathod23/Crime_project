import os
import time
import sys
import subprocess
from pyngrok import ngrok
from services.ngrok_service import ngrok_service

def start_mobile_unification():
    print("\n" + "═" * 60)
    print(" 🛡️  SENTINEL UNIFIED MOBILE BRIDGE 3.0 ".center(60, "═"))
    print("═" * 60 + "\n")

    auth_token = os.getenv('NGROK_AUTH_TOKEN')
    if not auth_token:
        print("❌ ERROR: NGROK_AUTH_TOKEN missing!")
        print("Run: $env:NGROK_AUTH_TOKEN='your_token' then run this script.")
        return

    # 1. Cleanup existing tunnels
    print("🧹 Resetting Uplinks...")
    try:
        ngrok.set_auth_token(auth_token)
        for t in ngrok.get_tunnels():
            ngrok.disconnect(t.public_url)
    except:
        pass

    # 2. Start UNIFIED Tunnel (Port 5000)
    # This tunnel serves BOTH API and UI (via Flask Proxy)
    print("📡 Launching Unified Uplink (Port 5000)...")
    public_url = ngrok_service.start_tunnel(port=5000, name="api")
    
    if not public_url:
        print("❌ FAILED TO ESTABLISH UPLINK.")
        return

    print(f"\n✅ UNIFIED BRIDGE ESTABLISHED!")
    print(f"🔗 PUBLIC URL: {public_url}")

    # 3. Booting Backend API in Mobile Mode
    print("\n🚀 AWAKENING BACKEND COMMAND CENTER...")
    os.environ['SENTINEL_MOBILE_MODE'] = 'true'
    
    print("\n" + "█" * 40)
    print("█ SCAN TO DEPLOY CITIZEN APP ".ljust(39) + "█")
    ngrok_service.print_terminal_qr(public_url)
    print("█" * 40)
    
    # Ensure current directory is in path
    sys.path.append(os.getcwd())
    
    from app import app as flask_app
    from extensions import socketio
    
    try:
        print("\n📡 UPLINK ONLINE. MONITORING SIGNALS...")
        socketio.run(flask_app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n🛑 SHUTTING DOWN PROTOCOL...")
        ngrok.kill()

if __name__ == "__main__":
    start_mobile_unification()
