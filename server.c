#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <errno.h>

#define MAX_MESSAGE_LENGTH 1480
#define MAX_USERNAME_LENGTH 20

int exit_flag = 0;
int socket_file_descriptor = 0;

// I don't know how long of a user name to use
// but I think to use fgets you need to explicitly define a max name length
// so 20 is an arbitrary number
char client_name[MAX_USERNAME_LENGTH];

// I am pretty sure when you type on the console and enter, it terminates the string with
// an EOL char "\n" and I am fairly certain that Harrison explained that you needed to
// null terminate the string. This takes in a string and explicitly null terminates a string
// if it is EOL terminated.
void trim_string (char* arr, int length) {

	for (int i = 0; i < length; i++) 
	{
		if (arr[i] == '\n') 
		{
			arr[i] = '\0';
			return;
		}
	}
}

// This is the method that manages all the message receiving
// A thread is created with this method
void receive_manager() {
	int message_flag = 1;
	char message[MAX_MESSAGE_LENGTH] = {};
	
	while (message_flag) {
		
		int receive = recv(socket_file_descriptor, message, MAX_MESSAGE_LENGTH, 0);
		if (receive > 0) {
			printf("%s\n", message);
			fflush(stdout);
		} 
		else if (receive == 0) 
		{
			message_flag = 0;
		} 
		memset(message, 0, MAX_MESSAGE_LENGTH);
	}
}

// This is the method that manages all the message sending
// A thread is created with this method
void send_manager() {
	// I think this flag may be unneeded
	int message_flag = 1;
	char message[MAX_MESSAGE_LENGTH - MAX_USERNAME_LENGTH] = {};
	char message_and_name[MAX_MESSAGE_LENGTH] = {};

	while(message_flag) 
	{
		fflush(stdout);
		fgets(message, MAX_MESSAGE_LENGTH, stdin);
		trim_string(message, MAX_MESSAGE_LENGTH);

		if (strcmp(message, "exit") == 0) 
		{
			exit_flag = 1;
		}
		else if (strcmp(message, "users") == 0)
		{
			// Others commands could be made stringing other else/if blocks here
		}
		else 
		{
			sprintf(message_and_name, "%s: %s\n", client_name, message);
			send(socket_file_descriptor, message_and_name, strlen(message_and_name), 0);
		}

		// Clears both text buffers above.
		memset(message, 0, MAX_MESSAGE_LENGTH - MAX_USERNAME_LENGTH);
		memset(message_and_name, 0, MAX_MESSAGE_LENGTH);
	}
}

int main(int argc, char **argv){
	// Insert generic argument error here
	if(argc != 2){
		printf("Usage: %s <port>\n", argv[0]);
		return EXIT_FAILURE;
	}

	// port and address
	// I tried to set this up so that you could communicate across networks with port forwarding
	// But I don't know that you can with WSL
	char *ip = "68.57.127.194";
	int port = htons(atoi(argv[1]));

	printf("Please enter your name: ");
	fgets(client_name, MAX_USERNAME_LENGTH, stdin);
	trim_string(client_name, strlen(client_name));

	/* Socket settings */
	socket_file_descriptor = socket(AF_INET, SOCK_STREAM, 0);
	
	// Using sockaddr_in instead of getaddrinfo because it is easier to deal with
	// if you you have the data already that you want to use for the connection.
	// NOTE: I tried server_address->sin_family = AF_INET; and it fails,
	// I don't know the difference between -> and .
	struct sockaddr_in server_address;
	server_address.sin_family = AF_INET;
	server_address.sin_port = port;
	server_address.sin_addr.s_addr = inet_addr("68.57.127.194");


	// This tries to connect to a server with no error handling whatsoever
	if (connect(socket_file_descriptor, (struct sockaddr *)&server_address, sizeof(server_address)) == -1)
	{
		printf("Error in connect: %s\n", strerror(errno));
		return EXIT_FAILURE;
	}

	// sends client name to server, have no idea what this does if connect fails
	//printf("The connecting client is: %s", client_name); I don't know why this line is here
	send(socket_file_descriptor, client_name, MAX_USERNAME_LENGTH, 0);

	// Welcome Message
	printf("CSCI-3160 Stupid Discord: Connected as client\n");

	// Creates threads
	// Going pretty strong on the whole "No error handling" strategy
	pthread_t send_msg_thread;
	pthread_create(&send_msg_thread, NULL, (void *) send_manager, NULL);
	pthread_t recv_msg_thread;
	pthread_create(&recv_msg_thread, NULL, (void *) receive_manager, NULL) ;

	// This loops until something breaks or the exit flag is updated to keep the process running
	// The exit flag is currently intended to be updated by the user typing "exit"
	while (1){
		if(exit_flag)
		{
			printf("\nYou have disconnected from the chat\n");
			break;
		}
	}

	close(socket_file_descriptor);
	return EXIT_SUCCESS;
}
