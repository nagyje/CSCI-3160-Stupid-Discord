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

#define MAX_CLIENTS 10

// Max message is longer for server so that server information could be appended without issues
// for logging purposes
#define MAX_MESSAGE 2000

static int client_count = 0;
static int user_id = 10;


struct client_struct{
	struct sockaddr_in address;
	struct client_struct *next;
	struct client_struct *prev;
	
	int socket_file_descriptor;
	int user_id;
	char name[32];
};

struct queue {
	struct client_struct *head;
	struct client_struct *tail;
	unsigned int count;
};

// I spent endless hours trying to get all the linked list stuff to work
// I found someone on stackoverflow doing something similar to this project
// But they used an array of structs, I don't know if this causes any
// unintended issues, but it makes the code a lot cleaner and does not segfault
// Please let me know in the comments if this array is a bad idea
struct queue *client_queue;
struct client_struct *clients[MAX_CLIENTS];

// Don't know if this creates a lock the way it is supposed to
// But I have not ran into any errors with this to suggest otherwise
pthread_mutex_t lock;
pthread_mutex_init(lock);

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

// Adds clients to client queue
// Method assumes enqueue is only called if max clients not reached
void enqueue_client(struct client_struct *client){
	pthread_mutex_lock(&lock);
	
	/* Old Linked List code
	client->prev = client_queue->tail;
	client->next = NULL;
	client_queue->tail = client;
	client_queue->count++;
	*/
	
	// newer sexier array based code
	for(int i=0; i <= client_count; ++i)
	{
		if(!clients[i])
		{		
			clients[i] = client;
			pthread_mutex_unlock(&lock);
			return;
		}
	}
			
}

// Tries to dequeue client, seg fualts randomly for no good reason
// UPDATE: I tried to fix this. Now instead of randomly seg faulting, it ALWAYS seg faults
// NEW UPDATE: this does not segfault with new array code
// NEW NEW
void dequeue_client(int search_id){
	pthread_mutex_lock(&lock);
	
	/* Old Linked List code
	struct client_struct *client_node = (struct client_struct*)malloc(sizeof(struct client_struct));
	client_node = client_queue->head;
	if(client_queue->head->user_id == search_id)
	{
		// This is supposed to dequeue a client if they are the head of the linked list
		client_queue->head = client_queue->head->next;
		client_queue->head->prev = NULL;	
		
		free(client_node);
		pthread_mutex_unlock(&lock);
		return;
	}
	else if (client_queue->tail->user_id == search_id)
	{
		// This is supposed to dequeue a client if they are the tail of the linked list
		client_node = client_queue->tail;
		client_queue->tail = client_queue->tail->prev;
		
		free(client_node);
		pthread_mutex_unlock(&lock);
		return;
	}
	
	for(int i = 0; i < MAX_CLIENTS; i++)
	{
		// This assumes the user is somewhere in the middle.
		// It checks each user and once it finds them, it removes them
		
		if (client_node->user_id == search_id)
		{
			client_node->prev->next = client_node->next;
			client_node->next->prev = client_node->prev;
			
			free(client_node);
			//free(q->queue->head);
			
			pthread_mutex_unlock(&lock);
			return;
		}
		client_node = client_node->next;
	}
	*/
	
	// It's clean, it's sheek. Arrays
	for(int i=0; i < MAX_CLIENTS; ++i)
	{		
		if(clients[i]->user_id == search_id)
		{
			clients[i] = NULL;
			pthread_mutex_unlock(&lock);
			return;
		}	
	}
}

