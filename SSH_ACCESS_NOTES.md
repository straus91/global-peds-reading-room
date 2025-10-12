# SSH Access Documentation - Beta Droplet

**Server**: 64.225.17.0 (global-readingroom)
**Last Updated**: 2025-10-12
**Purpose**: Clarify SSH access methods and user roles

---

## 🔑 SSH Access Summary

### Two Users, Two Different Access Methods

The Beta droplet has **two different users** with **separate SSH keys**:

| User | SSH Command | Purpose | Key Location (on droplet) | Your Key Status |
|------|-------------|---------|---------------------------|-----------------|
| **root** | `ssh root@64.225.17.0` | System administration, Nginx config | `/root/.ssh/authorized_keys` | ✅ Present |
| **deploy** | `ssh deploy@64.225.17.0` | Application deployment, code management | `/home/deploy/.ssh/authorized_keys` | ❌ Not present |

---

## 📊 Discovery Timeline

### How We Discovered This

**2025-10-12 Deployment:**

1. **Initial Attempt**: Tried `ssh deploy@64.225.17.0`
   - **Result**: ❌ "Permission denied (publickey)"
   - **Reason**: Local SSH key not in `/home/deploy/.ssh/authorized_keys`

2. **Investigation**: Checked project documentation
   - Found: `BETA_DEPLOYMENT.md` and `SERVER_CHEATSHEET.md` both show `ssh root@64.225.17.0`
   - Found: GitHub Actions uses `deploy` user with separate key (stored in repository secrets)

3. **Solution**: Tried `ssh root@64.225.17.0`
   - **Result**: ✅ **Success!**
   - **Conclusion**: Local SSH key IS on droplet, but only for root user

4. **Applied Fix**: Used root access to apply Nginx configuration
   - Site fixed successfully
   - Deployment completed

---

## 🎯 When to Use Which User

### Use `root` User For:

```bash
ssh root@64.225.17.0
```

**Best For:**
- ✅ System administration
- ✅ Nginx configuration changes (`/etc/nginx/`)
- ✅ Installing system packages (`apt install`)
- ✅ Service management (`systemctl restart nginx`)
- ✅ Firewall configuration (`ufw`)
- ✅ System updates
- ✅ Creating/modifying other users
- ✅ Emergency access when deploy user has issues

**Permissions**:
- Full sudo access (no password required)
- Can modify any file on system
- Can restart any service

**Your Current Access**: ✅ **Works** (SSH key present)

---

### Use `deploy` User For:

```bash
ssh deploy@64.225.17.0
```

**Best For:**
- ✅ Application code deployment
- ✅ Git operations (`git pull`)
- ✅ Python/Django operations
- ✅ Running migrations (`python manage.py migrate`)
- ✅ Collecting static files
- ✅ Viewing application logs
- ✅ Day-to-day development tasks

**Permissions**:
- Owns application files (`/home/deploy/global-peds-reading-room/`)
- Can run `sudo systemctl restart gunicorn` (configured in sudoers)
- Can run `sudo systemctl restart nginx` (configured in sudoers)
- Limited sudo access (only for specific commands)

**Your Current Access**: ❌ **Does Not Work** (SSH key not present)

**GitHub Actions Access**: ✅ **Works** (uses different key stored in repository secrets)

---

## 🔐 SSH Key Details

### Your Local SSH Key

**Location on Local Machine**:
```
Private: /home/straus91/.ssh/id_ed25519
Public:  /home/straus91/.ssh/id_ed25519.pub
```

