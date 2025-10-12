# SSH Key Setup Guide - Add Local Key to Droplet

## 🎯 Goal

Enable direct SSH access from your local machine to the droplet so you can run:
```bash
ssh deploy@64.225.17.0
```

Without needing DigitalOcean console or GitHub Actions.

---

## 📋 Prerequisites

- ✅ You have SSH key locally: `~/.ssh/id_ed25519`
- ✅ You can access droplet via DigitalOcean console
- ✅ You know the `deploy` user password (or have root access)

---

## Understanding the Current Situation

### Two Different SSH Keys

1. **Your Local SSH Key** (`~/.ssh/id_ed25519`):
   - Located on your local machine (WSL)
   - Added to GitHub for git push/pull operations ✅
   - NOT added to droplet yet ❌
   - **This is what we're adding now**

2. **GitHub Actions SSH Key** (stored in GitHub secrets):
   - Stored in repository secrets as `BETA_SSH_KEY`
   - Used by GitHub Actions workflow to deploy
   - Already on droplet (how GitHub Actions can deploy)
   - Different key from your local key

### Why You Need Your Local Key on Droplet

- Direct SSH access for debugging
- Running commands without GitHub Actions
- Faster iteration during development
- Emergency access when GitHub is down
- Following PHASE1_NGINX_DEPLOYMENT.md instructions

---

## Step 1: Get Your Public Key

On your **local machine** (WSL):

```bash
# Display your public key
cat ~/.ssh/id_ed25519.pub
```

**Expected Output** (example):
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBx... your-email@example.com
```

**📋 Copy this entire line** - you'll need it in Step 3.

**Troubleshooting:**
- If file doesn't exist, you may need to generate a key pair (see Section 7)
- If you see "No such file or directory", check `~/.ssh/` directory exists

---

## Step 2: Access Droplet Console

Follow **EMERGENCY_FIX_NGINX.md Step 1** to access the droplet console via DigitalOcean dashboard.

Once logged in as `deploy` user, proceed to Step 3.

---

## Step 3: Add Your Public Key to Droplet

In the **droplet console**:

### 3.1 Check if authorized_keys file exists

```bash
# Check if .ssh directory exists
ls -la ~/.ssh/

# Check if authorized_keys file exists
ls -la ~/.ssh/authorized_keys
```

### 3.2 Create .ssh directory if needed

```bash
# Create directory (if it doesn't exist)
mkdir -p ~/.ssh

# Set correct permissions
chmod 700 ~/.ssh
```

### 3.3 Add your public key

**Method A: Using nano (easier for console)**

```bash
# Open authorized_keys file
nano ~/.ssh/authorized_keys

# Paste your public key (from Step 1)
# - If file is empty, paste on first line
# - If file has existing keys, add your key on a new line
# - DO NOT delete existing keys!

# Save and exit:
# - Press Ctrl+X
# - Press Y (yes to save)
# - Press Enter (confirm filename)
```

**Method B: Using echo (if copy-paste works in console)**

```bash
# Replace YOUR_PUBLIC_KEY_HERE with actual key from Step 1
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBx... your-email@example.com" >> ~/.ssh/authorized_keys
```

### 3.4 Set correct permissions

```bash
# Set file permissions
chmod 600 ~/.ssh/authorized_keys

# Verify permissions
ls -la ~/.ssh/authorized_keys
```

**Expected output:**
```
-rw------- 1 deploy deploy 567 Oct 12 15:30 /home/deploy/.ssh/authorized_keys
```

**⚠️ Important**: The file MUST have `600` permissions (read/write for owner only), or SSH will reject the key!

---

## Step 4: Verify Key Was Added Correctly

Still in the **droplet console**:

```bash
# Display authorized_keys content
cat ~/.ssh/authorized_keys

# Verify your key is there (check the email or key comment at the end)
```

**What to verify:**
- File contains your public key (starts with `ssh-ed25519`)
- No extra line breaks or spaces in the middle of the key
- Each key is on its own line
- File permissions are `600`

---

## Step 5: Test SSH Connection from Local Machine

On your **local machine** (WSL):

```bash
# Test SSH connection
ssh deploy@64.225.17.0

# First time connecting, you'll see:
# "The authenticity of host '64.225.17.0 (64.225.17.0)' can't be established."
# Type: yes
```

**Expected Result**: You should be logged in without entering a password!

**If successful, you'll see:**
```
Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-79-generic x86_64)
...
deploy@globalpeds-beta:~$
```

**Troubleshooting**: If it fails, see Section 8 below.

---

## Step 6: Verify You Can Access Project Directory

Now that you're SSH'd in:

```bash
# Navigate to project
cd /home/deploy/global-peds-reading-room

# Check current branch
git status

# Verify you can read Nginx config
sudo cat /etc/nginx/sites-available/globalpeds | head -20

# Verify services are running
systemctl is-active gunicorn nginx postgresql
```

**If all commands work**, SSH access is fully configured! ✅

---

## Step 7: Testing Workflow

Try running the deployment script manually (this is what GitHub Actions does):

```bash
# SSH to droplet
ssh deploy@64.225.17.0

# Navigate to project
cd /home/deploy/global-peds-reading-room

# Pull latest changes
git pull origin online_beta

# Activate virtual environment
source backend/venv/bin/activate

# Install dependencies (if any changed)
pip install -q -r backend/requirements.txt

# Run migrations (if any)
python backend/manage.py migrate

# Collect static files
python backend/manage.py collectstatic --noinput

# Restart services
sudo systemctl restart gunicorn
sudo systemctl reload nginx

