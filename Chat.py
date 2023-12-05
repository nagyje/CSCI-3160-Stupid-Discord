"""
Program Name: Chat.py
Author: Sophia Herrell
Contributors: Joe Nagy 
Last Edited: 12/5/23
Description: Connects a user as a client to a server. 
             Facilitates light chatting only. 

Additional Information:
- This program is designed to be run from a WSL instance 
  with python extensions installed. If you set up WSL in 
  VS code, all you have to do is download the suggested
  extensions. 
- Dependent on C files guiClient.c

Usage:
- You can run this program on its own using >$ python3 Chat.py, 
  but it is designed to be run from LogIn.py. The main difference 
  is that LogIn.py allows you to input the username, port number, and IP.  
    - Otherwise, default username/port/ip is Sophia/9001/127.0.0.1
- You must have a server instance running on the same port for the 
  client to connect to 
- Remember to update LIBRARY_PATH
"""

#################### Import statements and constants ####################
import sys
import tkinter as tk
from tkinter import scrolledtext
import subprocess
from ctypes import *
import threading
import time
import datetime

DEFAULT_USER = "Sophia"
DEFAULT_PORT = 9001
DEFAULT_IP = "127.0.0.1"
LIBRARY_PATH = "/home/csci3160/stupid-discord/my_functions.so"

class Client(Structure):
    _fields_ = [
        ("exit_flag", c_int),
        ("socket_file_descriptor", c_int),
        ("client_name", c_char_p),
        ("received_message", c_char),
    ]

#################### Functions ####################
# compiles guiClient.c into library .so file 
def compile_library():
    compile_command = ["gcc", "-fPIC", "-shared", "guiClient.c", "-o", "my_functions.so"]
    subprocess.call(compile_command)
        
# def get_message():
#     message = entry.get()
#     if message:
#         # Send the message using the C library
#         my_functions.send_message(byref(client), message.encode())
#         # Display the message in the chat area
#         chat_area.insert(tk.END, f"You: {message}\n")
#         entry.delete(0, tk.END)  # Clear the entry field
        
def get_message(event=None):
    message = entry.get()
    if message:
        # Send the message using the C library
        my_functions.send_message(byref(client), message.encode())
        # Display the message in the chat area
        dt = datetime.datetime.now()
        dt_string = dt.strftime("%Y-%m-%d %H:%M")
        chat_area.insert(tk.END, f"{dt_string}  You: {message}\n")
        entry.delete(0, tk.END)  # Clear the entry field

def exit_chat():
    window.destroy() # kills the gui
    client.exit_flag = 1 # updates client state 
    my_functions.close_connection(byref(client))
    sys.exit(0)
    
#################### Begin execution ####################

# Read the values provided from LogIn.py 
# Username
if len(sys.argv) > 1:
    username = sys.argv[1]
else:
    username = DEFAULT_USER

# Port
if len(sys.argv) > 2:
    port = sys.argv[2]
else: 
    port = DEFAULT_PORT
    
# IP Address
if len(sys.argv) > 3:
    ip = sys.argv[3]
else: 
    ip = DEFAULT_IP
    
# Load the C library
so_file = LIBRARY_PATH
compile_library()
my_functions = CDLL(so_file)

# Initialize the client
client = Client()
my_functions.initialize_connection(byref(client), ip.encode(), int(port), username.encode())

#################### Receive messages ####################

# Set up to receive messages 
received_message = ""
receive_messages = my_functions.receive_messages
receive_messages.argtypes = [POINTER(Client)]
receive_messages.restype = c_char_p

def receive_messages_thread():
    global received_message  # Use the global variable to store the received message
    while not client.exit_flag:
        # Call the C function to receive a message
        received_message = receive_messages(byref(client)).decode("utf-8")
        # Check if there's a new message
        if received_message:
            # Update the chat area within the main GUI thread using the after method
            window.after(0, lambda: chat_area.insert(tk.END, f"{received_message}\n"))
        # Pause for a short duration to avoid high CPU usage
        time.sleep(0.1)

# Start the receive thread
receive_thread = threading.Thread(target=receive_messages_thread)
receive_thread.start()


#################### Receive messages ####################

#################### Main window -- GUI stuff ####################

# Main window
window = tk.Tk()
window.title("Stupid Discord")
window.geometry("650x600")
window.config(bg="#36393F")

# Left panel
left_frame = tk.Frame(window, width=175, height=590, bg="#2F3136")
left_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ns")

# Profile label
profile_label = tk.Label(left_frame, text="My Profile", fg="white", bg="#2F3136")
profile_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

# Tool bar frame
tool_bar = tk.Frame(left_frame, width=175, height=185, bd=1, relief="solid", bg="#2F3136")
tool_bar.grid(row=1, column=0, padx=5, pady=5, sticky="ns")

# Users online label
users_online = tk.Label(left_frame, text="Users Online", fg="white", bg="#2F3136")
users_online.grid(row=2, column=0, padx=5, pady=5, sticky="w")

# Users online frame
users_frame = tk.Frame(left_frame, width=175, height=250, bd=1, relief="solid", bg="#2F3136")
users_frame.grid(row=3, column=0, padx=5, pady=5, sticky="ns")

# Exit frame
exit_frame = tk.Frame(left_frame, width=175, height=50, bg="#2F3136")
exit_frame.grid(row=4, column=0, padx=5, pady=5, sticky="ns")

# Exit button
exit_button = tk.Button(exit_frame, text="Exit", command=exit_chat, width="15", bg="#7289DA", fg="white")
exit_button.pack(expand=True, fill=tk.BOTH)

# Right panel
right_frame = tk.Frame(window, width=350, height=590, bg="#2F3136")
right_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ns")

# Chat area frame
chat_frame = tk.Frame(right_frame, bg="#2F3136")
chat_frame.pack(padx=10, pady=10)

# Scrolled text widget for displaying messages
chat_area = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, width=40, height=30, bg="#36393F", fg="white")
chat_area.pack(padx=10, pady=10)

# Text input frame
input_frame = tk.Frame(right_frame, bg="#2F3136")
input_frame.pack(pady=5)

# Entry widget for entering messages
entry = tk.Entry(input_frame, width=30, bg="#36393F", fg="white")
entry.pack(side=tk.LEFT, padx=5)
entry.bind('<Return>', get_message)     # Bind Enter key to send messages

# Button to send messages
send_button = tk.Button(input_frame, text="Send", command=get_message, bg="#7289DA", fg="white")
send_button.pack(side=tk.LEFT, padx=5)

# Run the GUI
window.mainloop()
