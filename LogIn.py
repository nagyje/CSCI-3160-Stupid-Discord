/*
Program Name: guiClient.c
Author: Sophia Herrell
Contributors: Sophia Herrell, Jackson Denti
Last Edited: 12/5/23
Description: Client that connects to server. Modularized for 
             library import to Chat.py.

Additional Information:
- Based on client.c 

Usage:
- This program is compiled into my_functions.so by Chat.py
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pthread.h>

#define MAX_MESSAGE_LENGTH 1480
#define MAX_USERNAME_LENGTH 20

// Struct to hold client state
typedef struct {
    int exit_flag;
    int socket_file_descriptor;
    char client_name[MAX_USERNAME_LENGTH];
    char* received_message;
} Client;

void trim_string(char *arr, int length) {
    for (int i = 0; i < length; i++) {
        if (arr[i] == '\n') {
            arr[i] = '\0';
            return;
        }
    }
}

int initialize_connection(Client *client, char *ip, int port, char *username) {
    client->exit_flag = 0;

    strncpy(client->client_name, username, MAX_USERNAME_LENGTH - 1);
    client->client_name[MAX_USERNAME_LENGTH - 1] = '\0';

    client->socket_file_descriptor = socket(AF_INET, SOCK_STREAM, 0);
    if (client->socket_file_descriptor == -1) {
        perror("Error creating socket");
        return -1;
    }

    struct sockaddr_in server_address;
    server_address.sin_family = AF_INET;
    server_address.sin_port = htons(port);
    server_address.sin_addr.s_addr = inet_addr(ip);

    if (connect(client->socket_file_descriptor, (struct sockaddr *)&server_address, sizeof(server_address)) == -1) {
        perror("Error connecting to server");
        close(client->socket_file_descriptor);
        return -1;
    }

    if (send(client->socket_file_descriptor, client->client_name, MAX_USERNAME_LENGTH, 0) == -1) {
        perror("Error sending username to server");
        close(client->socket_file_descriptor);
        return -1;
    }

    printf("CSCI-3160 Stupid Discord: Connected as client\n");

    return 0;
}

void send_message(Client *client, char *message) {
    char message_and_name[MAX_MESSAGE_LENGTH];

    if (strcmp(message, "exit") == 0) {
        client->exit_flag = 1;
    } else if (strcmp(message, "users") == 0) {
        // Other commands could be handled here
    } else {
        sprintf(message_and_name, "%s: %s\n", client->client_name, message);
        send(client->socket_file_descriptor, message_and_name, strlen(message_and_name), 0);
    }
}

char* receive_messages(Client *client) {
    int message_flag = 1;
    char message[MAX_MESSAGE_LENGTH];

    while (message_flag) {
        int receive = recv(client->socket_file_descriptor, message, MAX_MESSAGE_LENGTH, 0);
        if (receive > 0) {
            // Allocate memory for the message
            char* received_message = (char*)malloc(receive + 1); // +1 for null terminator
            if (received_message == NULL) {
                perror("Error allocating memory for message");
                exit(EXIT_FAILURE); // Handle allocation failure
            }

            // Copy the received content into the allocated memory
            strncpy(received_message, message, receive);
            received_message[receive] = '\0'; // Null-terminate the string

            return received_message;
        } else if (receive == 0) {
            message_flag = 0;
        }
        memset(message, 0, MAX_MESSAGE_LENGTH);
    }

    // If no new message, return an empty string
    char *empty_string = (char *)malloc(1);
    if (empty_string == NULL) {
        perror("Error allocating memory for empty string");
        exit(EXIT_FAILURE); // Handle allocation failure
    }
    empty_string[0] = '\0';
    return empty_string;
}

void close_connection(Client *client) {
    close(client->socket_file_descriptor);
    exit(0);
}

void *send_manager(void *arg) {
    Client *client = (Client *)arg;
    int message_flag = 1;
    char message[MAX_MESSAGE_LENGTH - MAX_USERNAME_LENGTH];
    char message_and_name[MAX_MESSAGE_LENGTH];

    while (message_flag) {
        fflush(stdout);
        fgets(message, MAX_MESSAGE_LENGTH - MAX_USERNAME_LENGTH, stdin);
        trim_string(message, MAX_MESSAGE_LENGTH);

        if (strcmp(message, "exit") == 0) {
            client->exit_flag = 1;
        } else if (strcmp(message, "users") == 0) {
            // Others commands could be made stringing other else/if blocks here
        } else {
            sprintf(message_and_name, "%s: %s\n", client->client_name, message);
            send(client->socket_file_descriptor, message_and_name, strlen(message_and_name), 0);
        }
        memset(message, 0, MAX_MESSAGE_LENGTH - MAX_USERNAME_LENGTH);
        memset(message_and_name, 0, MAX_MESSAGE_LENGTH);
    }

    return NULL;
}

int main(int argc, char **argv) {
    if (argc != 3) {
        printf("Usage: %s <port> <username>\n", argv[0]);
        return EXIT_FAILURE;
    }

    char *ip = "127.0.0.1";
    int port = atoi(argv[1]);

    Client client;
    if (initialize_connection(&client, ip, port, argv[2]) != 0) {
        fprintf(stderr, "Connection initialization failed\n");
        return EXIT_FAILURE;
    }

    pthread_t send_msg_thread;
    pthread_create(&send_msg_thread, NULL, send_manager, (void *)&client);
	pthread_t recv_msg_thread;
    pthread_create(&recv_msg_thread, NULL, receive_messages, (void *)&client);

    while (1) {
        if (client.exit_flag) {
            printf("\nYou have disconnected from the chat\n");
            break;
        }
        sleep(0.05);
    }

    close_connection(&client);
    return EXIT_SUCCESS;
}
