document.addEventListener('DOMContentLoaded', function() {
    // Connect to Socket.IO
    const socket = io();
    
    // DOM elements
    const chatMessages = document.getElementById('chat-messages');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    
    // Typing indicator element
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';
    typingIndicator.innerHTML = '<span></span><span></span><span></span>';
    
    // Load chat history
    loadChatHistory();
    
    // Add typing animation
    function showTypingIndicator() {
        chatMessages.appendChild(typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function hideTypingIndicator() {
        if (typingIndicator.parentNode === chatMessages) {
            chatMessages.removeChild(typingIndicator);
        }
    }
    
    // Format timestamp
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // Add a message to the chat
    function addMessage(message, isUser, timestamp = new Date().toISOString()) {
        const messageElement = document.createElement('div');
        messageElement.className = isUser ? 'message user fade-in' : 'message sophia fade-in';
        
        const formattedTime = formatTimestamp(timestamp);
        
        messageElement.innerHTML = `
            ${message}
            <span class="timestamp">${formattedTime}</span>
        `;
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Load chat history from the server
    function loadChatHistory() {
        fetch('/api/chat_history')
            .then(response => response.json())
            .then(data => {
                // Clear existing messages
                chatMessages.innerHTML = '';
                
                // Add each message to the chat
                data.messages.forEach(msg => {
                    addMessage(msg.content, msg.is_from_user, msg.timestamp);
                });
                
                // Scroll to bottom
                chatMessages.scrollTop = chatMessages.scrollHeight;
            })
            .catch(error => {
                console.error('Error loading chat history:', error);
            });
    }
    
    // Send a message
    function sendMessage(message) {
        if (!message.trim()) return;
        
        // Add user message to the chat
        addMessage(message, true);
        
        // Clear input
        messageInput.value = '';
        
        // Show typing indicator
        showTypingIndicator();
        
        // Emit message to server
        socket.emit('message', { message: message });
    }
    
    // Handle form submission
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        sendMessage(messageInput.value);
    });
    
    // Enable/disable send button based on input
    messageInput.addEventListener('input', function() {
        sendButton.disabled = !messageInput.value.trim();
    });
    
    // Socket.IO events
    socket.on('connect', function() {
        console.log('Connected to server');
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
    });
    
    socket.on('response', function(data) {
        // Hide typing indicator
        hideTypingIndicator();
        
        if (data.error) {
            console.error('Error:', data.error);
            return;
        }
        
        // Add Sophia's response to the chat
        addMessage(data.message, false, data.timestamp);
    });
    
    // Initialize
    messageInput.value = '';
    sendButton.disabled = true;
});
