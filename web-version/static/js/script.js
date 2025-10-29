const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const typingIndicator = document.getElementById('typingIndicator');

let conversationStarted = false;

// Football player avatars (5 variations) - used as fallback
const userAvatars = [
    '/static/avatars/Football_player_red_jersey_bb2ddfcf.png',
    '/static/avatars/Football_player_blue_jersey_2dc695ec.png',
    '/static/avatars/Football_player_green_jersey_d8b5d345.png',
    '/static/avatars/Football_player_black_jersey_d05e4675.png',
    '/static/avatars/Football_player_white_jersey_77a7368f.png'
];

// Get user's avatar - use custom if available, otherwise use assigned fallback
function getUserAvatarPath() {
    if (window.userCustomAvatar) {
        return window.userCustomAvatar;
    }
    return userAvatars[window.userAvatarId || 0];
}

// Get initial avatar path
let userAvatarPath = getUserAvatarPath();

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
        
        // Try to get official NFL URL from data attribute, fallback to watch URL
        const officialNflUrl = iframe.dataset.officialNflUrl;
        
        // Extract video ID from embed URL as fallback
        const videoIdMatch = iframe.src.match(/\/embed\/([^?&]+)/);
        if (!videoIdMatch && !officialNflUrl) return;
        
        const videoId = videoIdMatch ? videoIdMatch[1] : null;
        const watchUrl = iframe.dataset.watchUrl || (videoId ? `https://www.youtube.com/watch?v=${videoId}` : null);
        const thumbnailUrl = iframe.dataset.thumbnail || (videoId ? `https://img.youtube.com/vi/${videoId}/hqdefault.jpg` : null);
        
        // Try to get title from data attribute or use default
        const title = iframe.dataset.title || 'NFL Highlight';
        
        // Create a wrapper to hold iframe + fallback link
        const wrapper = document.createElement('div');
        wrapper.className = 'youtube-embed-wrapper';
        iframe.parentNode.insertBefore(wrapper, iframe);
        wrapper.appendChild(iframe);
        
        // Always show a compact fallback link with official NFL footage
        // Use official NFL URL if available, otherwise fall back to the embedded video's URL
        const fallbackUrl = officialNflUrl || watchUrl;
        if (fallbackUrl) {
            const fallbackLink = createVideoFallbackLink(fallbackUrl, title);
            wrapper.appendChild(fallbackLink);
        }
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
            Want the official version?
        </div>
        <a href="${watchUrl}" target="_blank" rel="noopener noreferrer" class="fallback-watch-btn-compact">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/>
            </svg>
            Official NFL footage here
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

// ============================
// Bottom Navigation & Tab Management
// ============================

// Get all navigation items
const navItems = document.querySelectorAll('.nav-item');
const viewSections = document.querySelectorAll('.view-section');

// Function to switch views
function switchView(viewId) {
    // Hide all views
    viewSections.forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active from all nav items
    navItems.forEach(item => {
        item.classList.remove('active');
    });
    
    // Show selected view
    const selectedView = document.getElementById(viewId);
    if (selectedView) {
        selectedView.classList.add('active');
    }
    
    // Add active to clicked nav item
    const activeNavItem = document.querySelector(`[data-view="${viewId}"]`);
    if (activeNavItem) {
        activeNavItem.classList.add('active');
    }
    
    // Save to localStorage
    localStorage.setItem('activeView', viewId);
    
    // Trigger specific view logic
    if (viewId === 'scoresView') {
        loadScores();
    } else if (viewId === 'profileView') {
        loadProfile();
    }
}

// Add click listeners to navigation items
navItems.forEach(item => {
    item.addEventListener('click', () => {
        const viewId = item.getAttribute('data-view');
        switchView(viewId);
    });
});

// Restore last active view on load
document.addEventListener('DOMContentLoaded', () => {
    const lastView = localStorage.getItem('activeView') || 'chatView';
    switchView(lastView);
});

// ============================
// Profile Management
// ============================

const profileForm = document.getElementById('profileForm');
const displayNameInput = document.getElementById('displayName');
const avatarUploadInput = document.getElementById('avatarUpload');
const avatarPreview = document.getElementById('avatarPreview');
const presetAvatars = document.querySelectorAll('.preset-avatar');
const profileMessage = document.getElementById('profileMessage');

let selectedPresetAvatar = null;

// Load profile data
function loadProfile() {
    fetch('/api/profile')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const profile = data.profile;
                displayNameInput.value = profile.display_name || '';
                
                // Set avatar preview
                if (profile.custom_avatar_path) {
                    avatarPreview.src = profile.custom_avatar_path;
                } else {
                    avatarPreview.src = `/static/avatars/player${profile.fallback_avatar_id}.png`;
                }
                
                // Highlight selected preset if applicable
                if (profile.custom_avatar_path && profile.custom_avatar_path.includes('/static/avatars/player')) {
                    const avatarId = profile.custom_avatar_path.match(/player(\d)\.png/);
                    if (avatarId) {
                        const presetBtn = document.querySelector(`[data-avatar="${avatarId[1]}"]`);
                        if (presetBtn) {
                            presetBtn.classList.add('selected');
                        }
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error loading profile:', error);
        });
}

