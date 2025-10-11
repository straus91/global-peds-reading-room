# ⚡ Quick Reference Guide

**For**: Emergency procedures and commonly used commands
**Last Updated**: 2025-10-11

> This is your "panic button" reference. Keep this handy during deployments and troubleshooting.

---

## 🚨 Emergency Rollback

**Something went wrong after deployment? Rollback immediately:**

```bash
# 1. SSH into droplet
ssh root@64.225.17.0

# 2. Navigate to app directory
cd /home/deploy/global-peds-reading-room

# 3. Rollback code to previous commit
git reset --hard HEAD~1

# 4. Restart application
sudo systemctl restart gunicorn

# 5. Check if it's working
curl http://localhost:8001/api/
```

**See full rollback procedure**: `docs/BETA_DEPLOYMENT.md#rollback-procedure`

---

## 🔧 Common Deployment Commands

### Quick Deploy (standard workflow)

```bash
# On LOCAL machine
cd /mnt/c/Users/strau/Desktop/gr4-gemini
git add -A
git commit -m "Your message"
git push origin online_beta

# On DROPLET
ssh root@64.225.17.0
cd /home/deploy/global-peds-reading-room
git pull origin online_beta
source backend/venv/bin/activate
pip install -r backend/requirements.txt  # If deps changed
cd backend
python manage.py migrate  # If models changed
python manage.py collectstatic --noinput  # If frontend changed
sudo systemctl restart gunicorn
tail -f /var/log/gunicorn/gunicorn.log  # Check for errors
```

### Quick Health Check

```bash
# Check if services are running
sudo systemctl status gunicorn
sudo systemctl status nginx
sudo systemctl status postgresql

# Test API endpoint
curl http://localhost:8000/api/

# Check logs for errors
tail -n 50 /var/log/globalpeds/gunicorn.log | grep -i error
```

---

## 📊 Monitoring Commands

### View Real-Time Logs

```bash
# Application logs
tail -f /var/log/gunicorn/gunicorn.log

# Nginx access log
tail -f /var/log/nginx/access.log

# Nginx error log
tail -f /var/log/nginx/error.log

# Filter for errors only
tail -f /var/log/gunicorn/gunicorn.log | grep -i error

# Last 100 lines
tail -n 100 /var/log/gunicorn/gunicorn.log

# Systemd service logs
sudo journalctl -u gunicorn.service -f
sudo journalctl -u nginx.service -f
```

### Check System Resources

```bash
# Disk space
df -h

# Memory usage
free -m

# Top processes by CPU/memory
top
# Or more user-friendly
htop  # If installed

# Check running processes
ps aux | grep gunicorn
ps aux | grep postgres
ps aux | grep nginx
```

---

## 🗄️ Database Commands

### Quick Database Access

```bash
# Connect to database
psql -U globalpeds_user -d globalpeds_db

# Inside psql:
\dt              # List tables
\d cases_case    # Describe table structure
\q               # Quit
```

### Backup Database

```bash
# Create timestamped backup
sudo -u postgres pg_dump globalpeds_db > ~/backups/globalpeds_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
sudo -u postgres pg_dump globalpeds_db | gzip > ~/backups/globalpeds_$(date +%Y%m%d_%H%M%S).sql.gz

# Verify backup exists
ls -lh ~/backups/
```

### Restore Database

```bash
# Restore from backup (CAREFUL!)
sudo -u postgres psql globalpeds_db < ~/backups/globalpeds_YYYYMMDD_HHMMSS.sql

# Or if compressed
gunzip < ~/backups/globalpeds_YYYYMMDD_HHMMSS.sql.gz | sudo -u postgres psql globalpeds_db
```

### Check Database Size

```bash
# Connect to database
sudo -u postgres psql globalpeds_db

# Check database size
SELECT pg_size_pretty(pg_database_size('globalpeds_db'));

# Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

---

## 🔄 Django Management Commands

### Common Django Commands

```bash
# Navigate to backend
cd /home/deploy/global-peds-reading-room/backend

# Activate venv
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate

# Check migrations
python manage.py showmigrations

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Django shell
python manage.py shell

# Run tests
python manage.py test

# Check for issues
python manage.py check

# Clear expired sessions
python manage.py clearsessions
```

### Inspect Models

```bash
# Django shell
python manage.py shell

# Inside shell:
>>> from cases.models import Case, Report, AIFeedbackRating
>>> Case.objects.count()  # Total cases
>>> Report.objects.count()  # Total reports
>>> AIFeedbackRating.objects.count()  # Total ratings
>>>
>>> # Get recent reports
>>> Report.objects.order_by('-submitted_at')[:5]
>>>
>>> # Check AI feedback ratings
>>> from django.db.models import Avg
>>> AIFeedbackRating.objects.aggregate(Avg('star_rating'))
>>>
>>> exit()
```

---

## 🔧 Service Management

### Restart Services

```bash
# Restart gunicorn
sudo systemctl restart gunicorn

# Restart nginx
sudo systemctl restart nginx

# Restart PostgreSQL (careful!)
sudo systemctl restart postgresql

# Restart all at once
sudo systemctl restart gunicorn nginx
```

### Check Service Status

```bash
# Detailed status
sudo systemctl status gunicorn
sudo systemctl status nginx
sudo systemctl status postgresql

# Check if service is active (just yes/no)
sudo systemctl is-active gunicorn

# View recent logs for service
sudo journalctl -u gunicorn.service -n 50

# Follow logs in real-time
sudo journalctl -u gunicorn.service -f
```

### Stop/Start Services

```bash
# Stop service
sudo systemctl stop gunicorn

# Start service
sudo systemctl start gunicorn

# Enable service to start on boot
sudo systemctl enable gunicorn

# Disable service from starting on boot
sudo systemctl disable gunicorn
```

---

## 🐛 Debugging Commands

### Find Errors in Logs

```bash
# Search for errors in gunicorn logs
grep -i error /var/log/globalpeds/gunicorn.log

# Last 100 errors
grep -i error /var/log/globalpeds/gunicorn.log | tail -n 100

# Errors in last hour
find /var/log/globalpeds/ -name "*.log" -mmin -60 -exec grep -i error {} \;

# Count errors by type
grep -i error /var/log/globalpeds/gunicorn.log | sort | uniq -c | sort -rn
```

### Check Port Usage

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Check what's using port 80 (nginx)
sudo lsof -i :80

# Check all listening ports
sudo netstat -tlnp
```

### Network Testing

```bash
# Test if application responds
curl http://localhost:8000/api/

# Test from outside (replace with actual IP)
curl http://YOUR_DROPLET_IP/api/

# Test with headers
curl -I http://localhost:8000/api/

# Test specific endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/cases/
```

---

## 🔐 Security Commands

### Check Failed Login Attempts

```bash
# View failed SSH attempts
sudo grep "Failed password" /var/log/auth.log | tail -n 20

# View successful SSH logins
sudo grep "Accepted password" /var/log/auth.log | tail -n 20
```

### Firewall Status

```bash
# Check firewall status
sudo ufw status verbose

# Add rule
sudo ufw allow 8000/tcp

# Remove rule
sudo ufw delete allow 8000/tcp

# Enable firewall
sudo ufw enable
```

### Update System

```bash
# Update package list
sudo apt update

# Upgrade packages
sudo apt upgrade -y

# Check for security updates
sudo apt list --upgradable
```

---

## 🧪 Testing Commands

### Quick Functionality Test

```bash
# SSH into droplet
ssh root@64.225.17.0

# Activate venv
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate

# Navigate to backend
cd /home/deploy/global-peds-reading-room/backend

# Run specific test
python manage.py test cases.tests.TestCaseModel

# Run all tests
python manage.py test

# Run tests with verbosity
python manage.py test --verbosity=2

# Run tests and keep database
python manage.py test --keepdb
```

### API Testing from Command Line

