# 🚀 Deploy Your NFL AI Companion to Replit (5 Minutes)

Since your laptop has security restrictions blocking localhost access, deploying to Replit will give you a **public URL** you can access from any browser!

## ✅ Step-by-Step Guide

### 1. Go to Replit
Visit: **https://replit.com**
- Sign up or log in (it's free!)

### 2. Create a New Repl
- Click **"+ Create Repl"** button
- Select **"Python"** as the template
- Name it: **"nfl-ai-companion"**
- Click **"Create Repl"**

### 3. Upload Your Files

You need to upload these files from your project:

**Required Files:**
```
✅ app.py
✅ requirements.txt
✅ .replit
✅ templates/index.html
✅ static/css/style.css
✅ static/js/script.js
```

**How to upload:**
- Click the **"Files"** icon (📁) on the left sidebar
- Create folders: `templates`, `static/css`, `static/js`
- Drag and drop or click "Upload file" for each file

**Your file structure should look like:**
```
nfl-ai-companion/
├── app.py
├── requirements.txt
├── .replit
├── templates/
│   └── index.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── script.js
```

### 4. Add Your API Key 🔑

**IMPORTANT:** Don't put your API key in the code!

1. Click the **Lock icon** 🔒 on the left sidebar (labeled "Secrets")
2. Click **"+ New Secret"**
3. Add:
   - **Key:** `ANTHROPIC_API_KEY`
   - **Value:** `your-anthropic-api-key-here` (starts with `sk-ant-`)
4. Click **"Add Secret"**

**Get your API key at:** https://console.anthropic.com/

### 5. Click "Run" ▶️

That's it! Replit will:
- ✅ Install dependencies automatically
- ✅ Start the Flask server
- ✅ Give you a live preview
- ✅ Provide a shareable URL

### 6. Access Your App! 🎉

You'll get a URL like:
```
https://nfl-ai-companion.yourusername.repl.co
```

**This URL works from:**
- ✅ Any browser
- ✅ Any device (phone, tablet, laptop)
- ✅ Anywhere in the world
- ✅ Even with your laptop's security restrictions!

---

## 🌐 Share Your App

**Your Replit URL is public by default!**

You can share it with friends, but remember:
- They'll use YOUR API key (costs you money)
- Each conversation costs ~$0.05-0.15

**To monitor costs:**
- Go to https://console.anthropic.com/
- Check the "Usage" tab

---

## 🔧 Alternative: Use the CLI Version Locally

If you don't want to deploy to Replit, you can still use the app via command line:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
python3 demo_cli.py
```

This works in your terminal without any browser restrictions!

---

## ❓ Troubleshooting

### "Module not found" error on Replit
- Make sure `requirements.txt` is uploaded to the **root** folder
- Click "Stop" and "Run" again

### "API key not configured"
- Verify you added the secret in the Secrets tab (🔒)
- Make sure the key name is exactly: `ANTHROPIC_API_KEY`
- Click "Stop" and "Run" again

### "Template not found"
- Verify the folder structure matches exactly
- `templates/` folder must contain `index.html`
- Folder names are case-sensitive

### App won't load in Replit webview
- Check the Console tab for error messages
- Make sure port 5000 is being used
- Try opening the external URL in a new browser tab

---

## 💡 Pro Tips

### Keep It Running 24/7
- Free Replit accounts: App sleeps after inactivity
- Replit Core ($7/mo): Always-on hosting
- Alternative: Deploy to Railway, Render, or Heroku

### Customize Your App
- Edit `static/css/style.css` to change colors/styling
- Edit `templates/index.html` to change welcome messages
- Edit `app.py` to add new features

### Add a Custom Domain (Replit Core)
- Get a professional URL like `nfl-companion.com`
- Requires Replit Core subscription

---

## 🎯 Quick Start Checklist

- [ ] Create Replit account
- [ ] Create new Python Repl named "nfl-ai-companion"
- [ ] Upload all 6 required files
- [ ] Create folders: templates, static/css, static/js
- [ ] Add ANTHROPIC_API_KEY to Secrets
- [ ] Click "Run"
- [ ] Access your public URL!

---

## 🏈 Enjoy Your NFL AI Companion!

Once deployed, you can:
- Ask about live scores
- Get fantasy football advice
- Discuss tactics and strategy
- Share with friends

Your app will be accessible from any browser, bypassing your laptop's security restrictions!
