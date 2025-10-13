# 🚀 Deployment Guide - Global Peds Reading Room

## 🎯 Overview

This guide provides comprehensive deployment procedures for the Global Peds Reading Room Beta Droplet. It covers both automated GitHub Actions deployment and manual verification steps.

**⚠️ IMPORTANT**: Always read this guide AND `DEPLOYMENT_LOG.md` before deploying!

---

## 📋 Server Configuration

### Droplet Details

**Environment**: Beta (Testing/Staging)
**IP Address**: `64.225.17.0`
**OS**: Ubuntu (DigitalOcean Droplet)
**Access**: SSH via DigitalOcean console or SSH key

### User Accounts

The server has two user accounts with different purposes:

#### 1️⃣ **deploy** User (Application Operations)
**Purpose**: Runs the Django application, owns application code
**Home Directory**: `/home/deploy`
**Project Path**: `/home/deploy/global-peds-reading-room`
**Virtual Environment**: `/home/deploy/global-peds-reading-room/backend/venv`

**When to use `deploy` user**:
- ✅ Git operations (`git pull`, `git status`)
- ✅ Python operations (`python manage.py migrate`, Django shell)
- ✅ Application verification
- ✅ Virtual environment activation
- ❌ **NOT for** system config changes (Nginx, systemd services)

#### 2️⃣ **root** User (System Administration)
**Purpose**: System-level operations, infrastructure changes
**Access**: Full system privileges

**When to use `root` user**:
- ✅ Nginx configuration changes
- ✅ Service management (`systemctl restart gunicorn`)
- ✅ Package installation (`apt install`)
- ✅ File permission changes (`chown`, `chmod`)
- ❌ **NOT for** application code operations

### Directory Structure

```
/home/deploy/global-peds-reading-room/
├── backend/
│   ├── venv/                    # Python virtual environment
│   ├── manage.py                # Django management script
│   ├── globalpeds_project/      # Django project settings
│   ├── cases/                   # Main Django app
│   ├── users/                   # User management app
│   └── .env                     # Environment variables (NOT in git)
├── frontend/
│   ├── index.html
│   ├── login.html
│   ├── js/
│   └── css/
├── .git/                        # Git repository
└── nginx_app_prefix.conf        # Nginx configuration template
```

### Services Running

| Service | Purpose | Port | Status Command |
|---------|---------|------|----------------|
| **Gunicorn** | Django WSGI server | 8001 | `sudo systemctl status gunicorn` |
| **Nginx** | Web server/reverse proxy | 80 | `sudo systemctl status nginx` |
| **PostgreSQL** | Database | 5432 | `sudo systemctl status postgresql` |

---

## 🔄 Automated Deployment (GitHub Actions)

### How It Works

The project uses GitHub Actions for automated deployment to the Beta Droplet.

**Workflow File**: `.github/workflows/deploy-beta.yml`
**Trigger**: Automatic on push to `online_beta` branch

### What the Workflow Does

1. **Connects**: SSHs to droplet as `deploy` user
2. **Updates Code**: Runs `git pull origin online_beta`
3. **Dependencies**: Installs Python packages (`pip install -r requirements.txt`)
4. **Database**: Runs migrations (`python manage.py migrate`)
5. **Static Files**: Collects static files (`python manage.py collectstatic`)
6. **Services**: Restarts Gunicorn and Nginx

**Duration**: ~2-3 minutes

### Deployment Process

#### Step 1: Commit and Push Changes

```bash
# On your local machine (WSL or Windows)
cd /mnt/c/Users/strau/Desktop/gr4-gemini/backend

# Stage changes
git add <files>

# Commit with descriptive message
git commit -m "Your descriptive commit message

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to online_beta branch
git push origin online_beta
```

#### Step 2: GitHub Actions Deploys Automatically

GitHub Actions will automatically:
- Detect the push to `online_beta`
- Run the deployment workflow
- Deploy to the Beta Droplet

**Check Status**:
1. Go to https://github.com/straus91/global-peds-reading-room
2. Click **Actions** tab
3. See the running/completed workflow
4. ✅ Green checkmark = Success
5. ❌ Red X = Failed (check logs for errors)

#### Step 3: Verify Deployment (Manual)

See "Manual Verification" section below.

---

## 🔍 Manual Verification

After deployment, verify everything works correctly.

### Access the Droplet

**Option A: DigitalOcean Console** (Easiest)
1. Log in to DigitalOcean
2. Go to Droplets → global-readingroom
3. Click "Access" → "Launch Droplet Console"

**Option B: SSH** (If key configured)
```bash
ssh root@64.225.17.0
# or
ssh deploy@64.225.17.0
```

### Verification Checklist

#### 1️⃣ Check Services Running

```bash
# All services should show "active (running)"
sudo systemctl status gunicorn
sudo systemctl status nginx
sudo systemctl status postgresql
```

#### 2️⃣ Verify Code Updated

```bash
# As root, navigate to project
cd /home/deploy/global-peds-reading-room/backend

# Check git status
git log -1
# Should show your latest commit

git status
# Should show "Your branch is up to date with 'origin/online_beta'"
```

