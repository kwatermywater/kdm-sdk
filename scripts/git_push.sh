#!/bin/bash
# Git Push with Token Authentication
# Usage: ./scripts/git_push.sh [branch_name]

BRANCH=${1:-main}

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "❌ .env file not found"
    exit 1
fi

# Check token
if [ "$GITHUB_TOKEN" = "your_github_token_here" ] || [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Please set your GITHUB_TOKEN in .env file"
    echo "   Get your token from: https://github.com/settings/tokens"
    exit 1
fi

# Push using token
git push https://${GITHUB_TOKEN}@github.com/kwatermywater/kdm-sdk.git ${BRANCH}

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to ${BRANCH}"
else
    echo "❌ Push failed"
    exit 1
fi
