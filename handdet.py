import tkinter as tk
from tkinter import simpledialog
import cv2
import numpy as np
import mediapipe as mp
import time
import pandas as pd
import os

# Get player name using Tkinter
def get_input():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True) 
    while True:
        name = simpledialog.askstring("Input", "Enter name:", parent=root)
        if name:  # If name is not empty or None
            return name
        else:
            print("Name cannot be empty. Please enter again.")

name = get_input()

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2)

# Game settings
game_duration = 1200  # seconds
warning_duration = 1.5 # Warning before red light
game_start_time = time.time()
is_red_light = False
player_eliminated = False

# Set fixed durations for 5 switches
red_light_duration = 10
green_light_duration = 190

# Track light phases
light_start_time = time.time()
warning_time = None

# Open Camera
cap = cv2.VideoCapture(0)

# Create the Light Overlay using Tkinter
root = tk.Tk()
root.geometry("300x100+100+50")  # Adjusted window size for timer
root.title("Light Overlay")
root.configure(bg="black")
root.attributes("-topmost", True)  # Keep it on top
root.protocol("WM_DELETE_WINDOW", lambda: None)

# Canvas to draw the overlay
canvas = tk.Canvas(root, width=300, height=50, bg="black", bd=0, highlightthickness=0)
canvas.pack()

# Timer Label
timer_label = tk.Label(root, font=("Helvetica", 16), fg="white", bg="black")
timer_label.pack()

# Function to detect hand movement
def detect_hand_movement(frame):
    results = hands.process(frame)
    return bool(results.multi_hand_landmarks)  # True if hand is detected

# Function to update the timer
def update_timer():
    remaining_time = game_duration - (time.time() - game_start_time)
    if remaining_time > 0:
        mins, secs = divmod(int(remaining_time), 60)
        timer_label.config(text=f"Time Left: {mins:02d}:{secs:02d}")
        root.after(1000, update_timer)  # Call this function again after 1 second
    else:
        timer_label.config(text="Time's up!")

# Start the timer
update_timer()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Flip the frame for a mirror effect
    frame = cv2.flip(frame, 1)

    # Check elapsed time
    elapsed_time = time.time() - game_start_time
    if elapsed_time > game_duration:
        break

    # Time spent in current light phase
    current_light_time = time.time() - light_start_time

    # Set warning before switching to RED light
    if not is_red_light and current_light_time >= green_light_duration - warning_duration and warning_time is None:
        warning_time = time.time()

    # Switch to RED light
    if not is_red_light and current_light_time >= green_light_duration:
        is_red_light = True
        light_start_time = time.time()
        warning_time = None

    # Switch to GREEN light
    elif is_red_light and current_light_time >= red_light_duration:
        is_red_light = False
        light_start_time = time.time()
        warning_time = None

    # Handle Warning Message
    if warning_time and time.time() - warning_time <= warning_duration:
        light_color = (255, 0, 255)  # Pink for warning
        light_text = "WARNING - RED LIGHT SOON!"
    else:
        light_color = (0, 0, 255) if is_red_light else (0, 255, 0)
        light_text = "RED LIGHT" if is_red_light else "GREEN LIGHT"

    # Update Light Overlay
    canvas.create_rectangle(0, 0, 300, 50, fill="black", outline="black")  # Black background for the overlay
    canvas.create_rectangle(0, 0, 300, 50, fill=f"#{light_color[2]:02x}{light_color[1]:02x}{light_color[0]:02x}")  # Light color
    canvas.create_text(150, 25, text=light_text, font=("Helvetica", 12), fill="white")  # Light text

    # Detect Hand Movement During RED LIGHT
    if is_red_light and detect_hand_movement(frame):
        player_eliminated = True
        break

    # Show Main Game Window
    cv2.imshow("Red Light Green Light", frame)

    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    # Update the Tkinter window to reflect changes
    root.update()

# Game Over Logic
cap.release()
cv2.destroyAllWindows()

if player_eliminated:
    print("You have been eliminated!")
else:   
    print("You survived the game!")

# Save Results
file_name = "game_results.xlsx"
new_entry = pd.DataFrame([[name, elapsed_time, "Eliminated" if player_eliminated else "Survived"]],
                         columns=["Player Name", "Time Survived (s)", "Status"])

if os.path.exists(file_name):
    existing_data = pd.read_excel(file_name)
    updated_data = pd.concat([existing_data, new_entry], ignore_index=True)
else:
    updated_data = new_entry

updated_data.to_excel(file_name, index=False)
print(f"Results saved to {file_name} ✅")