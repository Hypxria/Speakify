# Voice-Activation Control Branch

# imports
import spotipy
import speech_recognition as sr
import random
import json
from spotipy.oauth2 import SpotifyOAuth
from rich import print
from methods import *
from windows_toasts import Toast, WindowsToaster
import asyncio
from src.initialize_speech import *
import time
import queue
import threading
import numpy as np

stop_flag = threading.Event()

def manual_input():
    while True:
        user_input = input("Enter command (or 'quit' to exit): ").strip().lower()
        if user_input == 'quit':
            asyncio.run(exit_application())
            break
        
        commands = user_input.split("and")
        for single_command in commands:
            words = single_command.strip().split()
            if words:
                command_queue.put(words)

# Define things
def listen_for_wake_phrase(recognizer, audio, sensitivity=0.325):
    rms = 0
    """Check if the wake phrase 'hey spotify' is in the audio."""
    recognizer = sr.Recognizer()
    try:
        # Use a more noise-resistant recognition method
        text = recognizer.recognize_google(audio_data=audio, show_all=False, with_confidence=True)
        if text and text[0][1] > 0.1:  # Check if confidence is above 80%
            # Calculate the root-mean-square (RMS) value of the audio data
            rms = np.sqrt(np.mean(np.square(audio.get_array_of_samples())))
            
            volume_threshold = -5 * (1 - sensitivity)  # Example calculation, adjust as needed
        
            if rms > volume_threshold:
            # Use a recognition method that allows specifying the audio duration
                print(f"Recognized text: {text.lower()}")
                return "hey spotify" in text.lower()

            
        return False
    except sr.UnknownValueError:
        return False
    except sr.RequestError:
        print("[italic red]Could not request results from Google Speech Recognition service.[/italic red]")
        return False

def check_play_playlist(command_words):
    required_keywords = ["play", "playlist"]
    lowercase_command = [word.lower() for word in command_words]
    return all(keyword in lowercase_command for keyword in required_keywords)

commands = ["play", "album", "artist", "playlist", "pause", "resume", "volume", "repeat", "shuffle"]

audio_queue = queue.Queue()
command_queue = queue.Queue()

def load_settings():
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        return settings
    except FileNotFoundError:
        print("Settings file not found. Using default settings.")
        return {"defaultMode": "normal"}
    except json.JSONDecodeError:
        print("Error parsing settings file. Using default settings.")
        return {"defaultMode": "normal"}

def set_initial_mode():
    settings = load_settings()
    return settings

# Define Spotify scopes
SPOTIFY_SCOPES = [
    "ugc-image-upload", "user-read-playback-state", "user-modify-playback-state",
    "user-follow-modify", "user-read-private", "user-follow-read", "user-library-modify",
    "user-library-read", "streaming", "user-read-playback-position", "app-remote-control",
    "user-read-email", "user-read-currently-playing", "user-read-recently-played",
    "playlist-modify-private", "playlist-read-collaborative", "playlist-read-private",
    "user-top-read", "playlist-modify-public"
]

# Initialize Spotify client
sp = spotipy.Spotify(
    auth_manager = SpotifyOAuth(
        scope =" ,".join(SPOTIFY_SCOPES),
        client_id = "CLIENT_ID_HERE",
        client_secret = "CLIENT_SECRET_HERE",
        redirect_uri = "http://localhost:8888/callback"
    ),
    requests_timeout=300
)

def process_commands():
    while not stop_flag.is_set():
        try:
            words = command_queue.get(timeout=0.1)
            if process_command(words):
                break
        except queue.Empty:
            continue

def listen_for_wake_phrase(recognizer, audio):
    """Check if the wake phrase 'hey spotify' is in the audio."""
    try:
        text = recognizer.recognize_google(audio_data=audio).lower()
        return "hey spotify" in text
    except sr.UnknownValueError:
        return False
    except sr.RequestError:
        print("[italic red]Could not request results from Google Speech Recognition service.[/italic red]")
        return False

def check_play_playlist(command_words):
    # Check if the command is to play a playlist 
    required_keywords = ["play", "playlist"]
    lowercase_command = [word.lower() for word in command_words]
    return all(keyword in lowercase_command for keyword in required_keywords)

