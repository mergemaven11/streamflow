'''
Handlers are passed in to thhe StreamFlow class and handle
actions such as: 
 - launching applications 
 - controlling audio
 - controlling video sources
 -  sending predefined messages
 - and more

'''
import platform
import sys
import subprocess
import webbrowser
import sounddevice as sd
import ctypes
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


def execute_command(command):
    print(f"Executing command: {command}")
    try:
        if command == "chrome":
            if sys.platform == "win32":
                webbrowser.get('windows-default').open('http://www.google.com')
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-a", "Google Chrome"])
            else:
                subprocess.Popen(["google-chrome"])
        elif command == "mute":
            mute_audio()
        elif command == "volume_up":
            volume_up()
        elif command == "volume_down":
            volume_down()
        else:
            # Execute arbitrary shell commands
            if sys.platform == "win32":
                subprocess.Popen(command, shell=True)
            else:
                subprocess.Popen(command.split())
    except Exception as e:
        print(f"Failed to execute command '{command}': {e}")


# ================= COMMANDS ========================

def control_camera():
    print("Controlling camera")
    # Implement camera control logic

def send_greeting():
    print("Sending greeting message")
    # Implement message sending logic

def custom_action():
    print("Performing custom action")
    # Implement custom action logic


def volume_up():
    """
    Increase the system volume by 10%.

    Raises:
        Exception: An error occurred while adjusting the volume.
    """
    print("Increasing volume")
    try:
        # Get the default audio endpoint and its volume control interface
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        # Increase the volume by 10%
        current_volume = volume.GetMasterVolumeLevelScalar()
        new_volume = min(current_volume + 0.1, 1.0)
        volume.SetMasterVolumeLevelScalar(new_volume, None)
        
        print("Volume increased successfully")
    except Exception as e:
        print(f"An error occurred: {e}")

def volume_down():
    """
    Decrease the system volume by 10%.

    Raises:
        Exception: An error occurred while adjusting the volume.
    """
    print("Decreasing volume")
    try:
        # Get the default audio endpoint and its volume control interface
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        # Decrease the volume by 10%
        current_volume = volume.GetMasterVolumeLevelScalar()
        new_volume = max(current_volume - 0.1, 0.0)
        volume.SetMasterVolumeLevelScalar(new_volume, None)
        
        print("Volume decreased successfully")
    except Exception as e:
        print(f"An error occurred: {e}")

def mute_audio():
    """
    Toggle the mute state of the system audio.

    Raises:
        Exception: An error occurred while toggling the mute state.
    """
    print("Toggling mute state")
    try:
        # Get the default audio endpoint and its volume control interface
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        # Toggle the mute state
        is_muted = volume.GetMute()
        volume.SetMute(not is_muted, None)

        if is_muted:
            print("Audio unmuted successfully")
        else:
            print("Audio muted successfully")
    except Exception as e:
        print(f"An error occurred: {e}")