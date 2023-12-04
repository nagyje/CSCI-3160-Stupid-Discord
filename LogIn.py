#################### Import statements and constants ####################
import tkinter as tk
import subprocess

MAX_USERNAME_LENGTH = 20

#################### Functions ####################

def join_chat():
    username = name_entry.get()
    if username:
        if len(username) <= MAX_USERNAME_LENGTH:
            welcome_label.config(text=f"Welcome, {username}!")
            launch_chat(username)
        else:
            welcome_label.config(text="Names cannot be longer than 20 characters.")
    else:
        welcome_label.config(text="Please enter your name.")
        
def launch_chat(username):
    # Close the Tkinter window
    logIn.destroy()
    # Launch the chat.py script with the provided username
    subprocess.run(['python3', 'Chat.py', username])

#################### Main ####################
logIn = tk.Tk()
logIn.title("Stupid Discord")
logIn.geometry("400x135")  # Default window size

# Create a title
title_label = tk.Label(logIn, text="Start a conversation", font=("Helvetica", 16))
title_label.pack(pady=10)

# Create a frame to contain the entry and button widgets
input_frame = tk.Frame(logIn)
input_frame.pack(pady=10)

# Create an entry widget for entering the name with default text
default_text = "Enter your name"
name_entry = tk.Entry(input_frame, width=30)
name_entry.insert(0, default_text)  # Set default text
name_entry.pack(side=tk.LEFT, padx=5)

# Remove default text when the entry is clicked
def on_entry_click(event):
    if name_entry.get() == default_text:
        name_entry.delete(0, tk.END)
        name_entry.config(fg='black')  # Change text color to black

# Bind the click event to the entry widget
name_entry.bind('<FocusIn>', on_entry_click)

# Create a button to join
join_button = tk.Button(input_frame, text="Join", command=join_chat)
join_button.pack(side=tk.LEFT, padx=5)

# Label to display a welcome message
welcome_label = tk.Label(logIn, text="")
welcome_label.pack(pady=10)

# Run the GUI
logIn.mainloop()