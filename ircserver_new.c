/*
Program Name: 	server.c
Author: Jackson Denti
Contributors:
	Chris Bragg
	Chris Upham
	Joe Nagy
	Sophia Herrell
Created:		11/16/23
Last Edited: 	12/03/23
Description:	Creates an instance of a server that allows clients to connect if they know the port and Hosting Address. 
				Allows some light chatting. 

Additional Information:
- This program is designed to be run from a linux kernal. It has been tested on WSL on Windows 10, 11 and Ubuntu 22.04.3

Usage:
- 	./server PORT or ./server
	If no port number is specified, the default is 9001 
*/

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <pthread.h>
#include <sys/types.h>
#include <netdb.h>

/*
	Constants and global variables:
	MAX_CLIENTS defines the max number of clients that can be in a server at one time
	MAX_MESSAGE defines the longest a message can be, addtional characters are ignored
	MAX_NAME_LENGTH defines how long a user name can be, if it is too long right now,
		the extra characters are passed as a message and that is not intended behavior.
	client_count defines the number of clients currently connected,
		it is currently used to manage loops after switching from a linked list of
		clients to an array of clients
	user_id is to provide a unique number to identify the clients because if you try
		and identify them by their IP, you can run into issues over network with 
		multiple clients behind the same gateway
	pthread_mutex stuff is to be mutex stuff
*/
#define MAX_CLIENTS 10
#define MAX_MESSAGE 2000
#define MAX_NAME_LENGTH 20
static int client_count = 0;
static int user_id = 13;
pthread_mutex_t lock;
pthread_mutex_init(lock);

struct client_struct{
	struct sockaddr_in address;
	struct client_struct *next;
	struct client_struct *prev;
	
	int socket_file_descriptor;
	int user_id;
	char name[MAX_NAME_LENGTH];
};

struct client_struct *clients[MAX_CLIENTS];

// Don't know if this creates a lock the way it is supposed to
// But I have not ran into any errors with this to suggest otherwise


// Adds clients to client queue
// Method assumes enqueue is only called if max clients not reached
void enqueue_client(struct client_struct *client){
	pthread_mutex_lock(&lock);
	
	for(int i=0; i <= client_count; ++i)
	{
		if(!clients[i])
		{		
			clients[i] = client;
			client_count++;
			pthread_mutex_unlock(&lock);
			return;
		}
	}
}

// Tries to dequeue client, seg faults randomly for no good reason
// UPDATE: I tried to fix this. Now instead of randomly seg faulting, it ALWAYS seg faults
// NEW UPDATE: this does not segfault with new array code
// NEW NEW UPDATE: It segfaults again
void dequeue_client(int search_id){
	pthread_mutex_lock(&lock);
	
	for(int i=0; i < MAX_CLIENTS; ++i)
	{		
		if(clients[i]->user_id == search_id)
		{
			clients[i] = NULL;
			client_count--;
			pthread_mutex_unlock(&lock);
			return;
		}	
	}
}

// Manually null terminates string
void null_term_string (char* arr, int length) {
	for (int i = 0; i < length; i++) 
	{
		if (arr[i] == '\n') 
		{
			arr[i] = '\0';
			return;
		}
	}
}

// Send message to all clients except sender
void send_message(char *s, int sending_user_id){
	pthread_mutex_lock(&lock);

	for(int i=0; i<MAX_CLIENTS; ++i)
	{
		if(clients[i] && clients[i]->user_id != sending_user_id)
		{
			write(clients[i]->socket_file_descriptor, s, strlen(s));
		}
	}
	
	pthread_mutex_unlock(&lock);
}


