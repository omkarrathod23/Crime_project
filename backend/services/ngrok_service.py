import os
import qrcode
import io
import base64
from pyngrok import ngrok, conf
import logging

class NgrokService:
    def __init__(self):
        self.public_url = None
        self.frontend_url = None
        self.qr_base64 = None
        self.qr_frontend_base64 = None
        self.qr_path = "static/qr.png"
        self.qr_frontend_path = "static/qr_frontend.png"
        
    def start_tunnel(self, port=5000, auth_token=None, name="api"):
        """
        Starts an Ngrok tunnel on the specified port.
        """
        try:
            # Handle Auth Token
            token = auth_token or os.getenv('NGROK_AUTH_TOKEN')
            if token:
                ngrok.set_auth_token(token)
            else:
                logging.warning("[!] NGROK_AUTH_TOKEN not found. Tunnel might fail or be restricted.")
                
            # Connect to ngrok with explicit name and address to avoid collisions
            addr = f"127.0.0.1:{port}"
            tunnel = ngrok.connect(addr, name=name)
            url = tunnel.public_url
            
            if name == "api":
                self.public_url = url
                self.qr_base64 = self.generate_qr_base64(url)
                self.save_qr_image(url, self.qr_path)
            else:
                self.frontend_url = url
                self.qr_frontend_base64 = self.generate_qr_base64(url)
                self.save_qr_image(url, self.qr_frontend_path)
                
            logging.info(f"[*] Ngrok Tunnel ({name}) Active: {url}")
            return url
        except Exception as e:
            logging.error(f"[!] Ngrok Error ({name}): {e}")
            if "authentication failed" in str(e).lower():
                print(f"\n[CRITICAL] NGROK AUTHENTICATION FAILED FOR {name}!")
                print("Get your token from: https://dashboard.ngrok.com/get-started/your-authtoken")
            return None

    def generate_qr_base64(self, url):
        """
        Generates a QR code image and returns it as a Base64 string.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def save_qr_image(self, url, path):
        """
        Saves a QR code image to the static directory.
        """
        try:
            # Ensure static dir exists
            os.makedirs("static", exist_ok=True)
            
            qr = qrcode.QRCode(box_size=10, border=4)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(path)
            logging.info(f"[*] QR Code saved to {path}")
        except Exception as e:
            logging.error(f"[!] QR Save Error: {e}")

    def print_terminal_qr(self, url=None):
        """
        Prints an ASCII QR code to the terminal.
        """
        target_url = url or self.public_url
        if not target_url:
            return
            
        print("\n" + "█" * 30)
        print("█ MOBILE ACCESS BRIDGE ".ljust(29) + "█")
        
        try:
            # Try to use a smaller box size with the standard library instead of the terminal lib
            # which can sometimes be too large
            qr = qrcode.QRCode(box_size=1, border=2)
            qr.add_data(target_url)
            qr.print_ascii()
        except Exception:
            print(f"\n[URL] -> {target_url}\n")
        
        print("█" * 30 + "\n")
        print("💡 TIP: Visit http://127.0.0.1:5000/qr on your laptop for a high-res scanner!")

# Global instance
ngrok_service = NgrokService()
