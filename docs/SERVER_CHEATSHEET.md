# 🖥️ Server Cheatsheet - global-readingroom

**Your Exact Server Configuration**
**Last Updated**: 2025-10-11

> **Quick Copy-Paste Commands** - All paths and IPs are YOUR actual server values

---

## 🔐 SSH Access

```bash
# SSH into server
ssh root@64.225.17.0
```

---

## 📂 Important Paths

```bash
# Application root
cd /home/deploy/global-peds-reading-room

# Backend
cd /home/deploy/global-peds-reading-room/backend

# Virtual environment
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate

# Logs
cd /var/log/gunicorn
cd /var/log/nginx
```

---

## ⚡ Quick Deployment (Copy-Paste)

```bash
# === LOCAL MACHINE ===
cd /mnt/c/Users/strau/Desktop/gr4-gemini
git add -A
git commit -m "Your commit message"
git push origin online_beta

# === ON SERVER ===
ssh root@64.225.17.0
cd /home/deploy/global-peds-reading-room
git pull origin online_beta
source backend/venv/bin/activate
cd backend
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
tail -f /var/log/gunicorn/gunicorn.log
```

---

## 🚨 Emergency Rollback (Copy-Paste)

```bash
ssh root@64.225.17.0
cd /home/deploy/global-peds-reading-room
git reset --hard HEAD~1
sudo systemctl restart gunicorn
curl http://localhost:8001/api/
```

---

## 🔄 Service Management

```bash
# Restart gunicorn
sudo systemctl restart gunicorn

# Check status
sudo systemctl status gunicorn
sudo systemctl status nginx

# View logs
sudo journalctl -u gunicorn.service -n 50
sudo journalctl -u gunicorn.service -f

# Check if running
systemctl is-active gunicorn
systemctl is-active nginx
```

---

## 📊 Logs (Copy-Paste)

```bash
# Real-time gunicorn logs
tail -f /var/log/gunicorn/gunicorn.log

# Real-time nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Last 100 lines
tail -n 100 /var/log/gunicorn/gunicorn.log

# Search for errors
grep -i error /var/log/gunicorn/gunicorn.log | tail -20
```

---

## 🗄️ Database (Copy-Paste)

```bash
# Connect to database
sudo -u postgres psql globalpeds_db

# Backup database
mkdir -p ~/backups
sudo -u postgres pg_dump globalpeds_db > ~/backups/globalpeds_$(date +%Y%m%d_%H%M%S).sql

# Restore database (CAREFUL!)
sudo -u postgres psql globalpeds_db < ~/backups/globalpeds_YYYYMMDD_HHMMSS.sql

# Check database size
sudo -u postgres psql globalpeds_db -c "SELECT pg_size_pretty(pg_database_size('globalpeds_db'));"
```

---

## 🐍 Django Commands (Copy-Paste)

```bash
# Always start with these two commands:
cd /home/deploy/global-peds-reading-room/backend
source /home/deploy/global-peds-reading-room/backend/venv/bin/activate

# Then run any of these:
python manage.py showmigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py shell
python manage.py test
python manage.py check
```

---

## 🧪 Testing (Copy-Paste)

```bash
# Test gunicorn directly
curl http://localhost:8001/api/

# Test through nginx
curl http://localhost/api/

# Test from your computer
curl http://64.225.17.0/api/

# Test in browser
http://64.225.17.0/login.html
```

---

## 🔍 Troubleshooting (Copy-Paste)

### Gunicorn Not Running

```bash
# Check status
sudo systemctl status gunicorn

# Start it
sudo systemctl start gunicorn

# View recent errors
sudo journalctl -u gunicorn.service -n 50
```

### Database Connection Error

```bash
# Check postgres is running
sudo systemctl status postgresql

# Try connecting
sudo -u postgres psql globalpeds_db

# Check env vars
cat /home/deploy/global-peds-reading-room/backend/.env | grep DB_
```

### Nginx Issues

```bash
# Test nginx config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

# Check nginx logs
tail -f /var/log/nginx/error.log
```

### Out of Disk Space

```bash
# Check disk usage
df -h

# Find large files
du -h /var/log | sort -rh | head -10

# Clean old logs
sudo find /var/log -name "*.log.*" -mtime +7 -delete
```

---

## 📈 Monitoring (Copy-Paste)

```bash
# Check running processes
ps aux | grep gunicorn
ps aux | grep nginx

# Check system resources
df -h          # Disk space
free -m        # Memory
top            # CPU/Memory usage

# Check port usage
sudo lsof -i :8001  # Gunicorn
sudo lsof -i :80    # Nginx
```

---

## 🔑 Configuration

**IP Address**: 64.225.17.0
**Hostname**: global-readingroom
**App Directory**: /home/deploy/global-peds-reading-room
**Virtual Env**: /home/deploy/global-peds-reading-room/backend/venv
**Database**: globalpeds_db (owner: straus91)
**Gunicorn**: 3 workers on 127.0.0.1:8001 (systemd service)
**Nginx**: Reverse proxy on port 80 (systemd service)
**Logs**: /var/log/gunicorn/, /var/log/nginx/
**Process Owner**: deploy user
**SSH User**: root

---

## 📝 Common Workflows

### Full Deployment with Migration

```bash
ssh root@64.225.17.0
cd /home/deploy/global-peds-reading-room
mkdir -p ~/backups
sudo -u postgres pg_dump globalpeds_db > ~/backups/globalpeds_$(date +%Y%m%d_%H%M%S).sql
git pull origin online_beta
source backend/venv/bin/activate
pip install -r backend/requirements.txt
cd backend
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
tail -f /var/log/gunicorn/gunicorn.log
```

### Quick Fix Deploy (No Migration)

```bash
ssh root@64.225.17.0
cd /home/deploy/global-peds-reading-room
git pull origin online_beta
sudo systemctl restart gunicorn
```

### View Recent Activity

```bash
ssh root@64.225.17.0
tail -n 50 /var/log/gunicorn/gunicorn.log
tail -n 50 /var/log/nginx/access.log | grep -v "GET /static"
sudo journalctl -u gunicorn.service -n 50
```

---

## 🆘 Emergency Contacts

**If everything is broken**:
1. Check logs: `/var/log/gunicorn/gunicorn.log`
2. Restart services: `sudo systemctl restart gunicorn nginx`
3. Rollback: `git reset --hard HEAD~1 && sudo systemctl restart gunicorn`
4. Restore DB: `sudo -u postgres psql globalpeds_db < ~/backups/latest.sql`

**Full docs**: See `docs/BETA_DEPLOYMENT.md` and `docs/QUICK_REFERENCE.md`

---

**💡 Tip**: Bookmark this file or keep it open in a tab during deployments!

**Last Updated**: 2025-10-11
**Server**: global-readingroom (64.225.17.0)
