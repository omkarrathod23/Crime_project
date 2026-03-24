import os
import time
import sys
import subprocess
from pyngrok import ngrok
from services.ngrok_service import ngrok_service

def start_mobile_ecosystem():
    print("\n" + "═" * 60)
    print(" 🛡️  SENTINEL MOBILE ECOSYSTEM 2.0 INITIALIZING ".center(60, "═"))
    print("═" * 60 + "\n")

    auth_token = os.getenv('NGROK_AUTH_TOKEN')
    if not auth_token:
        print("❌ ERROR: NGROK_AUTH_TOKEN missing!")
        print("Run: $env:NGROK_AUTH_TOKEN='your_token' then run this script.")
        return

    # 0. Cleanup existing tunnels
    print("🧹 Clearing legacy tunnels...")
    try:
        ngrok.set_auth_token(auth_token)
        for t in ngrok.get_tunnels():
            ngrok.disconnect(t.public_url)
    except:
        pass

    # 1. Start API Tunnel (Port 5000)
    print("📡 Launching API Uplink (Port 5000)...")
    api_url = ngrok_service.start_tunnel(port=5000, name="api")
    
    # 2. Start Frontend Tunnel (Port 5173)
    print("🌐 Launching UI Portal (Port 5173)...")
    ui_url = ngrok_service.start_tunnel(port=5173, name="ui")

    print("\n✅ TUNNELS ESTABLISHED!")
    print(f"🔗 PUBLIC API: {api_url}")
    print(f"🔗 PUBLIC UI:  {ui_url}")

    # 3. Booting Vite Mobile Portal
    print("\n🚀 AWAKENING MOBILE PORTAL (Vite)...")
    vite_env = os.environ.copy()
    vite_env["VITE_API_URL"] = api_url
    
    # Start Vite in background
    vite_proc = subprocess.Popen(
        ["npm", "run", "dev"], 
        cwd=os.path.abspath(os.path.join(os.getcwd(), "..", "citizen-mobile")),
        env=vite_env,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print("✅ MOBILE UI ENGINE RUNNING.")

    # 4. Booting Backend API
    print("\n🚀 SYNCHRONIZING BACKEND COMMAND CENTER...")
    os.environ['SENTINEL_MOBILE_MODE'] = 'true'
    os.environ['VITE_API_URL'] = api_url # For internal consistency if needed
    
    print("\n" + "█" * 40)
    print("█ SCAN TO DEPLOY ON MOBILE DEVICE ".ljust(39) + "█")
    ngrok_service.print_terminal_qr(ui_url)
    print("█" * 40)
    
    # Add parent dir to path if needed for service imports
    sys.path.append(os.getcwd())
    
    from app import app as flask_app
    from extensions import socketio
    
    try:
        print("\n📡 API LIVE. MONITORING UPLINKS...")
        socketio.run(flask_app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n🛑 SHUTTING DOWN PROTOCOL...")
        vite_proc.terminate()
        ngrok.kill()

if __name__ == "__main__":
    start_mobile_ecosystem()
