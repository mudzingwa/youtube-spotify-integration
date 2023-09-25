import json
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
import youtube_dl

from exceptions import ResponseException
from secrets import spotify_token, spotify_user_id, youtube_api_key

class CreatePlaylist:
    def __init__(self):
        self.youtube_client = self.get_youtube_client()
        self.all_song_info = {}

    def get_youtube_client(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_local_server()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    def get_liked_songs_from_spotify(self):
        query = "https://api.spotify.com/v1/me/tracks"
        response = requests.get(
            query,
            headers={
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )

        response_json = response.json()
        items = response_json["items"]

        for item in items:
            track = item["track"]
            song_name = track["name"]
            artist = track["artists"][0]["name"]
            spotify_uri = track["uri"]

            self.all_song_info[song_name] = {
                "song_name": song_name,
                "artist": artist,
                "spotify_uri": spotify_uri
            }

    def create_youtube_playlist(self):
        request_body = {
            "snippet": {
                "title": "Liked Spotify Videos",
                "description": "All liked videos from Spotify",
            },
            "status": {
                "privacyStatus": "public",
            },
        }

        request = self.youtube_client.playlists().insert(
            part="snippet,status",
            body=request_body
        )
        response = request.execute()

        return response["id"]

    def add_videos_to_youtube_playlist(self, playlist_id, video_ids):
        request_body = {
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": ""
                }
            }
        }

        for video_id in video_ids:
            request_body["snippet"]["resourceId"]["videoId"] = video_id

            request = self.youtube_client.playlistItems().insert(
                part="snippet",
                body=request_body
            )
            response = request.execute()

    def add_songs_to_playlist(self):
        self.get_liked_songs_from_spotify()

        # get video IDs
        video_ids = [info["spotify_uri"].split(":")[2] for song, info in self.all_song_info.items()]

        # create a new YouTube playlist
        playlist_id = self.create_youtube_playlist()

        # add all videos to the new YouTube playlist
        self.add_videos_to_youtube_playlist(playlist_id, video_ids)


if __name__ == '__main__':
    cp = CreatePlaylist()
    cp.add_songs_to_playlist()
