# Speakify
Python-based application that enables hands-free control of your Spotify playback using voice commands.



## Installation
- Make a application at https://developer.spotify.com (seen below)<br />
- Add a Redirect URI to the application and set it as http://localhost:8888/callback

https://github.com/user-attachments/assets/05bc1887-d137-452e-9935-c5e33af18ceb

Don't try using the ID and Secret here, I already deleted it.

- Clone/Download This repo
- Set variables "client_id" and "client_secret" to their assigned spots
- Run main.py (run again if needed)
- Move on to usage

## Usage
Call wake phrase by saying "Hey Spotify"

Then follow up with any of these commands

#### Features:
- Play {track name}; to play a track (say play random to play a random track from your  saved tracks)
- Album {album name}; to play an album
- Artist {artist name}; to play songs of an artist (say artist random to play a random artist from your followed artists)
- Playlist {playlist name}; to play a playlist from Your Library
- Pause; to pause the music
- Resume; to resume the music
- Next/Skip {number(optional)}; to skip to the next track
- Add To/Add this song to {playlist name}; to add the currently playing song to the playlist
- Remove this song; to remove playing song from current playlist
- Volume {number}; to set the volume to a number between 0 and 100
- Repeat; to put the current track in on repeat
- Shuffle {ON/OFF/BLANK}; to turn shuffle on or off
- Current song; to see the current song playing (ONLY IN COMMAND LINE)
- Go back/back; to go back to the last played song.
- Quit; to quit the program

## Settings
You can change the default input setting by changing settings.json (instructions inside)

#### Hint: Manual input doesn't require "Hey Spotify"

## Acknowledgements

 - [Spotify Voice Control](https://github.com/nexxeln/spotify-voice-control)
This was the very basis of the project, and what I copied the code from the beginning. I feel that at this point, the code has changed enough that it could be considered a different thing, but I want to put their repo out there albeit outdated.
 - [Spotipy](https://github.com/spotipy-dev/spotipy)



## FAQ

#### Will you add this feature?

I mean... If I feel its a good idea. Some features are unfeasable due to just my incompetence or restrictions on possible features due to the [Spotipy](https://github.com/spotipy-dev/spotipy) library 

#### Why isn't it picking up my mic!?

I dunno. Try setting your default input device in Windows settings. This is an unfinished project for now.

#### Can you help me with this issue?

No.

#### How can I reach out to you?

Uh... Good question. Check my profile and see if I put my socials on there yet.