// This is supposed to manage the sending and receiving for all clients connected
// This is what is threaded
void *manage_client(void *arg){
	char buffer[MAX_MESSAGE];
	char client_name[MAX_NAME_LENGTH];
	int leave_flag = 0;


	struct client_struct *client = (struct client_struct *)arg;

	// This is supposed to print the client name to the server and send it to all connected users
	// This worked at a point, but now it doesn't and I don't know why
	recv(client->socket_file_descriptor, client_name, MAX_NAME_LENGTH, 0);
	strcpy(client->name, client_name);
	
	// Updates buffer so it can be printed on the server end AND sent to all clients
	sprintf(buffer, "%s has joined this chat", client->name);
	printf("%s\n", buffer); // This is the line that prints to server, could be used for serverlogs
	send_message(buffer, client->user_id);
	memset(buffer, 0, MAX_MESSAGE);

	while(1)
	{
		// Loops until leave flag is updated


		// From recv man page: 
		// These calls return the number of bytes received, or -1 if an
		// error occurred. When a stream socket peer has performed an orderly shutdown, the
		// return value will be 0
		int receive = recv(client->socket_file_descriptor, buffer, MAX_MESSAGE, 0);
		
		// if any number of bytes was received
		if (receive > 0)
		{
			null_term_string(buffer, strlen(buffer));
			send_message(buffer, client->user_id);
			printf("%s\n", buffer);
		} 
		// If the user types "exit" or if the socket was shut down safely
		// I have no idea how the user would safely close the socket, but I threw
		// it in there as an exit condition
		else if (strcmp(buffer, "exit") == 0 || receive == 0)
		{
			sprintf(buffer, "%s has left this chat", client->name);
			printf("%s\n", buffer);
			//printf("User has left");
			send_message(buffer, client->user_id);
			break;
		}
		else if (strcmp(buffer, "test") == 0)
		{
			// I think you are supposed to be able to chain other server commands in here
		}
		else 
		{
			// Pretty sure this only hits if recv returns -1, meaning there was an error
			printf("%s errored out", client->name);
			break;
		}

		// Clear message buffer
		memset(buffer, 0, MAX_MESSAGE);
	}

	// close socket and free up memory
	close(client->socket_file_descriptor);
	dequeue_client(client->user_id);
	free(client);

	pthread_detach(pthread_self());

	return;
}

int main(int argc, char **argv){

	int connection_file_descriptor = 0;
	int	sfd, s;
	char buf[MAX_MESSAGE];
	char portnum[6];
	struct addrinfo          hints;
	struct addrinfo          *result, *rp;
	struct sockaddr_storage  peer_addr;
	struct sockaddr_in client_addr;
	socklen_t client_length;
	socklen_t peer_addrlen;
	pthread_t pid;

	if (argc > 1) {
		strncpy(portnum, argv[1], 5);
		portnum[5] = '\0';
	} else {
		strcpy(portnum, "9001");
	}

	memset(&hints, 0, sizeof(hints));
	hints.ai_family = AF_UNSPEC;    /* Allow IPv4 or IPv6 */
	hints.ai_socktype = SOCK_STREAM;/* TCP protocol socket */
	hints.ai_flags = AI_PASSIVE;    /* For wildcard IP address */
	hints.ai_protocol = IPPROTO_TCP;/* TCP */
	hints.ai_canonname = NULL;
	hints.ai_addr = NULL;
	hints.ai_next = NULL;

	s = getaddrinfo(NULL, portnum, &hints, &result);
	if (s != 0) {
		fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(s));
		exit(EXIT_FAILURE);
	}

	/* getaddrinfo() returns a list of address structures.
		 Try each address until we successfully bind(2).
		 If socket(2) (or bind(2)) fails, we (close the socket
		 and) try the next address. */

	for (rp = result; rp != NULL; rp = rp->ai_next) {
		sfd = socket(rp->ai_family, rp->ai_socktype,
				rp->ai_protocol);
		if (sfd == -1)
			continue;

		if (bind(sfd, rp->ai_addr, rp->ai_addrlen) == 0)
			break;                  /* Success */

		close(sfd);
	}

	freeaddrinfo(result);           /* No longer needed */

	if (rp == NULL) {               /* No address succeeded */
		fprintf(stderr, "Could not bind\n");
		exit(EXIT_FAILURE);
	}

	// Listen to the gorram socket
	if (listen(sfd, 1) < 0) {
		fprintf(stderr, "Error in listen\n");
		exit(EXIT_FAILURE);
	}
	
	printf("CSCI3160 Stupid Discord: Server\n");

	while(1)
	{
		client_length = sizeof(client_addr);
		connection_file_descriptor = accept(sfd, (struct sockaddr*)&client_addr, &client_length);

		// Client network set up
		struct client_struct *client = (struct client_struct *)malloc(sizeof(struct client_struct));
		client->address = client_addr;
		client->user_id = user_id++;
		client->socket_file_descriptor = connection_file_descriptor;

		// Add client to client queue and thread process
		enqueue_client(client);
		pthread_create(&pid, NULL, &manage_client, (void*)client);
	}

	return EXIT_SUCCESS;
}