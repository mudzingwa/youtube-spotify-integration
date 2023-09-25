import json
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
import youtube_dl

from exceptions import ResponseException
from secrets import spotify_token, spotify_user_id

client_id = "0ba42c7d017040c79747fbed4d4ffe22"
client_secret = "2b6a723f47ff4267ba1f4df5382656aa"

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
        scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_local_server()  # Use run_local_server() instead of run_console()


        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    def get_spotify_playlist_tracks(self):
        playlist_id = "3lRp9mT1AeLbLQDj1q3vuU?si=6d20720181d1402a"  # Replace with the Spotify playlist ID you want to convert
        query = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = {
            "Authorization": "Bearer {}".format(spotify_token)
        }
        response = requests.get(query, headers=headers)
        response_json = response.json()

        if "items" not in response_json:
            print("No 'items' key found in the Spotify API response.")
            return None

        tracks = response_json["items"]
        return tracks

    def get_liked_videos(self):
        youtube_dl.utils.std_headers['Referer'] = 'https://www.youtube.com/'

        # Get tracks from Spotify playlist
        spotify_tracks = self.get_spotify_playlist_tracks()

        for item in spotify_tracks:
            track_info = item["track"]
            song_name = track_info["name"]
            artist = track_info["artists"][0]["name"]

            youtube_url = self.search_youtube_video(song_name, artist)

            if youtube_url is not None:
                video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)
                video_title = video["title"]

                self.all_song_info[video_title] = {
                    "youtube_url": youtube_url,
                    "song_name": song_name,
                    "artist": artist,
                }

    def search_youtube_video(self, song_name, artist):
        # Search for the song on YouTube
        query = f"{song_name} {artist} official video"
        youtube_url = None

        youtube_search = self.youtube_client.search().list(
            q=query,
            part="id",
            maxResults=1
        ).execute()

        if "items" in youtube_search:
            video_id = youtube_search["items"][0]["id"]["videoId"]
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"

        return youtube_url

    def create_youtube_playlist(self):
        request = self.youtube_client.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": "Converted Spotify Playlist",
                    "description": "Converted from Spotify",
                    "tags": ["spotify", "music"]
                },
                "status": {
                    "privacyStatus": "public"
                }
            }
        )
        response = request.execute()
        return response["id"]

    def add_song_to_playlist(self):
        self.get_liked_videos()

        uris = [info["youtube_url"] for song_title, info in self.all_song_info.items()]

        new_playlist_id = self.create_youtube_playlist()

        for uri in uris:
            video_id = uri.split("=")[-1]
            request = self.youtube_client.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": new_playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            )
            request.execute()

        print("YouTube playlist created and videos added!")

if __name__ == '__main__':
    cp = CreatePlaylist()
    cp.add_song_to_playlist()
