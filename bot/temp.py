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
    print(f"Request headers: {headers}")
    
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

def create_crypto_withdrawal(currency, amount, address, network_id, address_tag=None):
    """
    Make a POST request to Mobee API to create a crypto withdrawal.
    
    Args:
        currency (str): Cryptocurrency code (e.g., BTC, ETH)
        amount (float): Amount to withdraw
        address (str): Withdrawal address
        network_id (int): Network ID for the withdrawal
        address_tag (str, optional): Additional address tag for the withdrawal
    
    Returns:
        dict: JSON response containing withdrawal details
    """
    url = "https://open-api.mobee.io/v1/wallets/crypto-withdrawals"
    method = "POST"
    
    # Prepare request body
    body = {
        "currency": str(currency),
        "amount": float(amount),  # Ensure amount is a float
        "address": str(address),
        "network_id": int(network_id)
    }
    
    # Include address_tag if provided
    if address_tag:
        body["address_tag"] = str(address_tag)
    
    # Serialize the body to JSON
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

def get_balances(currency=None):
    """
    Fetch wallet balances from Mobee API.

    Args:
        currency (str, optional): Symbol of a currency (e.g., BTC). Defaults to None.

    Returns:
        dict: JSON response containing wallet balances.
    """
    url = "https://open-api.mobee.io/v1/wallets/balances"
    method = "GET"
    
    # Prepare query parameters
    params = {}
    if currency:
        params["currency"] = str(currency)
    
    # Generate headers
    headers = sign_request(method, url, params)
    
    try:
        # Make the GET request
        response = requests.get(url, headers=headers, params=params)
        
        # Log the response details
        print("Response Status Code:", response.status_code)
        print("Response Body:", response.text)
        
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

def get_all_addresses():
    url = "https://open-api.mobee.io/v1/wallets/addresses"
    method = "GET"

    headers = sign_request(method, url)

    try:
        response = requests.get(url, headers=headers)

        response.raise_for_status()

        return response.json()
    except requests.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except requests.RequestException as e:
        print(f"Request failed: {str(e)}")
        raise

# Execute the request
if __name__ == "__main__":
    # try:
    #     # Example parameters
    #     amount = 100000  # 100,000 IDR
    #     bank_code = "BNI"  # Example bank code
    #     fiat_deposit = create_fiat_deposit(amount, bank_code)
    #     print("Fiat Deposit Response:")
    #     print(json.dumps(fiat_deposit, indent=2))
    # except Exception as e:
    #     print(f"Error: {str(e)}")

    # Test the createcyptowithd_rawal function
    # Example parameters
    currency = "USDT"  # Example cryptocurrency
    withdrawal_amount = 4.5  # Amount to withdraw
    address = "0x498b7c3b408ea03dc5cc34dc967114b6f6e3669a"  # Replace with your address
    network_id = 12  # Example network ID
    crypto_withdrawal = create_crypto_withdrawal(currency, withdrawal_amount, address, network_id)
    print("Crypto Withdrawal Response:")
    print(json.dumps(crypto_withdrawal, indent=2))
    
    # Test the get_balances function
    # try:
    #     # Fetch all balances
    #     all_balances = get_balances()
    #     print("All Balances:")
    #     print(json.dumps(all_balances, indent=2))
        
    #     # Fetch balance for a specific currency
    #     btc_balance = get_balances(currency="USDT")
    #     print("BTC Balance:")
    #     print(json.dumps(btc_balance, indent=2))
    # except Exception as e:
    #     print(f"Error: {str(e)}")


    # Test the get_all_addresses fucntion
    # try:
    #     all_addresses = get_all_addresses()
    #     print("All Address")
    #     print(json.dumps(all_addresses, indent=2))
    # except Exception as e:
    #     print(f"Error: {str(e)}")