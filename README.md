# Chat Application - Documentation

## **1. Introduction**

This document provides a comprehensive overview of the Chat Application. It includes descriptions of how the program works, testing reports, bug lists, and sources of information consulted during development.

---

## **2. How the Program Works**

### **a) Overview**

The Chat Application is a client-server-based messaging system built in Python. It uses sockets for communication and threading to handle multiple clients concurrently. The system supports both public and private messaging and includes server statistics tracking.

### **b) Application Structure**

1. **Server:**
   - Manages client connections and disconnections.
   - Handles incoming messages and broadcasts them to connected clients.
   - Tracks server uptime, total messages sent, and active users.
   - Logs all messages and events into a `chat_log.txt` file.

2. **Client:**
   - Connects to the server.
   - Provides a command-line interface for sending and receiving messages.
   - Allows users to execute various chat commands such as private messages, user list requests, and server statistics.

---

## **3. How to Use the Program**

### **a) Starting the Server**

1. Open a terminal.
2. Navigate to the project directory.
3. Run the following command:
   ```bash
   python Chat_app.py
   ```
4. When prompted, enter:
   ```
   Start as server (s) or client (c)? s
   ```
5. The server will start and listen for incoming connections on the configured port.

### **b) Starting the Client**

1. Open another terminal or machine.
2. Navigate to the project directory.
3. Run the following command:
   ```bash
   python Chat_app.py
   ```
4. When prompted, enter:
   ```
   Start as server (s) or client (c)? c
   ```
5. Follow the prompts to either log in or register.
6. Once connected, you can start sending messages or executing commands.

---

## **4. Supported Commands**

| **Command**                    | **Description**                                                                                                                                 |
|--------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| `/help`                        | Displays a list of all available commands.                                                                                                     |
| `/list`                        | Lists all currently connected users.                                                                                                           |
| `/private <username> <message>`| Sends a private message to a specific user.                                                                                                    |
| `/stats`                       | Displays server statistics, including active users, total messages sent, and server uptime.                                                    |
| `/quit`                        | Disconnects the client from the server.                                                                                                        |

---

## **5. Features and Updates**

### **a) Key Features**

- **Real-Time Messaging:** Supports both group chat and private messaging.
- **User Management:** Allows clients to log in, register, and view connected users.
- **Server Statistics:** Tracks active users, total messages sent, and uptime, available via the `/stats` command.
- **Command Parsing:** Handles various commands seamlessly using structured message parsing.
- **Logging:** All events, messages, and errors are logged in `chat_log.txt`.

### **b) Recent Updates**
- Added `/stats` command for server statistics.
- Enhanced error handling for invalid or malformed commands.
- Improved logging to track `/help`, `/list`, and `/private` commands.
- Fixed issues with user disconnections and message handling.

---

## **6. Test Reports and Bug Fixes**

### **a) Test Results Summary**

- **Environment:**
  - Python 3.x, tested on Windows/Linux.
  - Libraries: `unittest`, `socket`, `threading`, `logging`.

### **b) Test Coverage**

| **Component** | **Tested Functions**                                        |
|---------------|-------------------------------------------------------------|
| **Server**    | Startup, client connection handling, broadcast, statistics. |
| **Client**    | Message sending, command handling, disconnection.           |
| **Commands**  | `/help`, `/list`, `/private`, `/stats`, `/quit`.            |

### **c) Found Bugs and Fixes**

| Bug Description                     | Status     | Solution                        |
|-------------------------------------|------------|---------------------------------|
| Double username prompt on `/list`  | **Fixed**  | Updated list command handler.  |
| Messages not appearing immediately | **Fixed**  | Implemented threading fixes.   |
| Server stats incorrect uptime       | **Fixed**  | Corrected time calculations.   |
| Double username on use of command    | **Broken**  | |

---

## **7. Sources and Consultations**

- **Online Resources:**
  - [Python Documentation](https://docs.python.org/3/): Reference for core libraries.
  - [Real Python](https://realpython.com/): Tutorials on socket programming.
  - [Stack Overflow](https://stackoverflow.com/): Community support for troubleshooting.
  - ChatGPT: Assistance with command and feature implementation.

- **Educational Institution:**
  - SPŠE Ječná: Hodiny PV.


