import os
import qrcode
import io
import base64
from pyngrok import ngrok, conf
import logging

class NgrokService:
    def __init__(self):
        self.public_url = None
        self.qr_base64 = None
        self.qr_path = "static/qr.png"
        
    def start_tunnel(self, port=5000, auth_token=None):
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
                
            # Connect to ngrok
            # pyngrok handles downloading the binary automatically
            self.public_url = ngrok.connect(port).public_url
            logging.info(f"[*] Ngrok Tunnel Active: {self.public_url}")
            
            # Generate QR code for the web
            self.qr_base64 = self.generate_qr_base64(self.public_url)
            
            # Save QR to static folder for direct access
            self.save_qr_image(self.public_url)
            
            return self.public_url
        except Exception as e:
            logging.error(f"[!] Ngrok Error: {e}")
            if "authentication failed" in str(e).lower():
                print("\n[CRITICAL] NGROK AUTHENTICATION FAILED!")
                print("Get your token from: https://dashboard.ngrok.com/get-started/your-authtoken")
                print("Then run: $env:NGROK_AUTH_TOKEN='your_token'; python app.py\n")
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

    def save_qr_image(self, url):
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
            img.save(self.qr_path)
            logging.info(f"[*] QR Code saved to {self.qr_path}")
        except Exception as e:
            logging.error(f"[!] QR Save Error: {e}")

    def print_terminal_qr(self, url=None):
        """
        Prints an ASCII QR code to the terminal.
        """
        target_url = url or self.public_url
        if not target_url:
            return
            
        print("\n" + "█" * 50)
        print("█ SHIPPING SEAMLESS MOBILE ACCESS ".ljust(49) + "█")
        print("█" + " " * 48 + "█")
        
        try:
            import qrcode_terminal
            qrcode_terminal.draw(target_url)
        except ImportError:
            # Fallback to standard qrcode ascii
            qr = qrcode.QRCode()
            qr.add_data(target_url)
            qr.print_ascii()
        
        print(f"\n[SCAN TO OPEN] -> {target_url}")
        print("█" * 50 + "\n")

# Global instance
ngrok_service = NgrokService()
