#!/bin/bash
# Setup Git Authentication with Personal Access Token
# Usage: source scripts/setup_git_auth.sh

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Environment variables loaded from .env"
else
    echo "❌ .env file not found. Please create it from .env.example"
    exit 1
fi

# Check if GITHUB_TOKEN is set
if [ "$GITHUB_TOKEN" = "your_github_token_here" ] || [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Please set your GITHUB_TOKEN in .env file"
    echo "   Get your token from: https://github.com/settings/tokens"
    exit 1
fi

# Configure git to use credential helper
git config --global credential.helper store

# Configure git to use the token (this will be stored in ~/.git-credentials)
echo "https://${GITHUB_TOKEN}@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

echo "✅ Git authentication configured successfully"
echo "   You can now use: git push origin main"
