const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const resetBtn = document.getElementById('resetBtn');
const typingIndicator = document.getElementById('typingIndicator');

let conversationStarted = false;

async function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message) return;
    
    userInput.disabled = true;
    sendBtn.disabled = true;
    
    if (!conversationStarted) {
        chatContainer.innerHTML = '';
        conversationStarted = true;
    }
    
    addMessage(message, 'user');
    
    userInput.value = '';
    userInput.style.height = 'auto';
    
    typingIndicator.style.display = 'flex';
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        typingIndicator.style.display = 'none';
        
        if (data.success) {
            addMessage(data.response, 'assistant');
        } else {
            addMessage(`Error: ${data.error || 'Something went wrong'}`, 'error');
        }
    } catch (error) {
        typingIndicator.style.display = 'none';
        addMessage(`Connection error: ${error.message}. Make sure the server is running.`, 'error');
    }
    
    userInput.disabled = false;
    sendBtn.disabled = false;
    userInput.focus();
}

function addMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    if (type === 'user') {
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = text;
        messageDiv.appendChild(contentDiv);
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.textContent = '👤';
        messageDiv.appendChild(avatarDiv);
    } else if (type === 'assistant') {
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.textContent = '🏈';
        messageDiv.appendChild(avatarDiv);
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = formatMessage(text);
        messageDiv.appendChild(contentDiv);
    } else if (type === 'error') {
        const contentDiv = document.createElement('div');
        contentDiv.className = 'error-message';
        contentDiv.textContent = text;
        chatContainer.appendChild(contentDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return;
    }
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function formatMessage(text) {
    text = escapeHtml(text);
    
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    text = text.replace(/\n/g, '<br>');
    
    text = text.split('<br>').map(line => {
        if (line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
            return `<li>${line.replace(/^[-•]\s*/, '')}</li>`;
        }
        return line;
    }).join('<br>');
    
    text = text.replace(/(<li>.*?<\/li><br>)+/g, match => {
        return '<ul>' + match.replace(/<br>/g, '') + '</ul>';
    });
    
    const paragraphs = text.split('<br><br>');
    text = paragraphs.map(p => p.trim() ? `<p>${p}</p>` : '').join('');
    
    return text;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function resetConversation() {
    if (!confirm('Start a new conversation?')) {
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
            location.reload();
        }
    } catch (error) {
        alert('Error resetting conversation: ' + error.message);
    }
}

sendBtn.addEventListener('click', sendMessage);

userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 200) + 'px';
});

resetBtn.addEventListener('click', resetConversation);

document.querySelectorAll('.prompt-card').forEach(btn => {
    btn.addEventListener('click', function() {
        const question = this.getAttribute('data-question');
        userInput.value = question;
        userInput.focus();
        sendMessage();
    });
});

userInput.focus();

async function checkHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        if (!data.api_key_configured) {
            addMessage(
                'Warning: ANTHROPIC_API_KEY is not configured. Please set it in your Replit Secrets.',
                'error'
            );
        }
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

checkHealth();
