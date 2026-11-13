"""
Twitch Chat Logger - BACKEND.

Files (keep them in the same folder):
    twitch_chat_logger.py   <- this file: Twitch connection + Start/Stop + .txt dump
    index.html              <- the frontend: buttons + text box

Run:   python twitch_chat_logger.py
Open:  http://localhost:8000

Routes the frontend talks to:
    GET  /         -> serves index.html
    GET  /status   -> {"channel", "listening", "connected", "count"}
    POST /start    -> {"status": "..."}
    POST /stop     -> {"status": "..."}

Start -> read_chat = True: connects to the stream's chat and collects
         every message while `while read_chat:` keeps looping
Stop  -> read_chat = False: the loop ends, we disconnect, and every
         message from the start-stop window is dumped into a .txt file

Reads chat anonymously (read-only), so no Twitch account, API keys,
or ngrok needed. Only the Python standard library (Python 3.7+).
"""

import json
import random
import socket
import ssl
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# ======================= SETTINGS YOU CAN CHANGE =======================

# The stream whose chat we listen to - the name in twitch.tv/<name>
TWITCH_USERNAME = "your_channel_here"

# Where the .txt dumps go (default: the same folder as this script).
OUTPUT_FOLDER = Path(__file__).resolve().parent

# The frontend page (keep index.html in the same folder as this script).
FRONTEND_FILE = Path(__file__).resolve().parent / "index.html"

PORT = 8000

# =======================================================================

TWITCH_HOST = "irc.chat.twitch.tv"
TWITCH_PORT = 6697                 # secure (TLS) chat connection

read_chat = False          # the flag the Start/Stop buttons flip
connected = False          # True once we've actually joined the chat
chat_messages = []         # messages collected in the current start-stop window
start_time = None
listener_thread = None
lock = threading.Lock()


# --------------------------- Twitch chat reading ---------------------------

def connect():
    """Open a secure connection to Twitch chat."""
    raw = socket.create_connection((TWITCH_HOST, TWITCH_PORT), timeout=10)
    return ssl.create_default_context().wrap_socket(raw, server_hostname=TWITCH_HOST)


def parse_chat_line(line):
    """Turn a raw Twitch chat line into 'HH:MM:SS name: message' (or None)."""
    tags = {}
    if line.startswith("@"):                       # extra info Twitch adds (display name, time...)
        raw_tags, line = line[1:].split(" ", 1)
        for tag in raw_tags.split(";"):
            key, _, value = tag.partition("=")
            tags[key] = value

    if " PRIVMSG " not in line:                    # PRIVMSG = an actual chat message
        return None
    prefix, rest = line.split(" PRIVMSG ", 1)
    text = rest.partition(" :")[2]
    name = tags.get("display-name") or prefix.lstrip(":").split("!")[0]

    try:
        sent = datetime.fromtimestamp(int(tags["tmi-sent-ts"]) / 1000)
    except (KeyError, ValueError):
        sent = datetime.now()

    if text.startswith("\x01ACTION ") and text.endswith("\x01"):   # /me messages
        return f"{sent:%H:%M:%S} * {name} {text[8:-1]}"
    return f"{sent:%H:%M:%S} {name}: {text}"


