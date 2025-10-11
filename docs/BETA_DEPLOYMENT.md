# 🧪 Beta Droplet Deployment Guide

**Last Updated**: 2025-10-11
**Environment**: DigitalOcean Droplet (Production-like Beta)
**Branch**: `online_beta`

---

## 🎯 Overview

This document describes the **actual deployment setup** for the Global Peds Reading Room beta environment running on a DigitalOcean droplet. This is **not** using Docker or App Platform - it's a manual deployment with direct process management.

**Purpose of Beta**: Test new features, AI improvements, and changes in a production-like environment before deploying to main production.

---

## 🖥️ Droplet Configuration

### Server Specifications

- **Provider**: DigitalOcean
- **Hostname**: global-readingroom
- **IP Address**: 64.225.17.0
- **Domain**: None (using IP directly)
- **OS**: Ubuntu (systemd-based)
- **Region**: [Check DigitalOcean dashboard for region]
- **Plan**: [Check DigitalOcean dashboard for specs]

### Installed Services
- **Web Server**: Nginx (systemd service)
- **WSGI Server**: Gunicorn 23.0.0 (3 workers, port 8001)
- **Database**: PostgreSQL (database: globalpeds_db, owner: straus91)
- **Python Version**: 3.x (in virtual environment)
- **Process Manager**: systemd (gunicorn.service)

---

## 🔑 Access & Authentication

### SSH Access

```bash
# SSH into droplet
ssh root@64.225.17.0

# If you set up SSH keys, use:
ssh -i ~/.ssh/your_key root@64.225.17.0
```

### Important Directories

```bash
# Application directory
cd /home/deploy/global-peds-reading-room

# Backend directory
cd /home/deploy/global-peds-reading-room/backend

# Virtual environment
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate

# Logs locations
cd /var/log/gunicorn    # Application logs (owned by deploy user)
cd /var/log/nginx       # Web server logs
```

---

## 🚀 Deployment Workflow

### Pre-Deployment Checklist

- [ ] **Local testing complete** - All changes tested locally
- [ ] **Tests passing** - Run `python manage.py test` locally
- [ ] **Database migrations created** (if needed) - `python manage.py makemigrations`
- [ ] **Committed to git** - All changes committed
- [ ] **Risk assessment** - Reviewed @.claude/docs/RISK_ASSESSMENT.md if making significant changes
- [ ] **Backup current state** - Database backup taken (see below)

### Step-by-Step Deployment

#### 1. Create Database Backup (CRITICAL)

**Always backup before deployment!**

```bash
# SSH into droplet
ssh root@64.225.17.0

# Create backup directory if it doesn't exist
mkdir -p ~/backups

# Backup database with timestamp (as postgres or straus91 user)
sudo -u postgres pg_dump globalpeds_db > ~/backups/globalpeds_$(date +%Y%m%d_%H%M%S).sql

# Verify backup was created
ls -lh ~/backups/

# Optional: Compress backup
gzip ~/backups/globalpeds_$(date +%Y%m%d_%H%M%S).sql
```

**Keep at least 7 days of backups**

#### 2. Push Changes to GitHub

```bash
# On your local machine
cd /mnt/c/Users/strau/Desktop/gr4-gemini

# Ensure you're on online_beta branch
git branch  # Should show * online_beta

# Add and commit changes
git add -A
git commit -m "Descriptive commit message"

# Push to GitHub
git push origin online_beta
```

#### 3. Pull Changes on Droplet

```bash
# SSH into droplet
ssh root@64.225.17.0

# Navigate to application directory
cd /home/deploy/global-peds-reading-room

# Pull latest changes
git pull origin online_beta

# Check what changed
git log -1 --stat
```

#### 4. Update Dependencies (if requirements.txt changed)

```bash
# Activate virtual environment
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate

# Update Python packages
pip install -r backend/requirements.txt

# Verify installation
pip list
```

#### 5. Run Database Migrations (if models changed)

```bash
# Activate virtual environment if not already
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate

# Navigate to backend
cd /home/deploy/global-peds-reading-room/backend

# Check for pending migrations
python manage.py showmigrations

# Run migrations
python manage.py migrate

# Verify migrations applied
python manage.py showmigrations | grep -E "\[X\]"
```

#### 6. Collect Static Files (if frontend/CSS/JS changed)

```bash
# Still in backend directory
python manage.py collectstatic --noinput

# Verify static files collected
ls -la static/  # Or wherever STATIC_ROOT points
```

#### 7. Restart Services

**Using systemd (your current setup)**:

