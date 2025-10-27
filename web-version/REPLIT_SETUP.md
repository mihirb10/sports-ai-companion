# 🏈 NFL AI Companion - Replit Web Version

## Perfect for Replit! ✅

This is a **Flask web application** optimized for Replit with:
- Beautiful chat interface
- Shareable URL (anyone can access)
- Easy deployment
- Works perfectly on mobile

## 🚀 Quick Setup on Replit (5 minutes)

### Step 1: Create a New Repl
1. Go to https://replit.com
2. Click "Create Repl"
3. Choose "Python"
4. Name it "sports-ai-companion"

### Step 2: Upload Files
Upload these files to your Repl:

**Essential:**
- `app.py` (main Flask application)
- `requirements-web.txt` (rename to `requirements.txt`)
- `.replit` (Replit configuration)

**Folders & Files:**
- Create `templates/` folder → upload `index.html`
- Create `static/css/` folder → upload `style.css`
- Create `static/js/` folder → upload `script.js`

**Your file structure should look like:**
```
sports-ai-companion/
├── app.py
├── requirements.txt
├── .replit
├── templates/
│   └── index.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
```

### Step 3: Set Your API Key 🔑
1. Click the **lock icon** (🔒) on the left sidebar (Secrets)
2. Click "+ New Secret"
3. Set:
   - **Key:** `ANTHROPIC_API_KEY`
   - **Value:** Your Anthropic API key (starts with `sk-ant-`)

**Get API key:** https://console.anthropic.com/

### Step 4: Click "Run" ▶️
That's it! Replit will:
- Install dependencies automatically
- Start the Flask server
- Give you a web URL

### Step 5: Open Your Web App
Replit will show a browser window with your chat interface!

**Your URL will be something like:**
`https://sports-ai-companion.your-username.repl.co`

## 🌐 Sharing Your App

### Option 1: Share the Replit Link
Just share your Repl's URL - anyone can use it!

**Important:** They'll use YOUR API key, so they're using your credits. If you want to share publicly, consider adding user authentication or having them enter their own keys.

### Option 2: Make It Public
1. Click "Publish" in Replit
2. Get a cleaner URL
3. Anyone can access it

### Option 3: Keep It Running 24/7 (Replit Hacker Plan)
With Replit's paid plan, your app stays online all the time.

## 💰 Cost Considerations

**Replit:**
- Free plan: Works great! App sleeps when inactive
- Hacker plan ($7/month): Always-on, custom domains

**Anthropic API:**
- ~$0.05-0.15 per conversation
- If sharing publicly, costs can add up
- Consider adding usage limits

## 🎨 Features

### Current Interface:
- ✅ Beautiful chat UI with NFL theme
- ✅ Live scores via ESPN API
- ✅ Team statistics lookup
- ✅ Fantasy football advice
- ✅ Conversation memory
- ✅ Mobile responsive
- ✅ Example questions for quick start

### Quick Actions:
- Click example buttons for instant questions
- Type naturally in the chat box
- Press Enter to send (Shift+Enter for new line)
- Reset button to start fresh conversation

## 🔧 Customization

### Change Colors
Edit `static/css/style.css`:
```css
/* Main gradient (line 10) */
background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);

/* NFL theme colors (line 48) */
background: linear-gradient(135deg, #013369 0%, #d50a0a 100%);
```

### Change Welcome Message
Edit `templates/index.html` around line 20:
```html
<p>What's on your mind? Ask me anything about football!</p>
```

### Add Your Team's Colors
Replace the NFL colors with your favorite team!

## 🐛 Troubleshooting

### "API key not configured"
- Make sure you added `ANTHROPIC_API_KEY` in Secrets (🔒)
- Check the key starts with `sk-ant-`
- Click "Stop" and "Run" again to reload

### "Module not found"
- Check `requirements.txt` is in the root folder
- Make sure it includes:
  ```
  anthropic>=0.39.0
  requests>=2.31.0
  python-dotenv>=1.0.0
  flask>=3.0.0
  ```

### "Template not found"
- Verify folder structure is correct
- `templates/` folder must contain `index.html`
- `static/` folder must contain `css/` and `js/` subfolders

### Website won't load
- Check the Replit console for errors
- Make sure port 5000 is being used
- Try clicking "Stop" and "Run" again

## 📱 Mobile Access

The app is fully responsive! Share the link and use it on:
- iPhone/iPad
- Android phones/tablets
- Desktop browsers
- Works great on all devices

## 🔒 Security Tips

### For Personal Use:
Your setup is fine - API key is stored securely in Replit Secrets.

### For Public Sharing:
If you want others to use their own API keys:

1. Add an API key input field
2. Store keys per session
3. Don't commit your key to the code

Or use Replit's authentication to track usage per user.

## 🚀 Advanced Features to Add

### 1. User Authentication
```python
from flask_login import LoginManager
# Add user accounts so each person uses their own key
```

### 2. Rate Limiting
```python
from flask_limiter import Limiter
# Prevent abuse if sharing publicly
```

### 3. Database for History
```python
# Use Replit Database to save conversations
from replit import db
```

### 4. Custom Domain
With Replit Hacker plan, connect your own domain!

## 📊 Monitoring Usage

Watch your API costs:
1. Go to https://console.anthropic.com/
2. Check "Usage" tab
3. Set up billing alerts

Each conversation costs ~$0.05-0.15, so:
- 100 conversations ≈ $5-15
- 1000 conversations ≈ $50-150

## 🎉 You're Done!

Your NFL AI Companion is now live on the web!

**Test it:**
- "What games are on right now?"
- "Explain Cover 2 defense"
- "Should I start Breece Hall or Jahmyr Gibbs?"

**Share it:**
Copy your Repl URL and send to friends!

**Enhance it:**
Check the API_INTEGRATION_GUIDE.md for adding:
- YouTube highlights
- Advanced statistics
- Fantasy league integration
- And more!

---

## Quick Commands Reference

**Start the app:**
Click "Run" button in Replit

**View logs:**
Check the Console tab in Replit

**Stop the app:**
Click "Stop" button

**Update code:**
Edit files and click "Run" again

---

## Need Help?

**Replit specific issues:**
- Check Replit documentation
- Look at the Console for error messages

**App functionality issues:**
- Review the troubleshooting section above
- Check that API key is set correctly

**Want to add features:**
- See API_INTEGRATION_GUIDE.md
- Modify app.py and add new endpoints

---

🏈 **Enjoy your NFL AI Companion on the web!** 🏈

Share the link with your football friends and start discussing!
