const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const typingIndicator = document.getElementById('typingIndicator');

let conversationStarted = false;

// Football player avatars (5 variations)
const userAvatars = [
    '/static/avatars/Football_player_red_jersey_bb2ddfcf.png',
    '/static/avatars/Football_player_blue_jersey_2dc695ec.png',
    '/static/avatars/Football_player_green_jersey_d8b5d345.png',
    '/static/avatars/Football_player_black_jersey_d05e4675.png',
    '/static/avatars/Football_player_white_jersey_77a7368f.png'
];

// Get user's assigned avatar (set in HTML template)
const userAvatarPath = userAvatars[window.userAvatarId || 0];

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
    
    // Add loading indicator as a message bubble
    const loadingDiv = addLoadingMessage();
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        // Remove loading indicator
        loadingDiv.remove();
        
        if (data.success) {
            // Stream the response word by word
            await streamMessage(data.response, 'assistant');
        } else {
            addMessage(`Error: ${data.error || 'Something went wrong'}`, 'error');
        }
    } catch (error) {
        loadingDiv.remove();
        addMessage(`Connection error: ${error.message}. Make sure the server is running.`, 'error');
    }
    
    userInput.disabled = false;
    sendBtn.disabled = false;
    userInput.focus();
}

function addLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message loading-message';
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.textContent = '🏈';
    messageDiv.appendChild(avatarDiv);
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
    messageDiv.appendChild(contentDiv);
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    return messageDiv;
}

async function streamMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.textContent = '🏈';
    messageDiv.appendChild(avatarDiv);
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    messageDiv.appendChild(contentDiv);
    
    chatContainer.appendChild(messageDiv);
    
    // Split into words for streaming effect
    const words = text.split(' ');
    let currentText = '';
    
    for (let i = 0; i < words.length; i++) {
        currentText += (i > 0 ? ' ' : '') + words[i];
        contentDiv.innerHTML = formatMessage(currentText);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        // Adjust speed: faster for longer responses
        const delay = words.length > 100 ? 15 : 30;
        await new Promise(resolve => setTimeout(resolve, delay));
    }
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
        const avatarImg = document.createElement('img');
        avatarImg.src = userAvatarPath;
        avatarImg.alt = 'User';
        avatarImg.style.width = '100%';
        avatarImg.style.height = '100%';
        avatarImg.style.objectFit = 'cover';
        avatarImg.style.borderRadius = '50%';
        avatarDiv.appendChild(avatarImg);
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
    // Extract iframe embeds before escaping HTML
    const iframePattern = /<iframe[^>]*>.*?<\/iframe>/gi;
    const iframes = [];
    let iframeIndex = 0;
    
    text = text.replace(iframePattern, (match) => {
        const placeholder = `__IFRAME_PLACEHOLDER_${iframeIndex}__`;
        iframes.push({ html: match, placeholder });
        iframeIndex++;
        return placeholder;
    });
    
    // Extract markdown images before escaping HTML
    const imagePattern = /!\[([^\]]*)\]\(([^)]+)\)/g;
    const images = [];
    let imageIndex = 0;
    
    text = text.replace(imagePattern, (match, alt, src) => {
        // Strip < and > from URLs (Claude sometimes wraps URLs)
        src = src.replace(/^<|>$/g, '').trim();
        const placeholder = `__IMAGE_PLACEHOLDER_${imageIndex}__`;
        images.push({ alt, src, placeholder });
        imageIndex++;
        return placeholder;
    });
    
    text = escapeHtml(text);
    
    // Replace iframe placeholders with actual iframes
    iframes.forEach(({ html, placeholder }) => {
        text = text.replace(placeholder, html);
    });
    
    // Replace image placeholders with actual img tags (clickable thumbnails)
    images.forEach(({ alt, src, placeholder }) => {
        const escapedAlt = alt || 'Diagram';
        const imgTag = `<img src="${src}" alt="${escapedAlt}" class="diagram-thumbnail" data-full-src="${src}">`;
        text = text.replace(placeholder, imgTag);
    });
    
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

// Image Lightbox functionality
const imageModal = document.getElementById('imageModal');
const modalImage = document.getElementById('modalImage');
const modalClose = document.getElementById('modalClose');

