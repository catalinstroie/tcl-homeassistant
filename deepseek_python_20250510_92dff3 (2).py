import base64
import hashlib
import json
import os
import requests
import time
import datetime
from requests_aws4auth import AWS4Auth

# Configuration
CLIENT_ID = "54148614"
ACCOUNT_LOGIN_URL = "https://pa.account.tcl.com/account/login?clientId={}"
USER_AGENT = "Android"
CONTENT_TYPE = "application/json; charset=UTF-8"
GET_THINGS_URL = "https://prod-eu.aws.tcljd.com/v3/user/get_things"
TH_PLATFORM = "android"
TH_VERSION = "4.8.1"
TH_APPBUILD = "830"
REFRESH_TOKENS_URL = "https://prod-eu.aws.tcljd.com/v3/auth/refresh_tokens"
APP_ID = "wx6e1af3fa84fbe523"
AWS_COGNITO_URL = "https://cognito-identity.eu-central-1.amazonaws.com/"
AWS_IOT_REGION = "eu-central-1"
AWS_IOT_ENDPOINT = "a2qjkbbsk6qn2u-ats.iot.eu-central-1.amazonaws.com"

# From JWT analysis
HARDCODED_IDENTITY_ID = "eu-central-1:61e8f839-2d72-c035-a2bf-7ef50a856ddd"
IDENTITY_POOL_ID = "eu-central-1:83840aed-13f2-4c1d-8eaf-9df7f2daaee3"

def print_request(method, url, headers, data):
    print(f"\n=== {method} Request ===")
    print(f"URL: {url}")
    print("Headers:")
    for k, v in headers.items():
        print(f"  {k}: {v}")
    print("Body:")
    print(json.dumps(data, indent=2))

def print_response(response):
    print(f"\n=== Response {response.status_code} ===")
    print("Headers:")
    for k, v in response.headers.items():
        print(f"  {k}: {v}")
    try:
        print("Body:")
        print(json.dumps(response.json(), indent=2))
    except json.JSONDecodeError:
        print("Raw content:")
        print(response.text[:500])

def calculate_md5_hash_bytes(input_string):
    md5_hash = hashlib.md5()
    md5_hash.update(input_string.encode('utf-8'))
    return md5_hash.hexdigest()

def do_account_auth(username, password):
    password_hash = hashlib.md5(password.encode()).hexdigest()
    url = ACCOUNT_LOGIN_URL.format(CLIENT_ID)
    headers = {
        "th_platform": TH_PLATFORM,
        "th_version": TH_VERSION,
        "th_appbulid": TH_APPBUILD,
        "user-agent": USER_AGENT,
        "content-type": CONTENT_TYPE,
    }
    data = {
        "equipment": 2,
        "password": password_hash,
        "osType": 1,
        "username": username,
        "clientVersion": "4.8.1",
        "osVersion": "6.0",
        "deviceModel": "AndroidAndroid SDK built for x86",
        "captchaRule": 2,
        "channel": "app",
    }
    
    print_request("Account Auth", url, headers, data)
    response = requests.post(url, headers=headers, json=data)
    print_response(response)
    response.raise_for_status()
    return response.json()

def refresh_tokens(username, access_token):
    headers = {
        "user-agent": USER_AGENT,
        "content-type": CONTENT_TYPE,
        "accept-encoding": "gzip, deflate, br",
    }
    data = {
        "userId": username,
        "ssoToken": access_token,
        "appId": APP_ID,
    }
    
    print_request("Refresh Tokens", REFRESH_TOKENS_URL, headers, data)
    response = requests.post(REFRESH_TOKENS_URL, headers=headers, json=data)
    print_response(response)
    response.raise_for_status()
    return response.json()

def get_devices(saas_token, country):
    timestamp = str(int(time.time() * 1000))
    nonce = os.urandom(16).hex()
    sign = calculate_md5_hash_bytes(timestamp + nonce + saas_token)
    headers = {
        "platform": TH_PLATFORM,
        "appversion": "5.4.1",
        "thomeversion": TH_VERSION,
        "accesstoken": saas_token,
        "countrycode": country,
        "accept-language": "en",
        "timestamp": timestamp,
        "nonce": nonce,
        "sign": sign,
        "user-agent": USER_AGENT,
        "content-type": CONTENT_TYPE,
        "accept-encoding": "gzip, deflate, br",
    }
    
    print_request("Get Devices", GET_THINGS_URL, headers, {})
    response = requests.post(GET_THINGS_URL, headers=headers, json={})
    print_response(response)
    response.raise_for_status()
    return response.json()