def listen_to_twitch_chat():
    """Runs in the background. Keeps reading chat while read_chat is True."""
    global connected
    channel = "#" + TWITCH_USERNAME.strip().lower().lstrip("#")

    while read_chat:                               # outer loop: (re)connect if dropped
        try:
            sock = connect()
            sock.sendall(b"CAP REQ :twitch.tv/tags twitch.tv/commands\r\n")
            sock.sendall(b"PASS anonymous\r\n")
            sock.sendall(f"NICK justinfan{random.randint(10000, 99999)}\r\n".encode())
            sock.sendall(f"JOIN {channel}\r\n".encode())
            sock.settimeout(1)                     # wake up every second to check read_chat
            buffer = ""

            while read_chat:                       # inner loop: read messages
                try:
                    data = sock.recv(4096)
                except socket.timeout:
                    continue
                if not data:
                    raise ConnectionError("Twitch closed the connection")
                buffer += data.decode("utf-8", errors="replace")
                *lines, buffer = buffer.split("\r\n")

                for line in lines:
                    if line.startswith("PING"):    # Twitch checks we're still here
                        sock.sendall(line.replace("PING", "PONG", 1).encode() + b"\r\n")
                    elif " ROOMSTATE " in line and not connected:
                        connected = True
                        print(f"[joined] {channel}")
                    elif " RECONNECT" in line:
                        raise ConnectionError("Twitch asked us to reconnect")
                    else:
                        message = parse_chat_line(line)
                        if message:
                            with lock:
                                if read_chat:
                                    chat_messages.append(message)
                            print("[chat]", message)

            sock.close()
        except (OSError, ConnectionError) as error:
            connected = False
            if read_chat:
                print(f"[disconnected] {error} - retrying in 3s")
                time.sleep(3)

    connected = False
    print("[stopped listening]")


# --------------------------- Start / Stop logic ---------------------------

def save_chat_log(messages, start, end):
    name = TWITCH_USERNAME.strip().lower().lstrip("#")
    path = OUTPUT_FOLDER / f"twitch_chat_{name}_{start:%Y-%m-%d_%H-%M-%S}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Twitch chat log - twitch.tv/{name}\n")
        f.write(f"Started: {start:%Y-%m-%d %H:%M:%S}\n")
        f.write(f"Stopped: {end:%Y-%m-%d %H:%M:%S}\n")
        f.write(f"Messages: {len(messages)}\n")
        f.write("=" * 40 + "\n\n")
        for line in messages:
            f.write(line + "\n")
    return path


def start_listening():
    global read_chat, chat_messages, start_time, listener_thread
    with lock:
        if read_chat:
            return "Already listening."
        if not TWITCH_USERNAME.strip() or TWITCH_USERNAME == "your_channel_here":
            return "Set TWITCH_USERNAME at the top of the script first."
        start_time = datetime.now()
        chat_messages = []
        read_chat = True
        listener_thread = threading.Thread(target=listen_to_twitch_chat, daemon=True)
        listener_thread.start()
    return f"Listening to twitch.tv/{TWITCH_USERNAME} since {start_time:%H:%M:%S}..."


def stop_listening():
    global read_chat
    with lock:
        if not read_chat:
            return "Not listening - press Start first."
        read_chat = False
    listener_thread.join()               # wait for the loop to finish (about 1 second)
    end_time = datetime.now()
    with lock:
        messages = list(chat_messages)
    path = save_chat_log(messages, start_time, end_time)
    print(f"[saved] {len(messages)} messages to {path}")
    return f"Stopped. Saved {len(messages)} messages to {path.name}"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            # Re-read every time, so edits to index.html show up on refresh
            self.respond(200, FRONTEND_FILE.read_text(encoding="utf-8"), "text/html")
        elif self.path == "/status":
            with lock:
                status = {"channel": TWITCH_USERNAME, "listening": read_chat,
                          "connected": connected, "count": len(chat_messages)}
            self.respond(200, json.dumps(status), "application/json")
        else:
            self.respond(404, "Not found", "text/plain")

    def do_POST(self):
        if self.path == "/start":
            status = start_listening()
        elif self.path == "/stop":
            status = stop_listening()
        else:
            return self.respond(404, "Not found", "text/plain")
        self.respond(200, json.dumps({"status": status}), "application/json")

    def respond(self, code, body, content_type):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass  # keep the terminal quiet


if __name__ == "__main__":
    if not FRONTEND_FILE.exists():
        raise SystemExit(f"Can't find {FRONTEND_FILE} - put index.html next to this script.")
    print(f"Listening target: twitch.tv/{TWITCH_USERNAME}")
    print(f"Open http://localhost:{PORT} in your browser (Ctrl+C to quit)")
    ThreadingHTTPServer(("localhost", PORT), Handler).serve_forever()