**Public Key Content**:
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIO4q9yyVntYjpCp52Ux18vZN6ul9/WglZYIe9V2Ah+MT straus91@gmail.com
```

**Currently Added To**:
- ✅ GitHub (for git push/pull operations)
- ✅ Droplet: `/root/.ssh/authorized_keys` (root user access)
- ❌ Droplet: `/home/deploy/.ssh/authorized_keys` (deploy user access - **MISSING**)

---

### GitHub Actions SSH Key

**How It Works**:
- GitHub Actions workflow (`.github/workflows/deploy-beta.yml`) uses repository secret
- Secret name: `BETA_SSH_KEY`
- This is a **different key** than your local key
- Stored in GitHub repository settings → Secrets
- Used by GitHub Actions to SSH as `deploy` user

**Location on Droplet**:
- ✅ Present in: `/home/deploy/.ssh/authorized_keys`
- This is why GitHub Actions can deploy but you cannot SSH as deploy

**Key Insight**: There are **TWO different keys** for the deploy user:
1. GitHub Actions key (in `/home/deploy/.ssh/authorized_keys`)
2. Your local key (NOT in `/home/deploy/.ssh/authorized_keys`)

---

## ➕ Adding Your Key to Deploy User (Optional)

If you want to SSH as `deploy` user (for daily operations), follow these steps:

### Method 1: Using Root Access (Easiest)

```bash
# 1. SSH as root (you can already do this)
ssh root@64.225.17.0

# 2. Ensure .ssh directory exists for deploy user
mkdir -p /home/deploy/.ssh

# 3. Copy your public key to deploy user
# (Your key is already in /root/.ssh/authorized_keys)
cat /root/.ssh/authorized_keys >> /home/deploy/.ssh/authorized_keys

# 4. Set correct permissions
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

# 5. Exit and test
exit

# 6. From local machine, test deploy user access
ssh deploy@64.225.17.0
```

### Method 2: Using DigitalOcean Console

See `SSH_KEY_SETUP.md` for detailed instructions.

---

## 📋 Best Practices

### Security

1. **Separate Keys for Different Purposes** ✅
   - Already happening: GitHub Actions has its own key
   - Good practice: Consider separate keys for personal vs automated access

2. **Principle of Least Privilege** ✅
   - Use `deploy` user for daily operations (limited permissions)
   - Use `root` user only when necessary (full permissions)
   - Your setup already follows this for GitHub Actions

3. **Key Rotation**
   - Rotate SSH keys every 6-12 months
   - Rotate immediately if key is potentially compromised
   - Keep old keys for 30 days before removing (for rollback)

### Access Patterns

**For Regular Deployments**:
```bash
# Preferred: Use GitHub Actions
# - Click "Run workflow" in GitHub Actions tab
# - Automated, consistent, logged

# Alternative: SSH as deploy user (if key added)
ssh deploy@64.225.17.0
cd /home/deploy/global-peds-reading-room
git pull origin online_beta
# ... deployment commands ...
```

**For Infrastructure Changes**:
```bash
# Use root user
ssh root@64.225.17.0

# Make system-level changes
sudo cp nginx_app_prefix.conf /etc/nginx/sites-available/globalpeds
sudo nginx -t
sudo systemctl reload nginx
```

**For Troubleshooting**:
```bash
# Start with deploy user if possible
ssh deploy@64.225.17.0
tail -f /var/log/gunicorn/gunicorn.log

# Use root user if you need to check Nginx
ssh root@64.225.17.0
tail -f /var/log/nginx/globalpeds_error.log
```

---

## 🚀 Deployment Workflow Recommendations

### Code-Only Deployments (Use GitHub Actions)

**When**: Python code, HTML, JavaScript changes (no infrastructure)

**Method**: GitHub Actions as `deploy` user
```
1. Push code to online_beta branch
2. Go to GitHub Actions tab
3. Click "Deploy to Beta Droplet"
4. Click "Run workflow"
5. Monitor workflow output
```

**Advantages**:
- ✅ No SSH access needed
- ✅ Automated and consistent
- ✅ Logged in GitHub
- ✅ Can be triggered by team members

---

### Infrastructure Deployments (Use Root Access)

**When**: Nginx config, system packages, SSL certificates, service configs

**Method**: SSH as `root` user
```bash
ssh root@64.225.17.0
# Make infrastructure changes
# Test carefully
# Apply changes
```

**Advantages**:
- ✅ Full system access
- ✅ Can make any changes needed
- ✅ Emergency access always available

---

### Coordinated Deployments (Use Both)

**When**: Code + infrastructure changes (like this /app/ prefix deployment)

**Recommended Order**:
```
1. Apply infrastructure changes first (as root)
   ssh root@64.225.17.0
   # Apply Nginx config, etc.

