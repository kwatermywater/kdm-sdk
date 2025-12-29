# Security Policy

## Reporting Security Issues

If you discover a security vulnerability, please email: [security@example.com]

## Security Best Practices

### 🔒 Never Commit Sensitive Information

**DO NOT commit:**
- API keys (OpenAI, Supabase, etc.)
- Database credentials
- Environment variables with secrets
- Private keys (.pem, .key, .p12, .pfx)
- Authentication tokens
- Passwords

### ✅ Use Environment Variables

```python
import os

# ✅ GOOD - Use environment variables
server_url = os.getenv('KDM_MCP_SERVER_URL', 'http://203.237.1.4:8080/sse')
client = KDMClient(server_url=server_url)

# ❌ BAD - Never hardcode credentials
# client = KDMClient(api_key="sk-xxxxx")  # NEVER DO THIS
```

### 📝 Protected Files

The following files are automatically excluded by `.gitignore`:
- `.env`, `.env.*`, `*.env`
- `secrets/`, `credentials/`
- `*.pem`, `*.key`, `*.p12`, `*.pfx`
- `config/local.*`, `.secrets`

### 🔍 Before Committing

Always check for sensitive data:
```bash
# Check what you're about to commit
git diff --cached

# Search for potential secrets
git grep -i "api[_-]key\|secret\|password\|token"
```

### 🚨 If You Accidentally Commit Secrets

1. **Immediately rotate/revoke the exposed credentials**
2. Remove from git history:
   ```bash
   # DO NOT just delete the file - it's still in history!
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch path/to/secret/file" \
     --prune-empty --tag-name-filter cat -- --all
   ```
3. Force push (⚠️ Warning: This rewrites history)
   ```bash
   git push origin --force --all
   git push origin --force --tags
   ```
4. Notify all team members to re-clone the repository

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Features

- ✅ No hardcoded credentials in codebase
- ✅ Environment variable support for configuration
- ✅ Comprehensive `.gitignore` for sensitive files
- ✅ MCP server authentication (if required by server)
- ✅ HTTPS transport for MCP connections