# Check status
echo "Services:"
echo "  Gunicorn: $(systemctl is-active gunicorn)"
echo "  Nginx: $(systemctl is-active nginx)"
echo "  PostgreSQL: $(systemctl is-active postgresql)"
```

**If this works**, you can now deploy manually without GitHub Actions! ✅

---

## Troubleshooting

### Issue 1: "Permission denied (publickey)" Still Happening

**Diagnosis:**

```bash
# Test with verbose output
ssh -v deploy@64.225.17.0
```

**Common causes:**

1. **Wrong permissions on authorized_keys**:
   ```bash
   # In droplet console:
   chmod 600 ~/.ssh/authorized_keys
   chmod 700 ~/.ssh
   ```

2. **Extra spaces or line breaks in key**:
   ```bash
   # In droplet console:
   nano ~/.ssh/authorized_keys
   # Verify key is on ONE line with NO spaces in the middle
   ```

3. **Wrong user**:
   - Make sure you're adding key to `/home/deploy/.ssh/authorized_keys`
   - NOT `/root/.ssh/authorized_keys` (unless you're logging in as root)

4. **SELinux or security context issues** (rare on DigitalOcean):
   ```bash
   # In droplet console:
   restorecon -R -v ~/.ssh/
   ```

### Issue 2: "Host key verification failed"

**Solution:**

```bash
# Remove old host key
ssh-keygen -R 64.225.17.0

# Try connecting again
ssh deploy@64.225.17.0
# Type "yes" when asked about fingerprint
```

### Issue 3: Can't Edit authorized_keys (Permission Denied)

**Solution:**

```bash
# In droplet console, check ownership
ls -la ~/.ssh/authorized_keys

# If owned by root, fix it:
sudo chown deploy:deploy ~/.ssh/authorized_keys
sudo chmod 600 ~/.ssh/authorized_keys
```

### Issue 4: Can't Find Your Public Key Locally

**Generate a new SSH key pair:**

```bash
# On local machine
ssh-keygen -t ed25519 -C "your-email@example.com"

# Accept default location (~/.ssh/id_ed25519)
# Enter passphrase (or leave empty)

# Display public key
cat ~/.ssh/id_ed25519.pub
```

**Then add this new key to:**
1. Droplet (follow this guide)
2. GitHub (Settings → SSH and GPG keys → New SSH key)

### Issue 5: Multiple SSH Keys

**If you have multiple keys:**

```bash
# Test which key is being used
ssh -v deploy@64.225.17.0 2>&1 | grep "Offering public key"

# Specify which key to use explicitly
ssh -i ~/.ssh/id_ed25519 deploy@64.225.17.0

# Add to ~/.ssh/config for convenience:
cat >> ~/.ssh/config <<EOF
Host beta-droplet
    HostName 64.225.17.0
    User deploy
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
EOF

# Then you can just use:
ssh beta-droplet
```

---

## Security Best Practices

### DO ✅

1. **Use passphrase-protected keys** in production
2. **Keep private key secure** (never share, never commit)
3. **Use different keys for different purposes** (GitHub vs servers)
4. **Regularly rotate keys** (every 6-12 months)
5. **Remove old/unused keys** from authorized_keys
6. **Use `~/.ssh/config`** to manage multiple servers

### DON'T ❌

1. **Don't share private keys** (`id_ed25519` without `.pub`)
2. **Don't commit keys to git** (they're in `.gitignore`)
3. **Don't use password authentication** if possible
4. **Don't disable key-only authentication** on production servers
5. **Don't use same key for everything** (separation of concerns)

---

## Useful SSH Config (~/.ssh/config)

Create a config file for easier access:

```bash
# On local machine
nano ~/.ssh/config
```

**Add this configuration:**

```
# Beta Droplet Configuration
Host beta
    HostName 64.225.17.0
    User deploy
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3
    ForwardAgent no

# You can also add production later:
# Host prod
#     HostName your-production-ip
#     User deploy
#     IdentityFile ~/.ssh/id_ed25519_prod
```

**Now you can use:**

```bash
# Short command instead of full SSH
ssh beta

# SCP files easily
scp local-file.txt beta:/tmp/

# Run commands remotely
ssh beta 'systemctl is-active nginx'
```

---

## Verification Checklist ✅

After completing this guide, verify:

- [ ] Can SSH to droplet: `ssh deploy@64.225.17.0`
- [ ] No password prompt (key authentication works)
- [ ] Can navigate to project: `cd /home/deploy/global-peds-reading-room`
- [ ] Can run git commands: `git status`
- [ ] Can check service status: `systemctl is-active gunicorn`
- [ ] Can read Nginx config: `sudo cat /etc/nginx/sites-available/globalpeds`
- [ ] Can restart services: `sudo systemctl restart gunicorn nginx`
- [ ] SSH config file created (optional but recommended)
- [ ] Old host keys removed if any conflicts

---

## What This Enables

With SSH access configured, you can now:

1. **Follow PHASE1_NGINX_DEPLOYMENT.md** steps directly
2. **Debug issues in real-time** on the server
3. **Run manual deployments** using `scripts/deploy_beta.sh`
4. **Check logs instantly**: `tail -f /var/log/nginx/globalpeds_error.log`
5. **Test configurations** before applying
6. **Quick fixes** without waiting for GitHub Actions
7. **Emergency responses** when something breaks

---

## Next Steps

1. ✅ SSH access configured
2. **Apply Nginx configuration** (if not done yet - see EMERGENCY_FIX_NGINX.md)
3. **Test the site** thoroughly (see LOCAL_TESTING_GUIDE.md Stage 3)
4. **Document** any issues found
5. **Consider** setting up SSH key for GitHub Actions rotation (security best practice)

---

**🎉 Congratulations! You now have direct SSH access to your droplet!**
