// Chat functionality
const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const resetBtn = document.getElementById('resetBtn');
const typingIndicator = document.getElementById('typingIndicator');

// Handle sending messages
async function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message) return;
    
    // Disable input while processing
    userInput.disabled = true;
    sendBtn.disabled = true;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    userInput.value = '';
    userInput.style.height = 'auto';
    
    // Show typing indicator
    typingIndicator.style.display = 'flex';
    
    try {
        // Send to backend
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        // Hide typing indicator
        typingIndicator.style.display = 'none';
        
        if (data.success) {
            // Add assistant response
            addMessage(data.response, 'assistant');
        } else {
            // Show error
            addMessage(`Error: ${data.error || 'Something went wrong'}`, 'error');
        }
    } catch (error) {
        typingIndicator.style.display = 'none';
        addMessage(`Connection error: ${error.message}. Make sure the server is running.`, 'error');
    }
    
    // Re-enable input
    userInput.disabled = false;
    sendBtn.disabled = false;
    userInput.focus();
}

// Add message to chat
function addMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (type === 'assistant') {
        // Format assistant message with markdown-like styling
        const formattedText = formatMessage(text);
        contentDiv.innerHTML = `<strong>🏈 NFL Companion:</strong><div>${formattedText}</div>`;
    } else if (type === 'user') {
        contentDiv.innerHTML = `<strong>You:</strong><div>${escapeHtml(text)}</div>`;
    } else if (type === 'error') {
        contentDiv.innerHTML = `<strong>⚠️ Error:</strong><div>${escapeHtml(text)}</div>`;
        messageDiv.className = 'error-message';
    }
    
    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Format message text (basic markdown support)
function formatMessage(text) {
    // Escape HTML first
    text = escapeHtml(text);
    
    // Bold text **text**
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic text *text*
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Line breaks
    text = text.replace(/\n/g, '<br>');
    
    // Bullet points (simple detection)
    text = text.split('<br>').map(line => {
        if (line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
            return `<li>${line.replace(/^[-•]\s*/, '')}</li>`;
        }
        return line;
    }).join('<br>');
    
    // Wrap consecutive list items in ul
    text = text.replace(/(<li>.*?<\/li><br>)+/g, match => {
        return '<ul>' + match.replace(/<br>/g, '') + '</ul>';
    });
    
    // Paragraphs
    const paragraphs = text.split('<br><br>');
    text = paragraphs.map(p => p.trim() ? `<p>${p}</p>` : '').join('');
    
    return text;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Handle reset conversation
async function resetConversation() {
    if (!confirm('Are you sure you want to reset the conversation?')) {
        return;
    }
    
    try {
        const response = await fetch('/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            // Clear chat
            chatContainer.innerHTML = '';
            
            // Add welcome message
            addMessage(
                `Hey there! I'm your NFL discussion partner. I can help you with:\n\n` +
                `• Live scores and game updates\n` +
                `• Tactical analysis and X's & O's\n` +
                `• Fantasy football decisions\n` +
                `• Deep dives into strategy and matchups\n\n` +
                `What's on your mind? Ask me anything about football!`,
                'assistant'
            );
        }
    } catch (error) {
        alert('Error resetting conversation: ' + error.message);
    }
}

// Event listeners
sendBtn.addEventListener('click', sendMessage);

userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Auto-resize textarea
userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

resetBtn.addEventListener('click', resetConversation);

// Example question buttons
document.querySelectorAll('.example-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const question = this.getAttribute('data-question');
        userInput.value = question;
        userInput.focus();
        sendMessage();
    });
});

// Focus input on load
userInput.focus();

// Check if API is configured
async function checkHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        if (!data.api_key_configured) {
            addMessage(
                'Warning: ANTHROPIC_API_KEY is not configured. Please set it in your Replit Secrets (lock icon 🔒) or environment variables.',
                'error'
            );
        }
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

// Run health check on load
checkHealth();