```bash
# Test Gunicorn directly (on server)
curl http://localhost:8001/api/

# Test through Nginx (on server)
curl http://localhost/api/

# Test from outside (your local machine)
curl http://64.225.17.0/api/

# Test login (replace with actual credentials)
curl -X POST http://64.225.17.0/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}'

# Test with token (replace TOKEN)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://64.225.17.0/api/cases/cases/

# Test AI feedback (replace REPORT_ID and TOKEN)
curl -X POST http://64.225.17.0/api/cases/reports/REPORT_ID/ai-feedback/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📦 Dependency Management

### Update Python Dependencies

```bash
# Activate venv
source /path/to/venv/bin/activate

# Update all packages
pip list --outdated
pip install --upgrade pip
pip install -r backend/requirements.txt --upgrade

# Check installed versions
pip list

# Check specific package
pip show django
```

### Check for Security Vulnerabilities

```bash
# Install safety (if not already)
pip install safety

# Check for vulnerabilities
safety check

# Or use pip-audit
pip install pip-audit
pip-audit
```

---

## 🔍 Git Commands

### Check Current State

```bash
# Current branch
git branch

# Recent commits
git log --oneline -10

# What changed in last commit
git show HEAD

# Diff between local and remote
git fetch
git diff origin/online_beta
```

### Undo Changes

```bash
# Discard local uncommitted changes
git checkout -- filename.py

# Discard all uncommitted changes (CAREFUL!)
git reset --hard HEAD

# Rollback to specific commit
git reset --hard COMMIT_HASH

# Create a revert commit (safer)
git revert COMMIT_HASH
```

---

## 📞 When Things Go Wrong

### Application Won't Start

1. Check logs: `sudo journalctl -u gunicorn.service -n 50`
2. Check if port is in use: `sudo lsof -i :8000`
3. Check syntax: `python manage.py check`
4. Try restarting: `sudo systemctl restart gunicorn`
5. If still failing, rollback code: `git reset --hard HEAD~1`

### Database Connection Error

1. Check PostgreSQL running: `sudo systemctl status postgresql`
2. Test connection: `psql -U globalpeds_user -d globalpeds_db`
3. Check credentials in .env: `cat backend/.env | grep DB_`
4. Restart PostgreSQL: `sudo systemctl restart postgresql`

### Out of Disk Space

1. Check space: `df -h`
2. Find large files: `du -h /var/log | sort -rh | head -10`
3. Clean old logs: `sudo find /var/log -name "*.log" -mtime +7 -delete`
4. Clean old backups: `find ~/backups -mtime +30 -delete`

### Site Not Loading

1. Check nginx: `sudo systemctl status nginx`
2. Test nginx config: `sudo nginx -t`
3. Check nginx error log: `tail -f /var/log/nginx/error.log`
4. Restart nginx: `sudo systemctl restart nginx`

---

## 📚 Documentation Links

- **Full deployment guide**: `docs/BETA_DEPLOYMENT.md`
- **Testing workflow**: `docs/BETA_TESTING_WORKFLOW.md`
- **Monitoring setup**: `docs/MONITORING_SETUP.md`
- **AI improvements**: `docs/AI_ITERATION_WORKFLOW.md`
- **All documentation**: `DOCUMENTATION_INDEX.md`

---

## 💡 Pro Tips

1. **Always backup before making changes** - Takes 5 seconds, saves hours
2. **Test locally first** - Catch issues before they hit beta
3. **Check logs immediately after deployment** - Catch errors early
4. **Keep a terminal with `tail -f` open** - See issues in real-time
5. **Document what you changed** - Future you will thank you
6. **Use tmux/screen** - Don't lose your session if SSH disconnects

```bash
# Start a persistent session
screen -S deploy
# Or
tmux new -s deploy

# Detach: Ctrl+A then D (screen) or Ctrl+B then D (tmux)

# Reattach later
screen -r deploy
# Or
tmux attach -t deploy
```

---

**Remember**: When in doubt, check the logs first. 90% of problems reveal themselves in the logs.

**Need more details?** See the comprehensive `BETA_DEPLOYMENT.md` guide.