#### 3️⃣ Verify Migration Applied

```bash
# Switch to deploy user environment (if logged in as root)
cd /home/deploy/global-peds-reading-room/backend

# Activate virtual environment
source venv/bin/activate

# Check migrations
python manage.py showmigrations | tail -20
# Should show your latest migration with [X] mark

# Alternative: List all migrations
python manage.py migrate --list
```

#### 4️⃣ Verify Models Accessible (If New Models Added)

```bash
# Still in activated venv
python manage.py shell -c "from cases.models import YourNewModel; print('Model accessible')"
```

**Example**:
```bash
python manage.py shell -c "from cases.models import TutoringSession, TutoringTurn; print('Tables exist')"
```

#### 5️⃣ Check Logs for Errors

```bash
# Gunicorn logs
sudo journalctl -u gunicorn -n 50 --no-pager

# Nginx error log
sudo tail -50 /var/log/nginx/globalpeds_error.log

# Nginx access log (last 20 requests)
sudo tail -20 /var/log/nginx/globalpeds_access.log
```

#### 6️⃣ Test API Endpoint (Optional but Recommended)

```bash
# Test health/status of API
curl -I http://64.225.17.0/api/

# If you have a simple GET endpoint, test it
curl http://64.225.17.0/api/cases/ | head -50
```

---

## 🐛 Common Issues & Solutions

### Issue 1: "ModuleNotFoundError: No module named 'django'"

**Symptom**: When running Django commands as root
**Cause**: Not using virtual environment or wrong user

**Solution**:
```bash
# Make sure you're in the right directory
cd /home/deploy/global-peds-reading-room/backend

# Activate virtual environment
source venv/bin/activate

# Now run your command
python manage.py <command>
```

### Issue 2: GitHub Actions Deployment Failed

**Symptom**: Red X on GitHub Actions workflow

**Solution**:
1. Click on the failed workflow in GitHub Actions
2. Read the error log
3. Common causes:
   - **Migration error**: Check migration file syntax
   - **Dependency error**: Missing package in requirements.txt
   - **Merge conflict**: Resolve conflicts before pushing
   - **SSH timeout**: Network issue, try rerunning

### Issue 3: Services Not Restarting

**Symptom**: Changes deployed but old code still running

**Solution**:
```bash
# Manually restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Verify they started successfully
sudo systemctl status gunicorn
sudo systemctl status nginx
```

### Issue 4: Nginx Configuration Change Not Applied

**Symptom**: GitHub Actions doesn't apply Nginx config changes

**Cause**: Workflow doesn't modify system-level config (by design)

**Solution**: Apply Nginx changes manually
```bash
# SSH as root
ssh root@64.225.17.0

# Backup current config
sudo cp /etc/nginx/sites-available/globalpeds \
     /etc/nginx/sites-available/globalpeds.backup.$(date +%Y%m%d_%H%M%S)

# Copy new config from repo
sudo cp /home/deploy/global-peds-reading-room/nginx_app_prefix.conf \
     /etc/nginx/sites-available/globalpeds

# Test config
sudo nginx -t

# Apply
sudo systemctl reload nginx
```

### Issue 5: Can't Access Droplet via SSH

**Symptom**: Permission denied (publickey)

**Solutions**:
- **Option A**: Use DigitalOcean console access (always works)
- **Option B**: Add your SSH key to authorized_keys
  ```bash
  # On droplet (via console)
  cat >> ~/.ssh/authorized_keys
  # Paste your public key, press Ctrl+D
  ```

---

## 📝 Quick Command Reference

### Common Commands as Deploy User

```bash
# Navigate to project
cd /home/deploy/global-peds-reading-room/backend

# Activate venv
source venv/bin/activate

# Check git status
git status
git log -1

# Run migration
python manage.py migrate

# Check migrations
python manage.py showmigrations

# Django shell
python manage.py shell

# Create superuser
python manage.py createsuperuser
```

### Common Commands as Root

```bash
# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Check service status
sudo systemctl status gunicorn nginx postgresql

# View logs
sudo journalctl -u gunicorn -f         # Follow gunicorn logs
sudo tail -f /var/log/nginx/globalpeds_error.log   # Follow nginx errors

# Test Nginx config
sudo nginx -t

# Reload Nginx (after config change)
sudo systemctl reload nginx
```

---

## 🔄 Deployment Workflow Cheatsheet

### For Code-Only Changes (Most Common)

```
1. Make changes locally
2. Write tests (run: python manage.py test)
3. Commit changes
4. Push to online_beta
5. GitHub Actions deploys automatically (2-3 min)
6. Verify deployment (check services, test API)
7. Monitor for 24 hours
8. Document in DEPLOYMENT_LOG.md
```

### For Database Changes (Migrations)

```
1. Make model changes
2. Create migration: python manage.py makemigrations
3. Test migration locally: python manage.py migrate
4. Write tests for new models/fields
5. Commit changes (including migration file)
6. Push to online_beta
7. GitHub Actions runs migration automatically
8. Verify tables created on droplet
9. Document in DEPLOYMENT_LOG.md
```

### For Infrastructure Changes (Nginx, Services)

