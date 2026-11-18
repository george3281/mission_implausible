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
    POST /paste    -> {"status", "cards", "error"}   backup: pasted chat -> AI

Start -> read_chat = True: connects to the stream's chat and collects
         every message while `while read_chat:` keeps looping
Stop  -> read_chat = False: the loop ends, we disconnect, and every
         message from the start-stop window is dumped into a .txt file

Reads chat anonymously (read-only), so no Twitch account, API keys,
or ngrok needed. Only the Python standard library (Python 3.7+).
"""

import json
import os
import random
import re
import socket
import ssl
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from selector import select_cards      # the AI step (needs GEMINI_API_KEY, or MOCK=1 to test)

# ======================= SETTINGS YOU CAN CHANGE =======================

# The stream whose chat we listen to - the name in twitch.tv/<name>
TWITCH_USERNAME = "emiru"  # change this to the channel you want to log

# Where the .txt dumps go (default: the same folder as this script).
OUTPUT_FOLDER = Path(__file__).resolve().parent

# The frontend page (keep index.html in the same folder as this script).
FRONTEND_FILE = Path(__file__).resolve().parent / "index.html"

PORT = 8000

# MOCK=1 python twitch_chat_logger.py  -> fake AI, no API key needed (for testing the page)
USE_MOCK = os.environ.get("MOCK") == "1"

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


# ------------------------ Turning chat into AI input ------------------------

LINE = re.compile(r"^\d\d:\d\d:\d\d (.+?): (.*)$")

def to_ai_lines(messages):
    """'HH:MM:SS name: message'  ->  'name: message'. Skips /me action lines."""
    out = []
    for line in messages:
        if re.match(r"^\d\d:\d\d:\d\d \* ", line):
            continue
        m = LINE.match(line)
        if m and m.group(2).strip():
            out.append(f"{m.group(1)}: {m.group(2).strip()}")
    return out


# ------------------------ Backup: pasted chat ------------------------
# If the Twitch connection breaks during the show, someone copies the chat
# from Twitch, pastes it into the box on the page, and it goes to the AI
# the same way a normal round does. Also handy for testing with fake chat.

MAX_PASTED_LINES = 500                     # keep only the most recent lines
PASTE_TIME = re.compile(r"^\[?\d{1,2}:\d{2}(:\d{2})?\s*([AaPp][Mm])?\]?\s+")
PASTE_NAME = re.compile(r"^(\S{1,25}?)\s*:\s+(.+)$")
LOG_HEADER = re.compile(r"^(Twitch chat log - |Started: |Stopped: |Messages: |Pasted chat - |=+$)")


def parse_pasted_chat(text):
    """Turn messy pasted chat into 'name: message' lines.

    Handles timestamps ('12:34', '12:34:56', '[3:05 PM]'), our own saved .txt
    logs, '/me' lines ('* name waves'), and lines with no name at all
    (those become 'pasted: message').
    """
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or LOG_HEADER.match(line):
            continue
        line = PASTE_TIME.sub("", line)
        if line.startswith("* "):                  # /me line from our own logs
            name, _, msg = line[2:].partition(" ")
            if msg.strip():
                out.append(f"{name}: {msg.strip()}")
            continue
        m = PASTE_NAME.match(line)
        if m:
            out.append(f"{m.group(1)}: {m.group(2).strip()}")
        else:
            out.append(f"pasted: {line}")
    return out[-MAX_PASTED_LINES:]


def save_pasted_log(lines):
    path = OUTPUT_FOLDER / f"pasted_chat_{datetime.now():%Y-%m-%d_%H-%M-%S}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Pasted chat - {datetime.now():%Y-%m-%d %H:%M:%S}\n")
        f.write(f"Messages: {len(lines)}\n")
        f.write("=" * 40 + "\n\n")
        for line in lines:
            f.write(line + "\n")
    return path


def run_pasted(text):
    """Returns (status, cards, error) for the Send Pasted Chat button."""
    lines = parse_pasted_chat(text or "")
    if not lines:
        return "Nothing to send.", None, "The paste box is empty."
    path = save_pasted_log(lines)
    print(f"[pasted] {len(lines)} messages saved to {path}")
    try:
        cards = select_cards(lines, mock=USE_MOCK)["cards"]
        return f"Sent {len(lines)} pasted messages to the AI (saved to {path.name})", cards, None
    except Exception as error:
        return f"Saved {len(lines)} pasted messages to {path.name}", None, f"AI step failed: {error}"


def run_ai(messages):
    """Returns (cards, error). Never raises, so Stop always answers the page."""
    lines = to_ai_lines(messages)
    if not lines:
        return None, "No chat messages were collected, so there is nothing to send to the AI."
    try:
        return select_cards(lines, mock=USE_MOCK)["cards"], None
    except Exception as error:
        return None, f"AI step failed: {error}"


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
            return "Not listening - press Start first.", None, None
        read_chat = False
    listener_thread.join()               # wait for the loop to finish (about 1 second)
    end_time = datetime.now()
    with lock:
        messages = list(chat_messages)
    path = save_chat_log(messages, start_time, end_time)
    print(f"[saved] {len(messages)} messages to {path}")
    cards, error = run_ai(messages)
    return f"Stopped. Saved {len(messages)} messages to {path.name}", cards, error


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
            reply = {"status": start_listening()}
        elif self.path == "/stop":
            status, cards, error = stop_listening()
            reply = {"status": status, "cards": cards, "error": error}
        elif self.path == "/paste":
            try:
                length = int(self.headers.get("Content-Length", 0))
                text = json.loads(self.rfile.read(length) or b"{}").get("text", "")
            except (ValueError, AttributeError):
                text = ""
            status, cards, error = run_pasted(text)
            reply = {"status": status, "cards": cards, "error": error}
        else:
            return self.respond(404, "Not found", "text/plain")
        self.respond(200, json.dumps(reply), "application/json")

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