2. Then deploy code (via GitHub Actions)
   # Trigger workflow

3. Test thoroughly
4. Monitor logs
```

**Alternative (What Happened This Time)**:
```
1. Deployed code first (GitHub Actions)
2. Site broke (infrastructure not ready)
3. Emergency fix infrastructure (as root)
4. Site fixed
```

**Lesson**: Infrastructure first, then code!

---

## 📊 Current Configuration Summary

### Root User
- **SSH Access**: ✅ Works (`ssh root@64.225.17.0`)
- **Your SSH Key**: ✅ Present in `/root/.ssh/authorized_keys`
- **Use For**: System administration, Nginx config, emergency access
- **Permissions**: Full sudo access

### Deploy User
- **SSH Access**: ❌ Does Not Work (`ssh deploy@64.225.17.0`)
- **Your SSH Key**: ❌ Not present in `/home/deploy/.ssh/authorized_keys`
- **GitHub Actions Key**: ✅ Present (different key)
- **Use For**: Application deployment, git operations, Django commands
- **Permissions**: Limited sudo (only for gunicorn/nginx restart)

### Recommendation
- ✅ **Current Setup Works**: Root access is sufficient for all operations
- 🔄 **Optional Improvement**: Add your key to deploy user for convenience
- ✅ **GitHub Actions**: Continue using for code deployments

---

## 🔧 Troubleshooting

### "Permission denied (publickey)" for deploy user

**This is NORMAL** - your key isn't added to deploy user yet.

**Solutions**:
1. Use `ssh root@64.225.17.0` instead (works now)
2. Add your key to deploy user (see "Adding Your Key" section above)
3. Use GitHub Actions for deployments (already works)

### "Permission denied (publickey)" for root user

**This would be UNEXPECTED** - your key is present for root.

**If this happens**:
1. Check if droplet was rebuilt/recreated
2. Check if key was removed from `/root/.ssh/authorized_keys`
3. Use DigitalOcean console to access droplet
4. Re-add your SSH key

### Can't apply Nginx configuration

**Solution**: Use root user
```bash
ssh root@64.225.17.0
# Root has permissions to modify /etc/nginx/
```

---

## 📚 Related Documentation

- **BETA_DEPLOYMENT.md** - Complete deployment workflow
- **SERVER_CHEATSHEET.md** - Quick command reference
- **SSH_KEY_SETUP.md** - Detailed SSH key setup instructions
- **DEPLOYMENT_LOG.md** - Record of this deployment and SSH discovery
- **.github/workflows/deploy-beta.yml** - GitHub Actions deployment workflow

---

## 🎓 Key Takeaways

1. **Two Users, Two Purposes**:
   - Root: System administration
   - Deploy: Application deployment

2. **Your SSH Key Status**:
   - ✅ Works for root user
   - ❌ Not added to deploy user
   - ✅ Added to GitHub for git operations

3. **GitHub Actions Uses Different Key**:
   - Stored in repository secrets
   - Only for deploy user
   - Separate from your personal key

4. **When to Use What**:
   - Infrastructure changes: `ssh root@64.225.17.0`
   - Code deployments: GitHub Actions (or `ssh deploy@...` if key added)
   - Emergency access: `ssh root@64.225.17.0` always available

5. **Current Setup is Functional**:
   - ✅ You have root access (sufficient for everything)
   - ✅ GitHub Actions has deploy access (automated deployments)
   - 🔄 Adding your key to deploy user is optional convenience

---

**Last Updated**: 2025-10-12
**Discovered During**: /app/ prefix architecture deployment
**Status**: Documented and understood ✅
