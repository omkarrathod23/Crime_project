import re

def validate_aadhaar(number):
    """
    Validates Aadhaar number (12-digit numeric) and returns masked version.
    """
    if not number:
        return None, "Aadhaar number is required."
    
    # Remove any hyphens or spaces
    clean_number = re.sub(r'[\s-]', '', str(number))
    
    if not re.match(r'^\d{12}$', clean_number):
        return None, "Invalid Aadhaar format. Must be 12 digits."
    
    # Mask: XXXX-XXXX-1234
    masked = f"XXXX-XXXX-{clean_number[-4:]}"
    return masked, None

def validate_pan(number):
    """
    Validates PAN number (format: ABCDE1234F) and returns masked version.
    """
    if not number:
        return None, "PAN number is required."
    
    clean_number = str(number).strip().upper()
    
    if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', clean_number):
        return None, "Invalid PAN format. Expected format: ABCDE1234F"
    
    # Mask: XXXXX1234X
    masked = f"{clean_number[:2]}XXX{clean_number[5:9]}{clean_number[-1]}"
    return masked, None

def process_face_verification(image_base64):
    """
    Simulates face verification. In production, this would use OpenCV or a face API.
    """
    if not image_base64:
        return False, "Face image is required."
    
    # Basic check for base64 string
    if image_base64.startswith('data:image'):
        return True, "Face verification successful (simulated)."
    
    return False, "Invalid image data."