def process_command(words):
    if not words:
        return False
    command = [word for word in words if word not in ['hey', 'spotify']]
    

    if command[0] == "next":
        if len(command) > 1 and command[1].isdigit():
            count = int(command[    1])
            for _ in range(count):
                asyncio.run(next_track(spotify=sp))
            print(f"[bold deep_sky_blue2]Skipped [/bold deep_sky_blue2][italic spring_green3]{count}[/italic spring_green3][bold deep_sky_blue2] tracks[/bold deep_sky_blue2]")
        else:
            asyncio.run(next_track(spotify=sp))
        
    #add to playlist
    elif command[0] == "add" and len(command) > 2:
        if command[1] == "to":
            playlist_name = " ".join(command[2:])
        elif command[1] == "this" and command[2] == "song" and command[3] == "to":
            playlist_name = " ".join(command[4:])
        else:
            print("Invalid command format. Please use 'add to <playlist_name>' or 'add this song to <playlist_name>'")
            return
        asyncio.run(add_current_song_to_playlist(spotify=sp, playlist_name=playlist_name))
    
    elif command[0] == "remove" and len(command) > 2:
        if command[1] == "this" and command[2] == "song":
            current_track = sp.currently_playing()['item']
            if current_track:
                current_context = sp.currently_playing()['context']
                if current_context and current_context['type'] == 'playlist':
                    playlist_id = current_context['uri'].split(':')[-1]
                    sp.playlist_remove_all_occurrences_of_items(playlist_id=playlist_id, items=[current_track['id']])
                    print(f"Removed '{current_track['name']}' from the current playlist.")
                else:
                    print("The currently playing song is not part of a playlist.")
            else:
                print("No song is currently playing.")
        else:
            print("Invalid command format. Please use 'remove this song'")
            return
        
    elif command[0] == "pause":
        asyncio.run(pause_track(spotify=sp))
    
    elif command[0] == "resume":
        asyncio.run(resume_track(spotify=sp))
    
    elif command[0] == 'back':
        if len(command) > 1 and command[1].isdigit():
            count = int(command[1])
            for _ in range(count):
                asyncio.run(next_track(spotify=sp))
            print(f"[bold deep_sky_blue2]Went back [/bold deep_sky_blue2][italic spring_green3]{count}[/italic spring_green3][bold deep_sky_blue2] tracks[/bold deep_sky_blue2]")
    
    elif command[0] == "quit":
        asyncio.run(exit_application())
        return True  # Signal to exit the main loop
    
    elif command[0] == "repeat":
        asyncio.run(repeat_track(spotify=sp))
        
    elif command[0] == "current" and len(command) > 1 and command[1] == "song":
        track = asyncio.run(get_current_song(spotify=sp))
        print(f"[bold deep_sky_blue2]Current track:[/bold deep_sky_blue2] [italic spring_green3]{track}[/italic spring_green3]")
    
    elif command[0] == "go" and len(command) > 1 and command[1] == "back":
        asyncio.run(play_previous_song(spotify=sp))
    
    elif command[0] == "shuffle":
        if len(command) > 1:
            if command[1] == "on":
                asyncio.run(shuffle(spotify=sp, state="on"))
            elif command[1] == "off":
                asyncio.run(shuffle(spotify=sp, state="off"))
            elif command[1] == "status":
                shuffle_status = asyncio.run(is_shuffle_on(spotify=sp))
                state_str = "ON" if shuffle_status else "OFF"
                color = "spring_green3" if shuffle_status else "red"
                print(f"[bold deep_sky_blue2]Shuffle is currently [/bold deep_sky_blue2][italic {color}]{state_str}[/italic {color}]")
            else:
                print("[italic red]Invalid shuffle command. Use 'on', 'off', or 'status'.[/italic red]")
        else:
            # If no argument is provided, toggle the shuffle state
            if asyncio.run(is_shuffle_on(spotify=sp)):
                asyncio.run(shuffle(spotify=sp, state="off"))
            else:
                asyncio.run(shuffle(spotify=sp, state="on"))
    
    #play playlist
    elif command[0] == "playlist":
        handle_playlist_command(words[1:])
    
    elif command[0] == "play":
        handle_play_command(words[1:])
    
    #play album
    elif command[0] == "album":
        handle_album_command(words[1:])
    
    #play artist
    elif command[0] == "artist":
        handle_artist_command(words[1:])
    
    #change volume
    elif command[0] == "volume":
        handle_volume_command(words[1:])
    
    else:
        print("[italic red]Unknown command.[/italic red]")

    return False  # Continue the main loop

def handle_playlist_command(words):
    # Handle the 'playlist' command.
    playlists, playlist_ids = asyncio.run(get_user_playlists(spotify=sp))
    
    name = " ".join(words)
    
    if name.lower() in playlists:
        for i, playlist in enumerate(playlists):
            if name.lower() == playlist.lower():
                asyncio.run(play_playlist(spotify=sp, playlist_id=playlist_ids[i]))
                print(f"[bold deep_sky_blue2]Playing playlist:[/bold deep_sky_blue2] [italic spring_green3]{name}[/italic spring_green3]")
                break
    else:
        print("[italic red]Could not find playlist.[/italic red]")

def handle_play_command(words):
    # Handle the 'play' command 
    name = " ".join(words)
    if name == "random":
        tracks = asyncio.run(get_user_saved_tracks(spotify=sp))
        random_track = random.choice(tracks)
        uri = asyncio.run(get_track_uri(spotify=sp, name=random_track))
        asyncio.run(play_track(spotify=sp, uri=uri))
        print(f"[bold deep_sky_blue2]Playing track:[/bold deep_sky_blue2] [italic spring_green3]{random_track}[/italic spring_green3]")
    else:
        uri = asyncio.run(get_track_uri(spotify=sp, name=name))
        asyncio.run(play_track(spotify=sp, uri=uri))
        print(f"[bold deep_sky_blue2]Playing track:[/bold deep_sky_blue2] [italic spring_green3]{name}[/italic spring_green3]")

