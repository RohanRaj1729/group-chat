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
    <title>Material Chat</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Roboto', sans-serif;
        }

        body {
            background-color: #f5f5f5;
        }

        .dialog-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }

        .dialog-card {
            background: white;
            padding: 24px;
            border-radius: 8px;
            width: 90%;
            max-width: 400px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .dialog-title {
            font-size: 1.5rem;
            color: #1a73e8;
            margin-bottom: 16px;
            font-weight: 500;
        }

        .dialog-input {
            width: 100%;
            padding: 12px;
            border: 1px solid #dadce0;
            border-radius: 4px;
            margin-bottom: 16px;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .dialog-input:focus {
            border-color: #1a73e8;
        }

        .dialog-button {
            background-color: #1a73e8;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 500;
            text-transform: uppercase;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        .dialog-button:hover {
            background-color: #1557b0;
        }

        .chat-container {
            max-width: 1200px;
            margin: 0 auto;
            height: 100vh;
            display: flex;
            flex-direction: column;
            background: white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .chat-header {
            padding: 16px;
            background: #1a73e8;
            color: white;
            display: flex;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .chat-header h2 {
            margin-left: 12px;
            font-weight: 500;
        }

        #messages {
            flex-grow: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            list-style: none;
        }

        .message-card {
            padding: 12px 16px;
            border-radius: 8px;
            background: #f8f9fa;
            max-width: 80%;
            align-self: flex-start;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
            position: relative;
        }

        .message-card.self {
            background: #e3f2fd;
            align-self: flex-end;
        }

        .username {
            font-size: 0.875rem;
            color: #5f6368;
            margin-bottom: 4px;
            font-weight: 500;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .message-actions {
            display: none;
            gap: 8px;
        }

        .message-card:hover .message-actions {
            display: flex;
        }

        .action-button {
            background: none;
            border: none;
            cursor: pointer;
            color: #5f6368;
            padding: 4px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .action-button:hover {
            background: rgba(0, 0, 0, 0.04);
        }

        .message-content {
            color: #202124;
            line-height: 1.4;
        }

        .message-content img {
            max-width: 100%;
            border-radius: 4px;
            margin-top: 8px;
        }

        .reply-content {
            margin-bottom: 8px;
            padding: 8px;
            background: rgba(0, 0, 0, 0.04);
            border-left: 3px solid #1a73e8;
            border-radius: 4px;
            font-size: 0.875rem;
        }

        .reply-username {
            font-weight: 500;
            color: #1a73e8;
            margin-bottom: 4px;
        }

        .message-input-container {
            padding: 16px;
            background: white;
            border-top: 1px solid #dadce0;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .reply-preview {
            padding: 8px 16px;
            background: #f8f9fa;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.875rem;
        }

        .reply-preview-content {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .input-actions {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .message-input {
            flex-grow: 1;
            padding: 12px;
            border: 1px solid #dadce0;
            border-radius: 24px;
            outline: none;
            font-size: 1rem;
            transition: border-color 0.2s;
        }

        .message-input:focus {
            border-color: #1a73e8;
        }

        .send-button {
            background: #1a73e8;
            color: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        .send-button:hover {
            background-color: #1557b0;
        }

        .file-input-container {
            position: relative;
            width: 40px;
            height: 40px;
        }

        .file-input {
            position: absolute;
            width: 100%;
            height: 100%;
            opacity: 0;
            cursor: pointer;
        }

        .file-button {
            width: 100%;
            height: 100%;
            background: #f1f3f4;
            border: none;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #5f6368;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        .file-button:hover {
            background-color: #e8eaed;
        }
    </style>
</head>
<body>
    <div id="usernameDialog" class="dialog-overlay">
        <div class="dialog-card">
            <h3 class="dialog-title">Welcome to Chat</h3>
            <input type="text" id="usernameInput" class="dialog-input" placeholder="Enter your username">
            <button id="setUsername" class="dialog-button">Join Chat</button>
        </div>
    </div>

    <div class="chat-container">
        <div class="chat-header">
            <span class="material-icons">chat</span>
            <h2>Material Chat</h2>
        </div>
        <ul id="messages"></ul>
        <form class="message-input-container" onsubmit="sendMessage(event)">
            <div id="replyPreview" style="display: none;" class="reply-preview">
                <div class="reply-preview-content">
                    <span class="material-icons">reply</span>
                    <div>
                        <div style="font-weight: 500;" id="replyToUsername"></div>
                        <div id="replyToContent"></div>
                    </div>
                </div>
                <button type="button" class="action-button" onclick="cancelReply()">
                    <span class="material-icons">close</span>
                </button>
            </div>
            <div class="input-actions">
                <input type="text" id="messageText" class="message-input" placeholder="Type a message">
                <div class="file-input-container">
                    <input type="file" id="imageInput" class="file-input" accept="image/*">
                    <button type="button" class="file-button">
                        <span class="material-icons">image</span>
                    </button>
                </div>
                <button type="submit" class="send-button">
                    <span class="material-icons">send</span>
                </button>
            </div>
        </form>
    </div>

    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws/chat`);
        const messages = document.getElementById("messages");
        const messageInput = document.getElementById("messageText");
        const imageInput = document.getElementById("imageInput");
        const usernameInput = document.getElementById("usernameInput");
        const usernameDialog = document.getElementById("usernameDialog");
        const setUsernameButton = document.getElementById("setUsername");
        const replyPreview = document.getElementById("replyPreview");
        const replyToUsername = document.getElementById("replyToUsername");
        const replyToContent = document.getElementById("replyToContent");

        let username = localStorage.getItem("username");
        let replyingTo = null;

        if (username) {
            usernameDialog.style.display = "none";
        }

        setUsernameButton.addEventListener("click", () => {
            username = usernameInput.value.trim();
            if (username) {
                localStorage.setItem("username", username);
                usernameDialog.style.display = "none";
            } else {
                usernameInput.classList.add("error");
            }
        });
        
        function compressImage(file) {
            return new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const img = new Image();
                    img.onload = () => {
                        const canvas = document.createElement('canvas');
                        let width = img.width;
                        let height = img.height;
                        
                        // Max dimensions
                        const MAX_WIDTH = 1200;
                        const MAX_HEIGHT = 1200;
                        
                        if (width > height) {
                            if (width > MAX_WIDTH) {
                                height *= MAX_WIDTH / width;
                                width = MAX_WIDTH;
                            }
                        } else {
                            if (height > MAX_HEIGHT) {
                                width *= MAX_HEIGHT / height;
                                height = MAX_HEIGHT;
                            }
                        }
                        
                        canvas.width = width;
                        canvas.height = height;
                        
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(img, 0, 0, width, height);
                        
                        resolve(canvas.toDataURL('image/jpeg', 0.8));
                    };
                    img.src = e.target.result;
                };
                reader.readAsDataURL(file);
            });
        }

        function createThumbnail(imgSrc) {
            return new Promise((resolve) => {
                const img = new Image();
                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    const THUMB_SIZE = 100;
                    let width = img.width;
                    let height = img.height;
                    
                    if (width > height) {
                        height *= THUMB_SIZE / width;
                        width = THUMB_SIZE;
                    } else {
                        width *= THUMB_SIZE / height;
                        height = THUMB_SIZE;
                    }
                    
                    canvas.width = width;
                    canvas.height = height;
                    
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, width, height);
                    
                    resolve(canvas.toDataURL('image/jpeg', 0.7));
                };
                img.src = imgSrc;
            });
        }

        async function setReply(messageId, replyUsername, content, type) {
            replyingTo = messageId;
            replyToUsername.textContent = replyUsername;
            
            if (type === 'image') {
                const thumbnail = await createThumbnail(content);
                replyToContent.innerHTML = `<img src="${thumbnail}" style="max-height: 50px;">`;
            } else {
                replyToContent.textContent = content;
            }
            
            replyPreview.style.display = "flex";
            messageInput.focus();
        }

        function cancelReply() {
            replyingTo = null;
            replyPreview.style.display = "none";
        }

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const messageCard = document.createElement("li");
            messageCard.classList.add("message-card");
            messageCard.setAttribute("data-message-id", data.id);
            messageCard.setAttribute("data-message-type", data.type);
            
            if (data.username === username) {
                messageCard.classList.add("self");
            }

            const usernameDiv = document.createElement("div");
            usernameDiv.classList.add("username");
            
            const usernameText = document.createElement("span");
            usernameText.textContent = data.username;
            usernameDiv.appendChild(usernameText);

            const actions = document.createElement("div");
            actions.classList.add("message-actions");
            
            const replyButton = document.createElement("button");
            replyButton.classList.add("action-button");
            replyButton.innerHTML = '<span class="material-icons">reply</span>';
            replyButton.onclick = () => setReply(data.id, data.username, data.content, data.type);
            actions.appendChild(replyButton);
            
            usernameDiv.appendChild(actions);

            const messageContentDiv = document.createElement("div");
            messageContentDiv.classList.add("message-content");

            if (data.replyTo) {
                const replyDiv = document.createElement("div");
                replyDiv.classList.add("reply-content");
                
                const replyUsername = document.createElement("div");
                replyUsername.classList.add("reply-username");
                replyUsername.textContent = data.replyTo.username;
                
                const replyContent = document.createElement("div");
                if (data.replyTo.type === 'image') {
                    replyContent.innerHTML = `<img src="${data.replyTo.thumbnail}" style="max-height: 50px;">`;
                } else {
                    replyContent.textContent = data.replyTo.content;
                }
                
                replyDiv.appendChild(replyUsername);
                replyDiv.appendChild(replyContent);
                messageContentDiv.appendChild(replyDiv);
            }

            if (data.type === "text") {
                messageContentDiv.appendChild(document.createTextNode(data.content));
            } else if (data.type === "image") {
                const img = document.createElement("img");
                img.src = data.content;
                messageContentDiv.appendChild(img);
            }

            messageCard.appendChild(usernameDiv);
            messageCard.appendChild(messageContentDiv);
            messages.appendChild(messageCard);
            messages.scrollTop = messages.scrollHeight;
        };

        async function sendMessage(event) {
            event.preventDefault();
            
            if (!username) {
                alert("Please set your username first!");
                return;
            }

            const messageId = Date.now().toString();
            const messageData = {
                id: messageId,
                username: username,
                timestamp: new Date().toISOString()
            };

            if (replyingTo) {
                const replyMessage = document.querySelector(`[data-message-id="${replyingTo}"]`);
                if (replyMessage) {
                    const messageType = replyMessage.getAttribute('data-message-type');
                    const content = messageType === 'image' ? 
                        replyMessage.querySelector(".message-content img").src :
                        replyMessage.querySelector(".message-content").textContent;
                        
                    messageData.replyTo = {
                        id: replyingTo,
                        username: replyMessage.querySelector(".username span").textContent,
                        content: content,
                        type: messageType,
                        thumbnail: messageType === 'image' ? await createThumbnail(content) : null
                    };
                }
                cancelReply();
            }

            if (messageInput.value) {
                ws.send(JSON.stringify({
                    ...messageData,
                    type: "text",
                    content: messageInput.value
                }));
                messageInput.value = "";
            }

            if (imageInput.files.length > 0) {
                const compressedImage = await compressImage(imageInput.files[0]);
                ws.send(JSON.stringify({
                    ...messageData,
                    type: "image",
                    content: compressedImage
                }));
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
            chat_history.append(message)
            await manager.broadcast(message)

    except WebSocketDisconnect:
        manager.disconnect(websocket)