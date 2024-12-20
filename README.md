# Chat Application - Documentation

## **1. Introduction**

This document provides a comprehensive overview of the Chat Application. It includes descriptions of how the program works, testing reports, bug lists, and sources of information consulted during development.

---

## **2. How the Program Works**

### **a) Overview**

The Chat Application is a client-server-based messaging system built in Python. It uses sockets for communication, threading for handling multiple clients, and a Tkinter GUI for the client interface.

### **b) Application Structure**

1. **Server:**

   - Manages client connections.
   - Handles incoming messages and broadcasts them to connected clients.
   - Logs all messages and events in a `chat_log.txt` file.

2. **Client:**

   - Connects to the server.
   - Provides a graphical interface for sending and receiving messages.
   - Allows users to execute chat commands like private messages, user list requests, and disconnections.

### **c) System Diagram**

```text
+------------+            +--------------+            +------------+
|  Client A  | <--------> |   Server     | <--------> |  Client B  |
+------------+            +--------------+            +------------+
```

### **d) Main Functions and Features**

- **Messaging:** Supports group chat, private messages, and all-chat mode.
- **User Management:** Allows listing and disconnecting users.
- **Error Handling:** Handles unexpected disconnections and command validation.
- **Data Persistence:** Saves chat history for future reference.

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
5. The server will start and listen for incoming connections.

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
5. The client GUI will open, allowing message exchange with other connected clients.

### **c) Supported Commands**

- **Sending a Private Message:**

  ```text
  /private <username> <message>
  ```
  Sends a private message to a specific user.

- **Sending a Message to All Users:**

  ```text
  /all <message>
  ```
  Sends a message visible to all connected users.

- **Listing All Users:**

  ```text
  /list
  ```
  Displays the list of currently connected users.

- **Viewing Chat History:**

  ```text
  /history
  ```
  Displays the saved chat history from previous sessions.

- **Disconnecting:**

  ```text
  /disconnect
  ```
  Disconnects the client from the server.

---

## **4. Test Reports and Bug Fixes**

### **a) Test Results Summary**

- **Test Environment:**
  - Python 3.x, Windows/Linux.
  - Libraries used: `unittest`, `socket`, `threading`, `tkinter`, `logging`.

### **b) Test Coverage**

- **Server Tests:**

  - Starting and stopping the server.
  - Handling multiple client connections.
  - Broadcasting messages correctly.
  - Logging events and messages.

- **Client Tests:**

  - Establishing connection to the server.
  - Sending and receiving messages.
  - Executing client-side commands (`/private`, `/list`, `/disconnect`, `/all`).

### **c) Found Bugs and Fixes**

| Bug Description                    | Status    | Solution                             |
| ---------------------------------- | --------- | ------------------------------------ |
| Clients not disconnecting properly | **Fixed** | Improved disconnection handling      |
| Incomplete private messages        | **Fixed** | Improved command parsing             |
| Logging failures on shutdown       | **Fixed** | Corrected log file closure           |
| Unresponsive UI during load        | **Fixed** | Added threading for background tasks |

---

## **5. Sources and Consultations**

- **Online Resources:**

  - [Python Documentation](https://docs.python.org/3/): Reference for core libraries.
  - [Real Python](https://realpython.com/): Tutorials on socket programming.
  - [Stack Overflow](https://stackoverflow.com/): Community support for troubleshooting.
  - [Wikipedia](https://www.wikipedia.org/): General technical and programming references.
  - ChatGPT: Assistance with README creation.

- **Educational Institution:**

  SPŠE Ječná: Hodiny PV - Support and project consultations with teachers and mentors.

---

Thank you for reviewing the Chat Application Documentation!