def handle_album_command(words):
    # Handle the 'album' command 
    name = " ".join(words)
    uri = asyncio.run(get_album_uri(spotify=sp, name=name))
    asyncio.run(play_album(spotify=sp, uri=uri))
    print(f"[bold deep_sky_blue2]Playing album:[/bold deep_sky_blue2] [italic spring_green3]{name}[/italic spring_green3]")

def handle_artist_command(words):
    # Handle the 'artist' command 
    name = " ".join(words)
    if name == "random":
        random_artist = random.choice(get_user_followed_artists(spotify=sp))
        uri = asyncio.run(get_artist_uri(spotify=sp, name=random_artist))
        asyncio.run(play_artist(spotify=sp, uri=uri))
        print(f"[bold deep_sky_blue2]Playing artist:[/bold deep_sky_blue2] [italic spring_green3]{random_artist}[/italic spring_green3]")
    else:
        uri = asyncio.run(get_artist_uri(spotify=sp, name=name))
        asyncio.run(play_artist(spotify=sp, uri=uri))
        print(f"[bold deep_sky_blue2]Playing artist:[/bold deep_sky_blue2] [italic spring_green3]{name}[/italic spring_green3]")


def handle_volume_command(words):
    # Handle the 'volume' command 
    volume_map = {
    'one': 10, '1': 10,
    'two': 20, '2': 20,
    'three': 30, '3': 30,
    'four': 40, '4': 40,
    'five': 50, '5': 50,
    'six': 60, '6': 60,
    'seven': 70, '7': 70,
    'eight': 80, '8': 80,
    'nine': 90, '9': 90,
    'ten': 100, '10': 100
    }

    volume_input = words[len(words)-1].lower()
    
    if volume_input in volume_map:
        volume = volume_map[volume_input]
        asyncio.run(change_volume(spotify=sp, volume=volume))
        print(f"[bold spring_green3]Volume set to {volume}%[/bold spring_green3]")
    else:
        try:
            if volume_input[-1] == '%':
                volume_input = volume_input[:-1]
            volume = int(volume_input)
            if 0 <= volume <= 100:
                asyncio.run(change_volume(spotify=sp, volume=volume))
                print(f"[bold spring_green3]Volume set to {volume}%[/bold spring_green3]")
            else:
                print("[italic red]Volume must be between 0 and 100.[/italic red]")
        except ValueError:
            print("[italic red]Invalid volume level. Please use a number between 0 and 100 or say 'one' through 'ten'.[/italic red]")

def process_audio(recognizer):
    while True:
        try:
            audio = audio_queue.get(timeout=0.1)
            if listen_for_wake_phrase(recognizer, audio):
                print("[green]Wake phrase detected! Waiting for command...[/green]")
                try:
                    command = recognizer.recognize_google(audio_data=audio).lower()
                    print(f"[medium_purple3]{command}[/medium_purple3]")
                    
                    # Split the command into individual commands
                    commands = command.split("and")
                    
                    for single_command in commands:
                        words = single_command.strip().split()
                        if words:
                            command_queue.put(words)
                    
                except sr.UnknownValueError:
                    print("[italic red]Sorry, I didn't catch that. Could you repeat?[/italic red]")
                except sr.RequestError:
                    print("[italic red]Could not request results from Google Speech Recognition service.[/italic red]")
        except queue.Empty:
            continue

def main():
    print('[hot_pink2]Voice Control for Spotify[/hot_pink2]')
    
    initial = set_initial_mode() 
    print(initial["defaultMode"])
    if initial["defaultMode"] == "0":
        input_mode = "0"
    elif initial["defaultMode"] == "1":
        input_mode = "1"
    elif initial["defaultMode"] == "2":
        input_mode = "2"     
    
    command_thread = threading.Thread(target=process_commands)
    command_thread.start()
    
    try:
        if input_mode == '0':
            input_mode = input("Choose input mode (1 for voice, 2 for manual): ").strip()
        elif input_mode == '1':
            voice_control()
        elif input_mode == '2':
            manual_input()
        else:
            print("Invalid input. Exiting.")
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Stopping all processes...")
    finally:
        stop_flag.set()  # Signal all threads to stop
        command_thread.join(timeout=1)  # Wait for command thread to finish
        print("Shutting down...")

def voice_control():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)

    print("[green]Listening for wake phrase 'Hey Spotify'...[/green]")
    toaster = WindowsToaster('Spotify')
    newToast = Toast()
    newToast.text_fields = ["Ready!"]
    toaster.show_toast(newToast)
    run_audio_processing(recognizer, microphone)

def run_audio_processing(recognizer, microphone):
    global audio_queue
    audio_queue = queue.Queue()

    def callback(recognizer, audio):
        audio_queue.put(audio)

    stop_listening = recognizer.listen_in_background(microphone, callback)

    # Start the audio processing thread
    audio_thread = threading.Thread(target=process_audio, args=(recognizer,))
    audio_thread.daemon = True
    audio_thread.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("[italic yellow]Stopping voice control...[/italic yellow]")
    finally:
        stop_listening(wait_for_stop=False)
        exit()
            
if __name__ == "__main__":
    main()