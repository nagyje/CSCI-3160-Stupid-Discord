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
- Dependent on C files clientTest.c

Usage:
- You can run this program on its own using >$ python3 Chat.py, 
  but it is designed to be run from LogIn.py. The main difference 
  is that LogIn.py allows you to input the username.  
- You must have a server instance running on the same port for the 
  client to connect to 
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
LIBRARY_PATH = "/mnt/c/Users/Joe/csci3160/project1/my_functions.so"

class Client(Structure):
    _fields_ = [
        ("exit_flag", c_int),
        ("socket_file_descriptor", c_int),
        ("client_name", c_char_p),
        ("received_message", c_char),
    ]

#################### Functions ####################

# def connect_to_server_subprocess():
#     # Compile the C program
#     compile_command = ["gcc", "-Wall", "clientTest.c", "-o", "clientTest"]
#     subprocess.call(compile_command)
#     # Run the compiled program with port and username as arguments in the background
#     run_command = ["./clientTest", port, username]  # Replace "1234" and "YourUsername" with the desired port and username
#     subprocess.Popen(run_command)

def compile_library():
    compile_command = ["gcc", "-fPIC", "-shared", "clientTest.c", "-o", "my_functions.so"]
    subprocess.call(compile_command)
    
# not used right now 
def initialize_client():
    initialize_connection = my_functions.initialize_connection
    initialize_connection.argtypes = [POINTER(Client), c_char_p, c_int, c_char_p]
    initialize_connection.restype = c_int
    
    close_connection = my_functions.close_connection
    close_connection.argtypes = [POINTER(Client)]
    
    send_message = my_functions.send_message
    send_message.argtypes = [POINTER(Client), c_char_p]
    
    receive_messages = my_functions.receive_messages
    receive_messages.argtypes = [c_void_p]

# def get_message():
#     message = entry.get()
#     if message:
#         chat_area.insert(tk.END, f"You: {message}\n") #Display message
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

# to do: this doesn't work 
def exit_chat():
    window.destroy()
    client.exit_flag = 1
    my_functions.close_connection(byref(client))
    sys.exit(0)
    
#################### Begin execution ####################

# Read the values provided from LogIn.py 
if sys.argv[1]:
    username = sys.argv[1]

if sys.argv[2]:
    port = sys.argv[2]

if not port:
    port = DEFAULT_PORT

if not username:
    username = DEFAULT_USER
    
# Load the C library
so_file = LIBRARY_PATH
compile_library()
my_functions = CDLL(so_file)

# Initialize the client
client = Client()
my_functions.initialize_connection(byref(client), b"127.0.0.1", int(port), username.encode())

#################### Receive messages ####################

# # Set up to receive messages 
# received_message = ""
# receive_messages = my_functions.receive_messages
# receive_messages.argtypes = [POINTER(Client)]

# def receive_messages_thread():
#     while not client.exit_flag:
#         # Call the C function to receive a message
#         received_message = my_functions.receive_messages(byref(client)).decode("utf-8")
#         # Check if there's a new message
#         if client.received_message:
#             # Update the chat area within the main GUI thread using after method
#             window.after(0, lambda: chat_area.insert(tk.END, f"msg: {received_message}\n"))
#             # Clear the received_message buffer
#             client.received_message = None
#         # Pause for a short duration to avoid high CPU usage
#         time.sleep(0.1)

# # Start the receive thread
# receive_thread = threading.Thread(target=receive_messages_thread)
# receive_thread.start()

# Set up to receive messages 
received_message = ""
receive_messages = my_functions.receive_messages
receive_messages.argtypes = [POINTER(Client)]
receive_messages.restype = c_char_p  # Specify the return type as c_char_p

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

# Friends label
friends_label = tk.Label(left_frame, text="Friends Online", fg="white", bg="#2F3136")
friends_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")

# Friends frame
friends_frame = tk.Frame(left_frame, width=175, height=250, bd=1, relief="solid", bg="#2F3136")
friends_frame.grid(row=3, column=0, padx=5, pady=5, sticky="ns")

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
