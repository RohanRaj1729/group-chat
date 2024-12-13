from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
app = FastAPI()

html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebSocket Chat</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
    <!-- Material Icons -->
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
        body {
            background-color: #f5f5f5;
            font-family: 'Roboto', sans-serif;
        }
        .chat-container {
            max-width: 600px;
            margin: auto;
            margin-top: 50px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
            border-radius: 10px;
            background-color: #fff;
            padding: 20px;
        }
        .chat-header {
            text-align: center;
            border-bottom: 1px solid #ddd;
            margin-bottom: 20px;
            padding-bottom: 10px;
        }
        #messages {
            list-style-type: none;
            padding: 0;
            max-height: 300px;
            overflow-y: auto;
            margin-bottom: 20px;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 10px;
            background-color: #f9f9f9;
        }
        #messages li {
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 8px;
        }
        #messages li:nth-child(odd) {
            background-color: #e3f2fd;
        }
        #messages li:nth-child(even) {
            background-color: #bbdefb;
        }
        .message-input {
            display: flex;
            gap: 10px;
        }
        .message-input input {
            flex-grow: 1;
            border-radius: 5px;
        }
        .message-input button {
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container chat-container">
        <header class="chat-header">
            <h1>WebSocket Chat</h1>
        </header>
        <div id="username-prompt">
            <label for="usernameInput" class="form-label">Enter your name:</label>
            <input type="text" id="usernameInput" class="form-control mb-3" placeholder="Your name" required />
            <button id="joinChat" class="btn btn-primary w-100">Join Chat</button>
        </div>
        <div id="chat-section" style="display: none;">
            <h2>Welcome, <span id="user-name" class="text-primary"></span>!</h2>
            <ul id="messages"></ul>
            <form onsubmit="sendMessage(event)" class="message-input">
                <input type="text" class="form-control" id="messageText" placeholder="Type your message..." autocomplete="off" required />
                <button class="btn btn-primary">
                    <span class="material-icons">send</span>
                </button>
            </form>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-cVTAZF2z5oR0cFNExnbssmTrj91muZV5l9BMK5l2QxE1rxht5OJQECXY76i8IJG2" crossorigin="anonymous"></script>
    <script>
        let ws;
        let username;

        document.addEventListener("DOMContentLoaded", () => {
            // Check if a username exists in localStorage
            const storedUsername = localStorage.getItem("username");

            if (storedUsername) {
                // If username exists, directly enter the chat
                username = storedUsername;
                initializeChat();
            } else {
                // Show the username prompt if no username is found
                document.getElementById("username-prompt").style.display = "block";
            }
        });

        document.getElementById("joinChat").addEventListener("click", () => {
            username = document.getElementById("usernameInput").value.trim();
            if (username) {
                // Save the username to localStorage
                localStorage.setItem("username", username);
                initializeChat();
            }
        });

        function initializeChat() {
            // Hide the username prompt and show the chat section
            document.getElementById("username-prompt").style.display = "none";
            document.getElementById("chat-section").style.display = "block";
            document.getElementById("user-name").textContent = username;

            // Establish WebSocket connection with a unique ID
            const uniquePath = Date.now();
            ws = new WebSocket(`ws://localhost:9999/ws/${uniquePath}`);

            ws.onopen = () => {
                // Send the username to the server
                ws.send(JSON.stringify({ type: "username", data: username }));
            };

            ws.onmessage = function (event) {
                const messages = document.getElementById("messages");
                const message = document.createElement("li");
                const content = document.createTextNode(event.data);
                message.appendChild(content);
                messages.appendChild(message);
                messages.scrollTop = messages.scrollHeight; // Scroll to the latest message
            };
        }

        function sendMessage(event) {
            event.preventDefault();
            const input = document.getElementById("messageText");
            if (input.value.trim() !== "") {
                ws.send(JSON.stringify({ type: "message", data: input.value }));
                input.value = "";
            }
        }
    </script>

</body>
</html>
"""

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    
manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)

from collections import deque

# A deque to store the last 100 messages
chat_history = deque(maxlen=100)

@app.websocket("/ws/{unique_id}")
async def websocket_endpoint(websocket: WebSocket, unique_id: int):
    await manager.connect(websocket)
    username = None  # Placeholder for the username
    
    try:
        # Send the chat history to the new user
        for message in chat_history:
            await websocket.send_text(message)
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "username":
                # Store and broadcast the username
                username = message["data"]
                # join_message = f"{username} has joined the chat!"
                # chat_history.append(join_message)  # Add to history
                # await manager.broadcast(join_message)
            elif message["type"] == "message":
                # Broadcast messages using the username
                if username:
                    user_message = f"{username}: {message['data']}"
                    chat_history.append(user_message)  # Add to history
                    await manager.broadcast(user_message)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # if username:
        #     leave_message = f"{username} has left the chat."
        #     chat_history.append(leave_message)  # Add to history
        #     await manager.broadcast(leave_message)


# @app.websocket("/ws/{unique_id}")
# async def websocket_endpoint(websocket: WebSocket, unique_id: int):
#     await manager.connect(websocket)
#     username = None  # Placeholder for the username
    
#     try:
#         while True:
#             data = await websocket.receive_text()
#             message = json.loads(data)

#             if message["type"] == "username":
#                 # Store and broadcast the username
#                 username = message["data"]
#                 await manager.broadcast(f"{username} has joined the chat!")
#             elif message["type"] == "message":
#                 # Broadcast messages using the username
#                 if username:
#                     await manager.broadcast(f"{username}: {message['data']}")
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         if username:
#             await manager.broadcast(f"{username} has left the chat.")

# @app.websocket("/ws/{client_id}")
# async def websocket_endpoint(websocket: WebSocket, client_id: int):
#     await manager.connect(websocket)
#     try: 
#         while True:
#             data = await websocket.receive_text()
#             await manager.send_personal_message(f"You wrote: {data}", websocket)
#             await manager.broadcast(f"Client #{client_id} says: {data}")
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         await manager.broadcast(f"Client #{client_id} has left the chat")


