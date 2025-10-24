# utils/reminder.py
import threading
import time
from datetime import datetime
from plyer import notification
from playsound import playsound
import os

active_reminders = []

def schedule_reminder_at(reminder_time, message, sound_file=None):
    """
    Schedule a reminder at a specific HH:MM time with notification + custom MP3 sound.
    Supports multiple reminders simultaneously.
    """
    if sound_file is None:
        # Default MP3 in project root
        sound_file = os.path.join(os.path.dirname(__file__), "..", "alarm.mp3")

    active_reminders.append({"time": reminder_time, "message": message, "sound": sound_file})

    def reminder_thread(reminder):
        while True:
            now = datetime.now().strftime("%H:%M")
            if now == reminder["time"]:
                # Desktop notification
                notification.notify(
                    title="💊 Medicine Reminder",
                    message=reminder["message"],
                    timeout=10
                )
                # Play MP3 sound
                try:
                    playsound(reminder["sound"])
                except Exception as e:
                    print(f"Failed to play sound: {e}")
                print(f"Reminder triggered at {now}: {reminder['message']}")
                break
            time.sleep(30)  # check every 30 seconds

    thread = threading.Thread(target=reminder_thread, args=(active_reminders[-1],), daemon=True)
    thread.start()
    print(f"Reminder scheduled for {reminder_time}: {message}")
