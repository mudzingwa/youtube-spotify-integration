import base64
import requests

client_id = ' '
client_secret = ' '

auth_url = 'https://accounts.spotify.com/api/token'
auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode('utf-8')).decode('utf-8')
auth_payload = {
    "grant_type": "client_credentials"
}

auth_headers = {
    "Authorization": f"Basic {auth_header}"
}

response = requests.post(auth_url, data=auth_payload, headers=auth_headers)

if response.status_code == 200:
    access_token = response.json().get('access_token')
    print("Access Token:", access_token)
else:
    print("Error:", response.status_code, response.json())