```bash
# Restart gunicorn service
sudo systemctl restart gunicorn

# Check status
sudo systemctl status gunicorn

# Restart nginx if needed (rare)
sudo systemctl restart nginx
sudo systemctl status nginx
```

**Verify services are running**:

```bash
# Check gunicorn
systemctl is-active gunicorn

# Check nginx
systemctl is-active nginx

# View recent gunicorn logs
sudo journalctl -u gunicorn.service -n 50
```

#### 8. Health Checks

```bash
# Check if application is responding (Gunicorn runs on 8001)
curl http://localhost:8001/api/

# Check if Nginx is proxying correctly
curl http://localhost/api/

# Check if database is accessible
sudo -u postgres psql globalpeds_db
# Then in psql:
# \dt  -- list tables
# \q   -- quit

# Check logs for errors
tail -f /var/log/gunicorn/gunicorn.log
tail -f /var/log/nginx/error.log
```

#### 9. Frontend Verification

```bash
# Test from your local machine
curl http://64.225.17.0/

# Or visit in browser
# http://64.225.17.0/login.html
```

#### 10. Post-Deployment Verification

- [ ] **Login works** - Can login as test user
- [ ] **Cases load** - Case list displays correctly
- [ ] **AI feedback works** - Submit test report and request feedback
- [ ] **No errors in logs** - Check gunicorn and nginx logs
- [ ] **Database queries working** - Test critical functionality

---

## 🔄 Rollback Procedure

If deployment fails or causes issues:

### Quick Rollback (Code Only)

```bash
# SSH into droplet
ssh root@64.225.17.0

# Navigate to application directory
cd /home/deploy/global-peds-reading-room

# Check recent commits
git log --oneline -5

# Rollback to previous commit
git reset --hard HEAD~1
# Or rollback to specific commit
git reset --hard COMMIT_HASH

# Restart services
sudo systemctl restart gunicorn

# Verify rollback worked
curl http://localhost:8001/api/
curl http://localhost/api/
```

### Full Rollback (with Database)

```bash
# Stop application
sudo systemctl stop gunicorn

# Rollback database (if migrations were run)
# First, identify migration to rollback to
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate
cd /home/deploy/global-peds-reading-room/backend
python manage.py showmigrations cases
# Then rollback
python manage.py migrate cases 0XXX_previous_migration_name

# Restore database from backup if needed
sudo -u postgres psql globalpeds_db < ~/backups/globalpeds_YYYYMMDD_HHMMSS.sql

# Rollback code
cd /home/deploy/global-peds-reading-room
git reset --hard PREVIOUS_COMMIT_HASH

# Restart application
sudo systemctl start gunicorn
```

---

## 🔐 Environment Variables

### Location

Environment variables are stored in: `/home/deploy/global-peds-reading-room/backend/.env`

### Critical Variables for Beta

```bash
# Django Settings
SECRET_KEY=[Different from production!]
DEBUG=False  # Use False in beta for production-like behavior
ALLOWED_HOSTS=64.225.17.0,localhost,127.0.0.1

# Database
DB_NAME=globalpeds_db
DB_USER=straus91
DB_PASSWORD=[Your database password]
DB_HOST=localhost
DB_PORT=5432

# Gemini API
GEMINI_API_KEY=[Your API key]
GEMINI_API_RATE_LIMIT=10

# CORS
CORS_ALLOWED_ORIGINS=http://64.225.17.0

# JWT
ACCESS_TOKEN_LIFETIME=30
REFRESH_TOKEN_LIFETIME=7
```

### Updating Environment Variables

```bash
# Edit .env file
nano /home/deploy/global-peds-reading-room/backend/.env

# After editing, restart services
sudo systemctl restart gunicorn
```

---

## 📊 Monitoring & Logs

### Viewing Logs

```bash
# Gunicorn logs
tail -f /var/log/gunicorn/gunicorn.log
ls -la /var/log/gunicorn/

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# System logs (for gunicorn service)
sudo journalctl -u gunicorn.service -f
sudo journalctl -u gunicorn.service -n 100

# Nginx system logs
sudo journalctl -u nginx.service -f
```

### Checking Service Status

```bash
# Check gunicorn (systemd)
sudo systemctl status gunicorn
systemctl is-active gunicorn

# Check nginx
sudo systemctl status nginx
systemctl is-active nginx

# Check PostgreSQL
sudo systemctl status postgresql

# Check disk space
df -h

# Check memory usage
free -m

# Check running processes
ps aux | grep gunicorn
ps aux | grep nginx
ps aux | grep postgres
```

