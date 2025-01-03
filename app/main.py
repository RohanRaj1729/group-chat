from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import json
from collections import deque

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebSocket Chat</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
        body { font-family: Arial, sans-serif; background-color: #f5f5f5; }
        .chat-container { max-width: 600px; margin: 50px auto; background: #fff; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); padding: 20px; }
        #messages { list-style: none; max-height: 300px; overflow-y: auto; margin: 20px 0; padding: 0; }
        #messages li { margin-bottom: 10px; padding: 10px; border-radius: 10px; }
        #messages .sent { background-color: #d1e7dd; align-self: flex-end; }
        #messages .received { background-color: #e3f2fd; align-self: flex-start; }
        .chat-container {
            display: flex;
            flex-direction: column;
            height: 100vh; /* Full height of the viewport */
            margin: 0;
            padding: 0;
        }

        .chat-header {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }

        #messages {
            flex-grow: 1; /* Makes messages section expand to fill available space */
            overflow-y: auto; /* Enables scrolling for messages */
            height: 100vh; /* Full height of the viewport */
            padding: 10px;
            margin: 0;
            background-color: #f9f9f9;
        }

        .message-input {
            display: flex;
            gap: 10px;
            padding: 10px;
            background-color: #fff;
            box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1);
            border-top: 1px solid #ddd;
            position: fixed;
            bottom: 0;
            width: 100%; /* Stretches the bar to full width */
        }

        .message-input input {
            flex: 1;
        }
        .message-input button {
            flex-shrink: 0;
        }
        #messages img { max-width: 100%; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="chat-container">
        <h2 class="text-center">WebSocket Chat</h2>
        <ul id="messages"></ul>
        <form class="message-input" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" class="form-control" placeholder="Type your message...">
            <input type="file" id="imageInput" class="form-control" accept="image/*">
            <button class="btn btn-primary">
                <span class="material-icons">send</span>
            </button>
        </form>
    </div>

    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws/chat`);
        const messages = document.getElementById("messages");
        const messageInput = document.getElementById("messageText");
        const imageInput = document.getElementById("imageInput");

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const li = document.createElement("li");
            li.className = data.sender === "self" ? "sent" : "received";

            if (data.type === "text") {
                li.textContent = data.content;
            } else if (data.type === "image") {
                const img = document.createElement("img");
                img.src = data.content;
                li.appendChild(img);
            }

            messages.appendChild(li);
            messages.scrollTop = messages.scrollHeight;
        };

        function sendMessage(event) {
            event.preventDefault();

            if (messageInput.value) {
                ws.send(JSON.stringify({ type: "text", content: messageInput.value }));
                messageInput.value = "";
            }

            if (imageInput.files.length > 0) {
                const reader = new FileReader();
                reader.onload = () => {
                    ws.send(JSON.stringify({ type: "image", content: reader.result }));
                };
                reader.readAsDataURL(imageInput.files[0]);
                imageInput.value = "";
            }
        }
    </script>
</body>
</html>
"""

class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))


manager = ConnectionManager()
chat_history = deque(maxlen=100)  # Stores the last 100 messages


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        # Send chat history to the new user
        for message in chat_history:
            await websocket.send_text(json.dumps(message))

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            message["sender"] = "self" if websocket in manager.active_connections else "other"
            chat_history.append(message)
            await manager.broadcast(message)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
