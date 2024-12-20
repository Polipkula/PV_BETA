import socket
import threading
import logging
import json
import hashlib
import time
from datetime import timedelta

# Načtení konfiguračního souboru
config_file = "config.json"
users_file = "users.json"

# Třída pro načtení konfigurace serveru
class ConfigLoader:
    @staticmethod
    def load_config():
        """
        Načte konfiguraci serveru z JSON souboru.
        Pokud soubor neexistuje, vytvoří výchozí konfiguraci.
        """
        try:
            with open(config_file, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            default_config = {"HOST": "127.0.0.1", "PORT": 12345}
            with open(config_file, 'w') as file:
                json.dump(default_config, file, indent=4)
            return default_config

# Třída pro správu uživatelů
class UserManager:
    @staticmethod
    def load_users():
        """
        Načte seznam uživatelů z JSON souboru.
        Pokud soubor neexistuje, vytvoří prázdný seznam.
        """
        try:
            with open(users_file, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            with open(users_file, 'w') as file:
                json.dump({}, file, indent=4)
            return {}

    @staticmethod
    def save_user(username, password):
        """
        Uloží nového uživatele s heslem do seznamu uživatelů.
        Heslo je ukládáno jako SHA-256 hash.
        """
        users = UserManager.load_users()
        if username in users:
            return False
        users[username] = hashlib.sha256(password.encode()).hexdigest()
        with open(users_file, 'w') as file:
            json.dump(users, file, indent=4)
        return True

    @staticmethod
    def authenticate(username, password):
        """
        Ověří uživatele podle jeho jména a hesla.
        """
        users = UserManager.load_users()
        return users.get(username) == hashlib.sha256(password.encode()).hexdigest()

# Třída pro implementaci serveru
class ChatServer:
    def __init__(self, host, port):
        """
        Inicializace serveru.
        """
        self.host = host
        self.port = port
        self.clients = {}  # Slovník připojených klientů
        self.message_count = 0  # Počet přijatých zpráv
        self.start_time = time.time()  # Čas spuštění serveru
        logging.basicConfig(filename="chat_log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

    def log_message(self, msg):
        """
        Zaloguje zprávu do souboru a vypíše ji do konzole.
        """
        logging.info(msg)
        print(msg)

    def start(self):
        """
        Spustí server a čeká na připojení klientů.
        """
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen()
        self.log_message(f"[SERVER STARTED] Listening on {self.host}:{self.port}")

        while True:
            conn, addr = server.accept()  # Přijetí klienta
            self.log_message(f"[CONNECTION] Client connected from {addr}")
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            thread.start()
            self.log_message(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

    def handle_client(self, conn, addr):
        """
        Obsluhuje připojeného klienta.
        """
        try:
            username = conn.recv(1024).decode('utf-8').strip()
            self.log_message(f"[NEW CONNECTION] {username} ({addr}) connected.")
            self.clients[conn] = username
            self.broadcast(f"[SERVER] {username} has joined the chat.", conn)

            while True:
                msg = conn.recv(1024).decode('utf-8')
                if not msg:
                    break

                # Příkazy
                if msg.startswith("/help"):
                    help_message = (
                        "/help - Show this help message\n"
                        "/list - List all connected users\n"
                        "/private <username> <message> - Send a private message\n"
                        "/stats - Show server statistics"
                    )
                    conn.send(f"[SERVER] Commands:\n{help_message}\n".encode('utf-8'))
                    self.log_message(f"[HELP] Command issued by {username}")

                elif msg.startswith("/list"):
                    user_list = "[SERVER] Connected users:\n" + '\n'.join(self.clients.values())
                    conn.send(f"{user_list}\n".encode('utf-8'))
                    self.log_message(f"[LIST] Command issued by {username}")

                elif msg.startswith("/private"):
                    parts = msg.split(' ', 2)
                    if len(parts) < 3:
                        conn.send("[SERVER] Invalid format. Use /private <username> <message>\n".encode('utf-8'))
                        continue

                    target_username, private_message = parts[1], parts[2]
                    target_conn = next((c for c, u in self.clients.items() if u == target_username), None)
                    if target_conn:
                        target_conn.send(f"[PRIVATE] {username}: {private_message}\n".encode('utf-8'))
                        conn.send(f"[PRIVATE] To {target_username}: {private_message}\n".encode('utf-8'))
                        self.log_message(f"[PRIVATE] {username} to {target_username}: {private_message}")
                    else:
                        conn.send("[SERVER] User not found.\n".encode('utf-8'))

                elif msg.startswith("/stats"):
                    self.send_stats(conn, username)

                else:
                    self.log_message(f"[MESSAGE] {username}: {msg}")
                    self.broadcast(f"{username}: {msg}", conn)
                    self.message_count += 1

        except ConnectionResetError:
            self.log_message(f"[DISCONNECTED] {addr} forcibly closed the connection.")
        except Exception as e:
            self.log_message(f"[ERROR] {addr}: {e}")
        finally:
            conn.close()
            if conn in self.clients:
                username = self.clients.pop(conn)
                self.broadcast(f"[SERVER] {username} has left the chat.", conn)
                self.log_message(f"[DISCONNECTED] {username} ({addr}) disconnected.")

    def send_stats(self, conn, username):
        """
        Odešle statistiky serveru uživateli.
        """
        uptime = str(timedelta(seconds=int(time.time() - self.start_time)))
        stats_message = (
            f"[SERVER STATS]\n"
            f"Active users: {len(self.clients)}\n"
            f"Total messages: {self.message_count}\n"
            f"Uptime: {uptime}"
        )
        conn.send(stats_message.encode('utf-8'))
        self.log_message(f"[STATS] Command issued by {username}:\n{stats_message}")

    def broadcast(self, msg, sender=None):
        """
        Odešle zprávu všem připojeným uživatelům kromě odesílatele.
        """
        for client in list(self.clients):
            if client != sender:
                try:
                    client.send(msg.encode('utf-8'))
                except Exception as e:
                    self.log_message(f"[ERROR] Sending message: {e}")

# Třída pro klienta
class ChatClient:
    def __init__(self, host, port):
        """
        Inicializace klienta.
        """
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = None
        try:
            self.client.connect((host, port))
            print(f"[CONNECTED] to {host}:{port}")
        except Exception as e:
            print(f"[ERROR] Could not connect to server: {e}")

    def register(self):
        """
        Registrace nového uživatele.
        """
        username = input("Choose a username: ")
        password = input("Choose a password: ")
        if UserManager.save_user(username, password):
            print("Registration successful! You can now log in.")
        else:
            print("Username already exists! Try again.")
        self.start_client()

    def login(self):
        """
        Přihlášení uživatele.
        """
        while True:
            username = input("Enter your username: ")
            password = input("Enter your password: ")
            if UserManager.authenticate(username, password):
                print(f"Login successful!")
                self.username = username
                self.client.send(username.encode('utf-8'))
                break
            else:
                print("Invalid username or password! Try again.")

    def start_client(self):
        """
        Spuštění klienta.
        """
        while True:
            choice = input("Do you want to (R)egister or (L)ogin? ").strip().lower()
            if choice == 'r':
                self.register()
            elif choice == 'l':
                self.login()
                self.chat()
                break

    def chat(self):
        """
        Hlavní smyčka pro komunikaci uživatele.
        """
        print(f"Welcome to the chat, {self.username}! Type your messages below:")
        threading.Thread(target=self.receive_messages, daemon=True).start()
        while True:
            msg = input(f"{self.username}: ")
            if msg.lower() == '/quit':
                print("You have left the chat.")
                self.client.close()
                break
            try:
                self.client.send(msg.encode('utf-8'))
            except Exception as e:
                print(f"[ERROR] Could not send message: {e}")
                break

    def receive_messages(self):
        """
        Přijímá zprávy od serveru a zobrazuje je.
        """
        while True:
            try:
                msg = self.client.recv(1024).decode('utf-8')
                if msg:
                    print(f"\r{msg}\n{self.username}: ", end="")
            except Exception as e:
                print(f"[ERROR] Receiving message: {e}")
                break

if __name__ == "__main__":
    # Načtení konfigurace a spuštění serveru nebo klienta
    config = ConfigLoader.load_config()
    choice = input("Start as server (s) or client (c)? ").strip().lower()
    if choice == 's':
        server = ChatServer(config["HOST"], config["PORT"])
        server.start()
    elif choice == 'c':
        client = ChatClient(config["HOST"], config["PORT"])
        client.start_client()