### Common Log Locations

```bash
/var/log/gunicorn/          # Application logs (owned by deploy user)
/var/log/nginx/access.log   # Nginx access logs
/var/log/nginx/error.log    # Nginx error logs
/var/log/postgresql/        # Database logs
```

---

## 🚨 Troubleshooting

### Issue: Application Not Responding

```bash
# Check if gunicorn is running
ps aux | grep gunicorn

# Check if port 8000 is in use
sudo lsof -i :8000

# Restart gunicorn
sudo systemctl restart gunicorn

# Check for errors
sudo journalctl -u gunicorn.service -n 50
```

### Issue: Database Connection Error

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
psql -U globalpeds_user -d globalpeds_db -h localhost

# Check database credentials in .env
cat /var/www/gr4-gemini/backend/.env | grep DB_
```

### Issue: Static Files Not Loading

```bash
# Recollect static files
cd /var/www/gr4-gemini/backend
python manage.py collectstatic --noinput

# Check nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### Issue: AI Feedback Not Working

```bash
# Check Gemini API key is set
echo $GEMINI_API_KEY
# Or check .env
grep GEMINI_API_KEY /var/www/gr4-gemini/backend/.env

# Check API logs
tail -f /var/log/globalpeds/django.log | grep -i gemini

# Test Gemini API directly
python manage.py shell
>>> import os
>>> os.environ.get('GEMINI_API_KEY')
>>> # Should print your API key
```

### Issue: Out of Disk Space

```bash
# Check disk usage
df -h

# Find large files
du -h /var/log | sort -rh | head -10

# Clean old logs
sudo find /var/log -name "*.log" -mtime +7 -delete

# Clean old backups
find ~/backups -name "*.sql*" -mtime +7 -delete

# Django sessions cleanup (if using database sessions)
python manage.py clearsessions
```

---

## 🔒 Security Considerations

### SSH Key-Based Authentication

**Recommended**: Disable password authentication, use SSH keys only

```bash
# Copy your SSH public key to droplet
ssh-copy-id root@YOUR_DROPLET_IP

# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Set:
# PasswordAuthentication no
# PermitRootLogin prohibit-password

# Restart SSH
sudo systemctl restart sshd
```

### Firewall Configuration

```bash
# Check firewall status
sudo ufw status

# Recommended rules
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### Keep System Updated

```bash
# Update packages regularly
sudo apt update
sudo apt upgrade -y

# Set up automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

---

## 📋 Regular Maintenance Tasks

### Daily
- [ ] Check application logs for errors
- [ ] Verify AI feedback is working
- [ ] Monitor disk space

### Weekly
- [ ] Create database backup
- [ ] Review error logs
- [ ] Check for system updates
- [ ] Test critical functionality

### Monthly
- [ ] Rotate old logs
- [ ] Clean old backups (keep last 30 days)
- [ ] Review and update dependencies
- [ ] Security audit

---

## 📚 Related Documentation

- **Quick commands**: See `QUICK_REFERENCE.md`
- **Testing workflow**: See `BETA_TESTING_WORKFLOW.md`
- **Monitoring setup**: See `MONITORING_SETUP.md`
- **AI improvements**: See `AI_ITERATION_WORKFLOW.md`
- **Risk assessment**: See `.claude/docs/RISK_ASSESSMENT.md`

---

## ✅ Post-Deployment Checklist

After every deployment, verify:

- [ ] Application loads without errors
- [ ] Login functionality works
- [ ] Case list displays correctly
- [ ] Can view case details
- [ ] Can submit reports
- [ ] AI feedback generates successfully
- [ ] No errors in server logs
- [ ] Database queries executing normally
- [ ] Static files loading correctly
- [ ] Admin panel accessible

---

## 📞 Emergency Contacts

**If Something Breaks**:
1. Check logs (see Monitoring & Logs section)
2. Attempt rollback (see Rollback Procedure)
3. Restore from backup if needed
4. Document what happened for future reference

**Support Resources**:
- DigitalOcean Support: https://www.digitalocean.com/support
- Django Documentation: https://docs.djangoproject.com/
- PostgreSQL Documentation: https://www.postgresql.org/docs/

---

**Remember**: Beta is for testing. It's okay if things break here - that's what it's for! Always test in beta before deploying to production.

**Next Steps**:
1. Fill in the [TO FILL] sections with your actual configuration
2. Test the deployment workflow end-to-end
3. Document any deviations from this process
4. Set up monitoring (see MONITORING_SETUP.md)
