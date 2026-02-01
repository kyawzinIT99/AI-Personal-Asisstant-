import sys
import os

def play_sound(sound_type):
    # Mac/Linux-compatible sound player
    try:
        if sys.platform == "darwin":
            if sound_type == "success":
                os.system("afplay /System/Library/Sounds/Glass.aiff")
            elif sound_type == "waiting":
                os.system("afplay /System/Library/Sounds/Ping.aiff")
        else:
            # Fallback for Linux usually involves `aplay` or `paplay` or standard beep
            print(f"[{sound_type.upper()}] (Sound playback not implemented for {sys.platform})")
    except Exception as e:
        print(f"Failed to play sound: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 alert_user.py [success|waiting]")
        sys.exit(1)
    
    sound = sys.argv[1].lower()
    if sound in ["success", "done"]:
        play_sound("success")
        print("Notification: Task Completed.")
    elif sound == "waiting":
        play_sound("waiting")
        print("Notification: Waiting for input.")
    else:
        print("Unknown alert type.")