// Handle preset avatar selection
presetAvatars.forEach(button => {
    button.addEventListener('click', () => {
        // Remove selected class from all
        presetAvatars.forEach(btn => btn.classList.remove('selected'));
        
        // Add selected class to clicked
        button.classList.add('selected');
        
        // Update preview
        const avatarId = button.getAttribute('data-avatar');
        selectedPresetAvatar = avatarId;
        avatarPreview.src = `/static/avatars/player${avatarId}.png`;
        
        // Clear file input
        avatarUploadInput.value = '';
    });
});

// Handle file upload preview
avatarUploadInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        // Clear preset selection
        presetAvatars.forEach(btn => btn.classList.remove('selected'));
        selectedPresetAvatar = null;
        
        // Preview uploaded image
        const reader = new FileReader();
        reader.onload = (event) => {
            avatarPreview.src = event.target.result;
        };
        reader.readAsDataURL(file);
    }
});

// Handle profile form submission
profileForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('display_name', displayNameInput.value);
    
    // Add file if uploaded
    if (avatarUploadInput.files[0]) {
        formData.append('avatar', avatarUploadInput.files[0]);
    }
    
    // Add preset avatar selection if selected
    if (selectedPresetAvatar !== null) {
        formData.append('preset_avatar', selectedPresetAvatar);
    }
    
    try {
        const response = await fetch('/api/profile', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showProfileMessage('Profile updated successfully!', 'success');
            
            // Update global user data
            window.userDisplayName = data.profile.display_name;
            window.userCustomAvatar = data.profile.custom_avatar_path;
            
            // Reload chat avatars
            updateChatAvatars();
        } else {
            showProfileMessage(data.error || 'Failed to update profile', 'error');
        }
    } catch (error) {
        console.error('Profile update error:', error);
        showProfileMessage('An error occurred. Please try again.', 'error');
    }
});

// Show profile message
function showProfileMessage(message, type) {
    profileMessage.textContent = message;
    profileMessage.className = `profile-message ${type}`;
    profileMessage.style.display = 'block';
    
    setTimeout(() => {
        profileMessage.style.display = 'none';
    }, 5000);
}

// Update chat avatars after profile change
function updateChatAvatars() {
    // Reload the user avatar path to use the new custom avatar in future messages
    userAvatarPath = getUserAvatarPath();
}

// ============================
// Scores Management
// ============================

const scoresContent = document.getElementById('scoresContent');
const weekSelector = document.getElementById('weekSelector');
let currentWeekNumber = null;

// Load scores data
function loadScores(week = 'current') {
    // If we don't have current week number yet, load it first
    if (!currentWeekNumber && week === 'next') {
        // Load current week first to get the week number
        fetch('/api/scores')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentWeekNumber = data.current_week;
                    // Now load next week
                    loadScores('next');
                }
            });
        return;
    }
    
    let weekParam = '';
    if (week === 'next' && currentWeekNumber) {
        weekParam = `?week=${currentWeekNumber + 1}`;
    }
    
    fetch(`/api/scores${weekParam}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Store current week number if we don't have it
                if (!currentWeekNumber) {
                    currentWeekNumber = data.current_week;
                }
                
                if (data.games && data.games.length > 0) {
                    renderScores(data.games);
                } else {
                    scoresContent.innerHTML = `
                        <div class="scores-loading">
                            <p style="color: var(--text-secondary);">${data.status || 'No games available'}</p>
                        </div>
                    `;
                }
            } else {
                scoresContent.innerHTML = `
                    <div class="scores-loading">
                        <p style="color: var(--text-secondary);">Failed to load scores</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading scores:', error);
            scoresContent.innerHTML = `
                <div class="scores-loading">
                    <p style="color: var(--text-secondary);">Failed to load scores</p>
                </div>
            `;
        });
}

// Week selector change handler
if (weekSelector) {
    weekSelector.addEventListener('change', (e) => {
        loadScores(e.target.value);
    });
}

// Render scores with team logos
function renderScores(games) {
    scoresContent.innerHTML = '';
    
    games.forEach(game => {
        const gameCard = document.createElement('div');
        gameCard.className = 'game-card';
        
        const homeScore = game.home_score !== undefined && game.home_score !== 'N/A' ? game.home_score : '-';
        const awayScore = game.away_score !== undefined && game.away_score !== 'N/A' ? game.away_score : '-';
        const status = game.status || 'Scheduled';
        
        gameCard.innerHTML = `
            <div class="game-status">${escapeHtml(status)}</div>
            <div class="game-matchup">
                <div class="team-row">
                    <div class="team-logo-container">
                        ${game.away_logo ? `<img src="${escapeHtml(game.away_logo)}" alt="${escapeHtml(game.away_abbr)}" class="team-logo">` : ''}
                        <span class="team-abbr">${escapeHtml(game.away_abbr || 'TBD')}</span>
                    </div>
                    <div class="team-score">${awayScore !== '-' ? awayScore : ''}</div>
                </div>
                <div class="team-row">
                    <div class="team-logo-container">
                        ${game.home_logo ? `<img src="${escapeHtml(game.home_logo)}" alt="${escapeHtml(game.home_abbr)}" class="team-logo">` : ''}
                        <span class="team-abbr">${escapeHtml(game.home_abbr || 'TBD')}</span>
                    </div>
                    <div class="team-score">${homeScore !== '-' ? homeScore : ''}</div>
                </div>
            </div>
        `;
        
        scoresContent.appendChild(gameCard);
    });
}
