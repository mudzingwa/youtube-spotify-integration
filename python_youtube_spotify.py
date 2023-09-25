import json
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
import youtube_dl

from exceptions import ResponseException
from secrets import spotify_token, spotify_user_id

class CreatePlaylist:

    def __init__(self):
        self.youtube_client = self.get_youtube_client()
        self.all_song_info = {}


    # GETTING CREDENTIALS AND YOUTUBE API
    def get_youtube_client(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_local_server() 

        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    #  GETTING LIKED VIDEOS FROM YOUTUBE
    def get_liked_videos(self):
        youtube_dl.utils.std_headers['Referer'] = 'https://www.youtube.com/'

        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like"
        )
        response = request.execute()

        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])
           
            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)
            song_name = video["track"]
            artist = video["artist"]

            if song_name is not None and artist is not None:
                self.all_song_info[video_title] = {
                    "youtube_url": youtube_url,
                    "song_name": song_name,
                    "artist": artist,

                    "spotify_uri": self.get_spotify_uri(song_name, artist)

                }

    # CREATING A NEW SPOTIFY PLAYLIST
    def create_playlist(self):
        request_body = ({
            "name": "Liked Youtube Videos",
            "description": "All liked Youtube Videos",
            "public": True
        })

        query = "https://api.spotify.com/v1/users/{}/playlists".format(spotify_user_id)  
        response = requests.post(
            query,
            data=json.dumps(request_body),  
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )

        response_json = response.json()

        if "error" in response_json:
            error_message = response_json["error"]["message"]
            raise Exception(f"Error creating playlist: {error_message}")

        return response_json["id"]


    # GETTING SPOTIFY AUTHORIZATION AND URI
    def get_spotify_uri(self, song_name, artist):
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
           song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        response_json = response.json()

        if "tracks" not in response_json:
            print("No 'tracks' key found in the Spotify API response.")
            return None

        songs = response_json["tracks"]["items"]

        if not songs:
            print("No 'items' found in the Spotify API response.")
            return None

        uri = songs[0]["uri"]

        return uri


    # ADDING SONGS TO THE PLAYLIST
    def add_song_to_playlist(self):
        self.get_liked_videos()

        uris = [info["spotify_uri"] for song, info in self.all_song_info.items()]

        playlist_id = self.create_playlist()
        request_data = json.dumps({
        "uris": uris
        })

        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )


        if response.status_code != 200:
            raise ResponseException(response.status_code)

        response_json = response.json()
        return response_json


if __name__ == '__main__':
    cp = CreatePlaylist()
    cp.add_song_to_playlist()
