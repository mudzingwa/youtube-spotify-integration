import jwt
from secrets import spotify_token

def get_token_scopes(access_token):
    token_info = jwt.decode(access_token, options={"verify_signature": False})
    if "scope" in token_info:
        return token_info["scope"].split()
    else:
        return []

scopes = get_token_scopes(spotify_token)
print("Token scopes:", scopes)

required_scopes = ["playlist-modify-private", "playlist-read-private"]
if all(scope in scopes for scope in required_scopes):
    print("Token has all necessary scopes.")
else:
    print("Token is missing some necessary scopes.")
