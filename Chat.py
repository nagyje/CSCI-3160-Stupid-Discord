"""
Program Name: Chat.py
Author: Sophia Herrell
Contributors: 
Last Edited: 12/2/23
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

DEFAULT_USER = "Sophia"
DEFAULT_PORT = 9001
LIBRARY_PATH = "/home/csci3160/stupid-discord/my_functions.so"

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
        
def get_message():
    message = entry.get()
    if message:
        # Send the message using the C library
        my_functions.send_message(byref(client), message.encode())
        # Display the message in the chat area
        chat_area.insert(tk.END, f"You: {message}\n")
        entry.delete(0, tk.END)  # Clear the entry field

# to do: this doesn't work 
def exit_chat():
    window.destroy()
    client.exit_flag = 1
    my_functions.close_connection(byref(client))
    sys.exit(0)
    
#################### Begin execution ####################

# Check if a command-line argument (username) is provided
if len(sys.argv) > 1:
    username = sys.argv[1]
else:
    username = DEFAULT_USER

if len(sys.argv) > 2:
    port = sys.argv[2]
else: 
    port = DEFAULT_PORT
    
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

window = tk.Tk()
window.title("Stupid Discord")
window.geometry("605x600") # Default window size 
#window.config(bg="blue")

# bd=2, relief="solid"

#################### Left panel ####################

# Create frame to hold profile, chat members, exit button
left_frame = tk.Frame(window, width=175, height=590)
left_frame.grid(row=0, column=0, padx=10, pady=5)
#left_frame.config(bg="red")

# Create label for profile
profile_label = tk.Label(left_frame, text="My profile")
profile_label.grid(row=0, column=0, padx=5, pady=5)

# Create frame for profile
tool_bar = tk.Frame(left_frame, width=175, height=185, bd=1, relief="solid")
tool_bar.grid(row=1, column=0, padx=5, pady=5)

# Create label for friends online
friends_label = tk.Label(left_frame, text="Friends Online")
friends_label.grid(row=2, column=0, padx=5, pady=5)

# Create frame for friends online
friends_frame = tk.Frame(left_frame, width=175, height=250, bd=1, relief="solid")
friends_frame.grid(row=3, column=0, padx=5, pady=5)

# Create frame for exit button
exit_frame = tk.Frame(left_frame, width=175, height=50)
exit_frame.grid(row=4, column=0, padx=5, pady=5)

# Create exit button
exit_button = tk.Button(exit_frame, text="Exit", command=exit_chat, width="15")
exit_button.pack(expand=True, fill=tk.BOTH)

#################### Right panel ####################

# Create frame to hold chat window
right_frame = tk.Frame(window, width=350, height=590)
right_frame.grid(row=0, column=1, padx=10, pady=5)
#right_frame.config(bd=2, relief="solid")

#################### Chat area #################### 

# Create a frame to contain the chat area
chat_frame = tk.Frame(right_frame)
chat_frame.pack(padx=10, pady=10)
# Create a scrolled text widget for displaying messages
chat_area = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, width=40, height=30)
chat_area.pack(padx=10, pady=10)

#################### Text input ####################

# Create a frame to contain the entry and button widgets
input_frame = tk.Frame(right_frame)
input_frame.pack(pady=10)
# Create an entry widget for entering messages
entry = tk.Entry(input_frame, width=30)
entry.pack(side=tk.LEFT)
# Create a button to send messages
send_button = tk.Button(input_frame, text="Send", command=get_message)
send_button.pack(side=tk.LEFT, padx=5)

# Run the GUI
window.mainloop()