#################### Import statements and constants ####################
import tkinter as tk
import subprocess
import re

MAX_USERNAME_LENGTH = 20
DEFAULT_PORT = 9001

#################### Functions ####################

def join_chat():
    username = name_entry.get()  
    port = port_entry.get()
    
    if not port:
        port = DEFAULT_PORT
        
    # validate username and port
    if username:
        if len(username) <= MAX_USERNAME_LENGTH:
            if port:
                if len(port) == 4:
                    if re.match(r'^\d+$', port):
                        welcome_label.config(text=f"Welcome, {username}!")
                        launch_chat(username, port)
                    else:
                        welcome_label.config(text="Port must be characters 0-9")
                else:
                    welcome_label.config(text="Port must be 4 digits long.")
            else:
                welcome_label.config(text="Please enter a 4 digit port.")
        else:
            welcome_label.config(text="Names cannot be longer than 20 characters.")
    else:
        welcome_label.config(text="Please enter your name.")
        
def launch_chat(username, port):
    # Close the Tkinter window
    logIn.destroy()
    # Launch the chat.py script with the provided username, port, and ip
    subprocess.run(['python3', 'Chat.py', username, port])

#################### Main ####################
logIn = tk.Tk()
logIn.title("Stupid Discord")
logIn.geometry("400x200")  # Default window size
logIn.config(bg="#36393F")

# Create a title
title_label = tk.Label(logIn, text="Start a conversation", font=("Helvetica", 16), fg="white", bg="#36393F")
title_label.pack(pady=10)

# Create a frame to contain the entry and button widgets
input_frame = tk.Frame(logIn, bg="#2F3136")
input_frame.pack(pady=10)

# Create an entry widget for entering the name with default text
default_text = "Enter your name"
name_entry = tk.Entry(input_frame, width=30, bg="#36393F", fg="white", insertbackground="white")
name_entry.insert(0, default_text)  # Set default text
name_entry.pack(side=tk.TOP, padx=5)

# Remove default text when the entry is clicked
def on_entry_click(event):
    if name_entry.get() == default_text:
        name_entry.delete(0, tk.END)
        name_entry.config(fg='white')  # Change text color to white

# Bind the click event to the entry widget
name_entry.bind('<FocusIn>', on_entry_click)

# Port entry -------------------
# Create an entry widget for entering the name with default text
port_default_text = "9001"
port_entry = tk.Entry(input_frame, width=30, bg="#36393F", fg="white", insertbackground="white")
port_entry.insert(0, port_default_text)  # Set default text
port_entry.pack(side=tk.TOP, padx=5)

# Remove default text when the entry is clicked
def on_entry_click(event):
    if port_entry.get() == port_default_text:
        port_entry.delete(0, tk.END)
        port_entry.config(fg='white')  # Change text color to white

# Bind the click event to the entry widget
port_entry.bind('<FocusIn>', on_entry_click)

# Create a button to join
join_button = tk.Button(input_frame, text="Join", command=join_chat, bg="#7289DA", fg="white")
join_button.pack(side=tk.TOP, padx=5)

# Label to display a welcome message
welcome_label = tk.Label(logIn, text="", fg="white", bg="#36393F")
welcome_label.pack(pady=10)

# Run the GUI
logIn.mainloop()
