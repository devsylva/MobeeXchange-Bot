import hmac
import hashlib
import base64
import time
import requests
import json
from django.conf import settings
from asgiref.sync import sync_to_async
import logging

# Configure logging
logger = logging.getLogger(__name__)

def generate_mobee_auth_headers(method, path, body=None):
    """
    Generate authentication headers for Mobee API requests.
    
    Args:
        method (str): HTTP method (GET, POST, PUT)
        path (str): API endpoint path (e.g., '/v1/wallets/fiat-deposits')
        body (dict, optional): Request body for POST/PUT requests
    
    Returns:
        dict: Headers containing X-API-Key, X-Request-Signature, X-Request-Timestamp
    
    Raises:
        KeyError: If MOBEE_API_KEY or MOBEE_API_SECRET is not set in settings
    """
    try:
        api_key = settings.MOBEE_API_KEY
        api_secret = settings.MOBEE_API_SECRET
    except AttributeError as e:
        raise KeyError("MOBEE_API_KEY or MOBEE_API_SECRET not found in settings") from e

    timestamp = str(int(time.time()))
    str_to_sign = f"{method}\n{path}\n{timestamp}"
    
    if method in ["POST", "PUT"] and body is not None:
        body_str = json.dumps(body, separators=(',', ':'))
        str_to_sign += f"\n{body_str}"
    
    api_secret_bytes = api_secret.encode('utf-8')
    str_to_sign_bytes = str_to_sign.encode('utf-8')
    hmac_obj = hmac.new(api_secret_bytes, str_to_sign_bytes, hashlib.sha256)
    signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')
    
    return {
        "X-API-Key": api_key,
        "X-Request-Signature": signature,
        "X-Request-Timestamp": timestamp
    }

@sync_to_async
def getDepositAddress(amount, bank_code):
    """
    Make a POST request to Mobee's fiat deposit endpoint to initiate a deposit.
    
    Args:
        amount (float): The deposit amount
        bank_code (str): The bank code for the deposit
    
    Returns:
        requests.Response: The API response
    
    Raises:
        requests.RequestException: If the API request fails
    """
    url = "https://open-api.mobee.io/v1/wallets/fiat-deposits"
    path = "/v1/wallets/fiat-deposits"
    body = {
        "amount": amount,
        "bank_code": bank_code
    }
    
    try:
        auth_headers = generate_mobee_auth_headers("POST", path, body)
        headers = {
            **auth_headers,
            "accept": "application/json",
            "content-type": "application/json"
        }
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()  # Raise exception for 4xx/5xx status codes
        return response
    except requests.RequestException as e:
        logger.error(f"Error making fiat deposit request: {str(e)}")
        raise