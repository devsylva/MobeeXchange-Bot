import hmac
import hashlib
import base64
import time
import requests
import json
from django.conf import settings
from asgiref.sync import sync_to_async
from urllib.parse import urlparse
import logging
from .utils import get_user_balance

# Configure logging
logger = logging.getLogger(__name__)

def generate_mobee_auth_headers(method, url, body=None):
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
    secret_bytes = settings.MOBEE_API_SECRET.encode('utf-8')
    str_to_sign_bytes = str_to_sign.encode('utf-8')
    hmac_obj = hmac.new(secret_bytes, str_to_sign_bytes, hashlib.sha256)
    signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')
    
    # Prepare headers
    headers = {
        "X-API-Key": settings.MOBEE_API_KEY,
        "X-Request-Signature": signature,
        "X-Request-Timestamp": timestamp
    }
    
    return headers


def createFiatDeposit(amount, bank_code):
    url = "https://open-api.mobee.io/v1/wallets/fiat-deposits"
    method = "POST"

    body = {
        "amount": amount,
        "bank_code": bank_code
    }
    print(f"Request body: {body}")
    body_json = json.dumps(body, separators=(',', ':'))
    print(f"Request body JSON: {body_json}")
    # Generate headers
    headers = generate_mobee_auth_headers(method, url, body_json)
    headers["Content-Type"] = "application/json"
    headers["accept"] = "application/json"
    print(f"Request headers: {headers}")
    
    try:
        # Make the POST request
        response = requests.post(url, headers=headers, data=body_json)
        
        # Check if request was successful
        response.raise_for_status()
        
        # Return JSON response
        logger.info(f"Response from Mobee: {response.json()}")
        return response.json()
    
    except requests.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except requests.RequestException as e:
        print(f"Request failed: {str(e)}")
        raise


def createCryptoWithdrawal(currency, amount, address, network_id):
    url = "https://open-api.mobee.io/v1/wallets/crypto-withdrawals"
    method = "POST"

    # Construct the request body
    body = {
        "currency": currency,
        "amount": amount,
        "address": address,
        "network_id": network_id
    }
    
    # Serialize the body to JSON
    body_json = json.dumps(body, separators=(',', ':'))

    # Generate headers
    headers = generate_mobee_auth_headers(method, url, body_json)
    headers["Content-Type"] = "application/json"
    headers["accept"] = "application/json"
    
    try:
        # Make the POST request
        response = requests.post(url, headers=headers, data=body_json)
        
        # Check if request was successful
        response.raise_for_status()
        
        # Log and return JSON response
        logger.info(f"Response from Mobee: {response.json()}")
        return response.json()
    
    except requests.HTTPError as e:
        logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except requests.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        raise
