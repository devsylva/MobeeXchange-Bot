import requests
import hmac
import hashlib
import base64
import time
from urllib.parse import urlparse
import json

# API credentials
API_KEY = "d22b3dfd-a40b-4d91-8f6a-f9bb7ea2aee6"
API_SECRET = "71a17cca-7855-4561-b69d-4ff8a81bf074"

def sign_request(method, url, body=None):
    """
    Generate authentication headers for Mobee API request.
    
    Args:
        method (str): HTTP method (GET, POST, PUT)
        url (str): Full URL of the API endpoint
        body (str, optional): JSON string body for POST/PUT requests
    
    Returns:
        dict: Headers with X-API-Key, X-Request-Signature, and X-Request-Timestamp
    """
    # Generate timestamp
    timestamp = str(int(time.time()))
    
    # Get URL path
    path = urlparse(url).path
    
    # Construct string to sign
    str_to_sign = f"{method}\n{path}\n{timestamp}"
    
    # Append body for POST or PUT requests
    if method in ["POST", "PUT"] and body:
        str_to_sign += f"\n{body}"
    
    # Generate HMAC-SHA256 signature
    secret_bytes = API_SECRET.encode('utf-8')
    str_to_sign_bytes = str_to_sign.encode('utf-8')
    hmac_obj = hmac.new(secret_bytes, str_to_sign_bytes, hashlib.sha256)
    signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')
    
    # Prepare headers
    headers = {
        "X-API-Key": API_KEY,
        "X-Request-Signature": signature,
        "X-Request-Timestamp": timestamp
    }
    
    return headers

def create_fiat_deposit(amount, bank_code):
    """
    Make a POST request to Mobee API to create a fiat deposit with fixed amount.
    
    Args:
        amount (int): IDR amount (minimum 10000)
        bank_code (str): Bank code (BNI, BRI, MANDIRI, PERMATA, CIMB)
    
    Returns:
        dict: JSON response containing fiat deposit details
    """
    url = "https://open-api.mobee.io/v1/wallets/fiat-deposits"
    method = "POST"
    
    # Validate inputs
    if amount < 10000:
        raise ValueError("Amount must be at least 10000 IDR")
    valid_banks = ["BNI", "BRI", "MANDIRI", "PERMATA", "CIMB"]
    if bank_code not in valid_banks:
        raise ValueError(f"Bank code must be one of: {', '.join(valid_banks)}")
    
    # Prepare request body
    body = {
        "amount": amount,
        "bank_code": bank_code
    }
    body_json = json.dumps(body, separators=(',', ':'))
    
    # Generate headers
    headers = sign_request(method, url, body_json)
    headers["Content-Type"] = "application/json"
    
    try:
        # Make the POST request
        response = requests.post(url, headers=headers, data=body_json)
        
        # Check if request was successful
        response.raise_for_status()
        
        # Return JSON response
        return response.json()
    
    except requests.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except requests.RequestException as e:
        print(f"Request failed: {str(e)}")
        raise

# Execute the request
if __name__ == "__main__":
    try:
        # Example parameters
        amount = 100000  # 100,000 IDR
        bank_code = "BNI"  # Example bank code
        fiat_deposit = create_fiat_deposit(amount, bank_code)
        print("Fiat Deposit Response:")
        print(json.dumps(fiat_deposit, indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")



# import asyncio
# from bot.mobee_utils import createFiatDeposit

# async def test():
#     response = await createFiatDeposit(100000, "BNI")
#     print(response)

# asyncio.run(test())