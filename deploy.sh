#!/bin/bash

# Streamlit Cloud Deployment Script

echo "🚀 Deploying Etsy Analytics Dashboard to Streamlit Cloud..."

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "❌ Git not found. Please install Git first."
    exit 1
fi

# Check if repository is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit for Streamlit Cloud deployment"
fi

# Check if remote origin exists
if ! git remote get-url origin &> /dev/null; then
    echo "🔗 Please add your GitHub repository as origin:"
    echo "git remote add origin https://github.com/yourusername/your-repo.git"
    echo "git push -u origin main"
    echo ""
    echo "Then go to https://share.streamlit.io to deploy!"
    exit 1
fi

# Add and commit all changes
echo "📝 Committing changes..."
git add .
git commit -m "Deploy to Streamlit Community Cloud - $(date)"

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push origin main

echo "✅ Code pushed to GitHub!"
echo ""
echo "🎯 Next steps:"
echo "1. Go to https://share.streamlit.io"
echo "2. Sign in with your GitHub account"
echo "3. Click 'New app'"
echo "4. Select your repository"
echo "5. Set main file: main.py"
echo "6. Add secrets in Settings → Secrets:"
echo ""
echo "   [secrets]"
echo "   POSTGRES_HOST = \"aws-1-ap-southeast-1.pooler.supabase.com\""
echo "   POSTGRES_PORT = \"6543\""
echo "   POSTGRES_DB = \"postgres\""
echo "   POSTGRES_USER = \"postgres.ltnxbmqzguhwwilvxfaj\""
echo "   POSTGRES_PASSWORD = \"mAdJUW85WcoYJiCc\""
echo "   POSTGRES_URL = \"postgresql://postgres.ltnxbmqzguhwwilvxfaj:mAdJUW85WcoYJiCc@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres\""
echo ""
echo "7. Click 'Deploy!'"
echo ""
echo "🎉 Your dashboard will be live at the provided URL!"
echo "📊 Dashboard features:"
echo "   - Real-time analytics"
echo "   - Interactive charts"
echo "   - Mobile-friendly"
echo "   - Auto-refresh data"
echo "   - 24/7 availability"