// Use event delegation to handle image clicks
chatContainer.addEventListener('click', (e) => {
    if (e.target.tagName === 'IMG' && e.target.classList.contains('diagram-thumbnail')) {
        openLightbox(e.target.src);
    }
});

function openLightbox(src) {
    modalImage.src = src;
    imageModal.classList.add('active');
    document.body.style.overflow = 'hidden'; // Prevent scrolling
}

function closeLightbox() {
    imageModal.classList.remove('active');
    document.body.style.overflow = ''; // Restore scrolling
}

// Close on X button click
modalClose.addEventListener('click', closeLightbox);

// Close on clicking outside the image
imageModal.addEventListener('click', (e) => {
    if (e.target === imageModal) {
        closeLightbox();
    }
});

// Close on ESC key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && imageModal.classList.contains('active')) {
        closeLightbox();
    }
});

// PWA Install functionality
let deferredPrompt;
const installButton = document.getElementById('installBtn');

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    if (installButton) {
        installButton.style.display = 'flex';
    }
});

if (installButton) {
    installButton.addEventListener('click', async () => {
        if (!deferredPrompt) {
            alert('To install SportsAI:\n\n• Android: Tap menu (⋮) → "Install app" or "Add to Home Screen"\n• iOS: Tap Share (□↑) → "Add to Home Screen"');
            return;
        }
        
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        
        if (outcome === 'accepted') {
            console.log('PWA installed');
        }
        
        deferredPrompt = null;
        installButton.style.display = 'none';
    });
}

window.addEventListener('appinstalled', () => {
    console.log('PWA was installed');
    if (installButton) {
        installButton.style.display = 'none';
    }
    deferredPrompt = null;
});

// Handle example prompt clicks
document.addEventListener('click', (e) => {
    const promptButton = e.target.closest('.example-prompt');
    if (promptButton) {
        const promptText = promptButton.getAttribute('data-prompt');
        if (promptText) {
            userInput.value = promptText;
            userInput.focus();
        }
    }
});

// Add fallback "Watch on YouTube" cards for all video embeds
function setupVideoFallbacks() {
    const iframes = document.querySelectorAll('iframe[src*="youtube.com/embed"]');
    
    iframes.forEach(iframe => {
        // Skip if already processed
        if (iframe.dataset.fallbackProcessed) return;
        iframe.dataset.fallbackProcessed = 'true';
        
        // Extract video ID from embed URL
        const videoIdMatch = iframe.src.match(/\/embed\/([^?&]+)/);
        if (!videoIdMatch) return;
        
        const videoId = videoIdMatch[1];
        const watchUrl = `https://www.youtube.com/watch?v=${videoId}`;
        const thumbnailUrl = `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
        
        // Try to get title from data attribute or use default
        const title = iframe.dataset.title || 'NFL Highlight';
        
        // Create a wrapper to hold iframe + fallback link
        const wrapper = document.createElement('div');
        wrapper.className = 'youtube-embed-wrapper';
        iframe.parentNode.insertBefore(wrapper, iframe);
        wrapper.appendChild(iframe);
        
        // Always show a compact fallback link below the video
        // This is useful if the embed is blocked by NFL restrictions
        const fallbackLink = createVideoFallbackLink(watchUrl, title);
        wrapper.appendChild(fallbackLink);
    });
}

// Create a compact fallback link for videos (always shown as backup)
function createVideoFallbackLink(watchUrl, title) {
    const link = document.createElement('div');
    link.className = 'youtube-fallback-link';
    link.innerHTML = `
        <div class="fallback-info-text">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
            </svg>
            If video doesn't play (NFL restrictions):
        </div>
        <a href="${watchUrl}" target="_blank" rel="noopener noreferrer" class="fallback-watch-btn-compact">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/>
            </svg>
            Watch on YouTube
        </a>
    `;
    return link;
}

// Run fallback setup when DOM changes (new messages added)
const observer = new MutationObserver(() => {
    setupVideoFallbacks();
});

observer.observe(chatContainer, {
    childList: true,
    subtree: true
});