def get_aws_credentials(cognito_token):
    headers = {
        "X-Amz-Target": "AWSCognitoIdentityService.GetCredentialsForIdentity",
        "Content-Type": "application/x-amz-json-1.1",
        "User-Agent": "aws-sdk-iOS/2.26.2 iOS/18.4.1 en_RO",
        "X-Amz-Date": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
        "Accept-Language": "en-GB,en;q=0.9",
    }
    data = {
        "IdentityId": HARDCODED_IDENTITY_ID,
        "Logins": {
            "cognito-identity.amazonaws.com": cognito_token
        }
    }
    
    print_request("AWS Credentials", AWS_COGNITO_URL, headers, data)
    response = requests.post(AWS_COGNITO_URL, headers=headers, json=data)
    print_response(response)
    response.raise_for_status()
    return response.json()

def control_device(device_id, command, credentials):
    url = f"https://{AWS_IOT_ENDPOINT}/topics/%24aws/things/{device_id}/shadow/update?qos=0"
    headers = {
        "Content-Type": "application/x-amz-json-1.0",
        "X-Amz-Security-Token": credentials["SessionToken"],
        "User-Agent": "aws-sdk-iOS/2.26.2 iOS/18.4.1 en_RO",
        "X-Amz-Date": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    }
    
    auth = AWS4Auth(
        credentials["AccessKeyId"],
        credentials["SecretKey"],
        AWS_IOT_REGION,
        'iotdata',
        session_token=credentials["SessionToken"]
    )
    
    data = {
        "state": {"desired": command},
        "clientToken": f"mobile_{int(time.time() * 1000)}"
    }
    
    print_request("Device Control", url, headers, data)
    response = requests.post(url, headers=headers, json=data, auth=auth)
    print_response(response)
    response.raise_for_status()
    return response.json()

def load_config():
    """Load configuration from environment variables"""
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file
    
    required_vars = ['TCL_USERNAME', 'TCL_PASSWORD']
    missing = [var for var in required_vars if var not in os.environ]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return {
        'username': os.environ['TCL_USERNAME'],
        'password': os.environ['TCL_PASSWORD']
    }

if __name__ == "__main__":
    try:
        config = load_config()
        # Initial authentication
        account = do_account_auth(config['username'], config['password'])
        access_token = account["token"]
        country = account["user"]["countryAbbr"]
        username = account["user"]["username"]

        # Token refresh
        refresh_response = refresh_tokens(username, access_token)
        cognito_token = refresh_response["data"]["cognitoToken"]
        saas_token = refresh_response["data"]["saasToken"]

        # Parse JWT to get expiry time
        import jwt
        cognito_token = refresh_response["data"]["cognitoToken"]
        decoded = jwt.decode(cognito_token, options={"verify_signature": False})
        expiry_time = datetime.datetime.fromtimestamp(decoded["exp"])
        if datetime.datetime.utcnow() > expiry_time:
            raise Exception("Cognito token expired - regenerate tokens")

        # AWS credentials
        aws_creds = get_aws_credentials(cognito_token)
        credentials = aws_creds["Credentials"]

        # Get devices
        devices = get_devices(saas_token, country)
        
        # Improved device selection
        print("\nAvailable Devices:")
        device_map = {}
        for idx, device in enumerate(devices['data']):
            print(f"{idx + 1}. {device['nickName']} (ID: {device['deviceId']})")
            device_map[str(idx + 1)] = device['deviceId']

        # Validate device selection
        while True:
            selection = input("\nEnter device NUMBER to control: ")
            if selection in device_map:
                device_id = device_map[selection]
                break
            print(f"Invalid input! Please enter a number between 1-{len(devices['data'])}")

        # Send control command
        command = {"powerSwitch": 0}
        control_response = control_device(device_id, command, {
            "AccessKeyId": credentials["AccessKeyId"],
            "SecretKey": credentials["SecretKey"],
            "SessionToken": credentials["SessionToken"]
        })
        print("\nControl response:", json.dumps(control_response, indent=4))

    except Exception as e:
        print(f"\nERROR: {str(e)}")