```
1. Test changes locally (if possible)
2. Create new config file
3. Commit config to repo
4. Push to online_beta
5. GitHub Actions deploys code
6. **Manually apply config as root**
7. Test config: sudo nginx -t
8. Reload service
9. Verify functionality
10. Document in DEPLOYMENT_LOG.md
```

---

## 📚 Related Documentation

### Must-Read Before Deploying

- **DEPLOYMENT_LOG.md** - History of all deployments, lessons learned
- **DEPLOYMENT_STATUS.md** - Current deployment status
- **CLAUDE.md** - Project overview and quick start
- **.claude/docs/RISK_ASSESSMENT.md** - Assess risks before deploying
- **.claude/docs/WORKFLOWS.md** - Safe change workflows

### For Specific Tasks

- **.claude/docs/DATA_MODELS.md** - Database schema and migrations
- **.claude/docs/TESTING.md** - Testing before deployment
- **.claude/docs/SECURITY.md** - Security considerations
- **.claude/docs/PERFORMANCE.md** - Performance optimization

---

## 🎯 Deployment Best Practices

### Before Deploying

- [ ] ✅ Run all tests locally: `python manage.py test`
- [ ] ✅ Test migrations locally: `python manage.py migrate`
- [ ] ✅ Complete risk assessment (see RISK_ASSESSMENT.md)
- [ ] ✅ Read DEPLOYMENT_LOG.md for lessons learned
- [ ] ✅ Ensure commit message is descriptive
- [ ] ✅ Check no sensitive data in commit (API keys, passwords)

### After Deploying

- [ ] ✅ Verify services running
- [ ] ✅ Check logs for errors
- [ ] ✅ Test at least one API endpoint
- [ ] ✅ Monitor for 24 hours
- [ ] ✅ Document in DEPLOYMENT_LOG.md
- [ ] ✅ Update DEPLOYMENT_STATUS.md

### For Critical Changes

- [ ] ✅ Deploy outside peak hours
- [ ] ✅ Notify users of maintenance window
- [ ] ✅ Have rollback plan ready
- [ ] ✅ Monitor closely for first hour
- [ ] ✅ Keep communication channels open

---

## 🚨 Emergency Rollback

If deployment causes issues and you need to rollback:

### Quick Rollback (Code Only)

```bash
# SSH to droplet as deploy user
cd /home/deploy/global-peds-reading-room/backend

# Revert to previous commit
git log -5  # Find previous commit hash
git reset --hard <previous-commit-hash>

# Restart services
sudo systemctl restart gunicorn

# Verify
git log -1
```

### Database Migration Rollback

```bash
# List migrations
python manage.py showmigrations cases

# Rollback to specific migration
python manage.py migrate cases <migration_name>

# Example: Rollback tutoring tables
python manage.py migrate cases 0007_alter_report_unique_together_report_is_archived
```

### Nginx Config Rollback

```bash
# Restore from backup
sudo cp /etc/nginx/sites-available/globalpeds.backup.YYYYMMDD_HHMMSS \
     /etc/nginx/sites-available/globalpeds

# Test
sudo nginx -t

# Apply
sudo systemctl reload nginx
```

---

## 💡 Tips for Future Claude Sessions

### If You're Claude in a New Session

**Always do this FIRST**:
1. Read `DEPLOYMENT_LOG.md` - Understand deployment history and lessons learned
2. Read `DEPLOYMENT_STATUS.md` - Check current deployment status
3. Read this file (`DEPLOYMENT.md`) - Understand server setup

**Key Things to Remember**:
- 🔴 Deployment is **automated via GitHub Actions** (not manual SSH)
- 🔴 Use **deploy user** for app operations, **root** for system operations
- 🔴 Virtual environment is at `/home/deploy/global-peds-reading-room/backend/venv`
- 🔴 Droplet IP: 64.225.17.0
- 🔴 Always test locally before pushing to online_beta

**Don't Assume**:
- ❌ Don't assume manual deployment is needed (GitHub Actions handles it)
- ❌ Don't assume you need SSH key access (DigitalOcean console works)
- ❌ Don't assume root user for Django commands (use deploy user context)

---

## 📞 Support & Troubleshooting

### If Stuck

1. **Check logs first**: Gunicorn and Nginx logs usually reveal the issue
2. **Review DEPLOYMENT_LOG.md**: Similar issues may have been documented
3. **Check GitHub Actions**: Did the workflow actually complete?
4. **Verify services running**: `sudo systemctl status gunicorn nginx postgresql`
5. **Test manually**: SSH in and run commands step by step

### Useful Debugging Commands

```bash
# Check what's listening on port 8001 (Gunicorn)
sudo ss -tlnp | grep 8001

# Check Nginx configuration
sudo nginx -T | grep -A 10 "server {"

# Check Django settings
python manage.py diffsettings

# Check database connection
python manage.py dbshell
\dt  # List tables
\q   # Exit
```

---

**Last Updated**: 2025-10-12
**Maintainer**: straus91
**Environment**: Beta (64.225.17.0)
**For Help**: Refer to DEPLOYMENT_LOG.md for past issues and resolutions