/* Send message to all clients except sender */
void send_message(char *s, int sending_user_id){
	pthread_mutex_lock(&lock);

	
	// This also segfaults, maybe a doubly linked list is not the way to go about this
	// This was also the last straw before I tried to use an array
	/*
	struct client_struct *client_node = (struct client_struct*)malloc(sizeof(struct client_struct));
	client_node = client_queue->head;
	for(int i=0; i < client_count -1; ++i)
	{
		if(client_node->user_id != sending_user_id)
		{
			write(client_node->socket_file_descriptor, s, strlen(s));
		}
		client_node = client_node->next;
	}*/
	
	// Newer array code, I don't know if leveraging max clients instead of client count is better or worse
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
void *handle_client(void *arg){
	char buffer[MAX_MESSAGE];
	char client_name[32];
	int leave_flag = 0;

	client_count++;
	struct client_struct *client = (struct client_struct *)arg;

	// This is supposed to print the client name to the server and send it to all connected users
	// This worked at a point, but now it doesn't and I don't know why
	recv(client->socket_file_descriptor, client_name, 32, 0);
	strcpy(client->name, client_name);
	
	// Updates buffer so it can be printed on the server end AND sent to all clients
	sprintf(buffer, "%s has joined this chat\n", client->name);
	printf("%s", buffer); // This is the line that prints to server, could be used for serverlogs
	send_message(buffer, client->user_id);
	memset(buffer, 0, MAX_MESSAGE);

	// BUG: some of the text is not formatted correctly, inbound message and outbound message are ending up in the same line.
	// BUG: we need some \n somewhere, I just don't know where
	while(1)
	{
		// Loops until leave flag is updated
		if (leave_flag) 
		{
			break;
		}

		// From recv man page: 
		// These calls return the number of bytes received, or -1 if an
		// error occurred. When a stream socket peer has performed an orderly shutdown, the
		// return value will be 0
		int receive = recv(client->socket_file_descriptor, buffer, MAX_MESSAGE, 0);
		
		// if any number of bytes was received
		if (receive > 0)
		{
			trim_string(buffer, strlen(buffer));
			send_message(buffer, client->user_id);
			printf("%s\n", buffer);
		} 
		// If the user types "exit" or if the socket was shut down safely
		// I have no idea how the user would safely close the socket, but I threw
		// it in there as an exit condition
		else if (strcmp(buffer, "exit") == 0 || receive == 0)
		{
			sprintf(buffer, "%s has left this chat", client->name);
			printf("%s", buffer);
			send_message(buffer, client->user_id);
			leave_flag = 1;
		}
		else if (strcmp(buffer, "test") == 0)
		{
			// I think you are supposed to be able to chain other server commands in here
			// This did not remotely work when I tested
			//send_message("\nTHIS IS A TEST\n", client->user_id);
		}
		else 
		{
			// Pretty sure this only hits if recv returns -1, meaning there was an error
			printf("%s errored out", client->name);
			leave_flag = 1;
		}

		// Clear message buffer
		memset(buffer, 0, MAX_MESSAGE);
	}

	// close socket and free up memory
	close(client->socket_file_descriptor);
	dequeue_client(client->user_id);
	free(client);
	client_count--;
	pthread_detach(pthread_self());

	return;
}

int main(int argc, char **argv){
	if(argc != 2)
	{
		printf("Usage: %s <port>\n", argv[0]);
		return EXIT_FAILURE;
	}

	// I tried using Harrison's little bit of port code here and it explodes
	// sockaddr_in needs to port as a specific datatype
	int port = atoi(argv[1]);
	int listenfd = 0, connection_file_descriptor = 0;
	struct sockaddr_in client_addr;
	pthread_t pid;
	client_queue = (struct queue*)malloc(sizeof(struct queue));

	// Listen Socket
	listenfd = socket(AF_INET, SOCK_STREAM, 0);
  
	// Using sockaddr_in instead of getaddrinfo because it is easier to deal with
	// if you you have the data already that you want to use for the connection.
	// NOTE: I tried server_address->sin_family = AF_INET; and it fails,
	// I don't know the difference between -> and .
	struct sockaddr_in server_address;
	server_address.sin_family = AF_INET;
	server_address.sin_port = htons(port); // I don't understand what htons is, but stackoverflows as I need it instead of just atoi
	server_address.sin_addr.s_addr = inet_addr("127.0.0.1");
	

	// Bind Socket and address
	if(bind(listenfd, (struct sockaddr*)&server_address, sizeof(server_address)) < 0) 
	{
		fprintf(stderr, "Error in bind\n");
		exit(EXIT_FAILURE);
	}
	/* Listen to the gorram socket */
	// Don't know what this does, stole it from Harrison.
	if (listen(listenfd, 1) < 0) 
	{
		fprintf(stderr, "Error in listen\n");
		exit(EXIT_FAILURE);
	}
	// connection succeeded?
	printf("CSCI3160 Stupid Discord: Server\n");

	while(1)
	{
		socklen_t client_length = sizeof(client_addr);
		connection_file_descriptor = accept(listenfd, (struct sockaddr*)&client_addr, &client_length);

		// Client network set up
		struct client_struct *client = (struct client_struct *)malloc(sizeof(struct client_struct));
		client->address = client_addr;
		client->user_id = user_id++;
		client->socket_file_descriptor = connection_file_descriptor;

		// Add client to client queue and thread process
		enqueue_client(client);
		pthread_create(&pid, NULL, &handle_client, (void*)client);
	}

	return EXIT_SUCCESS;
}
