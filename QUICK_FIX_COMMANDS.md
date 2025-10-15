# ⚡ QUICK FIX: Copy-Paste Commands

**Problem**: 401 API errors & 404 frontend errors
**Cause**: Missing `.env` file on production server
**Fix Time**: 10 minutes

---

## 🚀 Option 1: Using SSH (If You Have SSH Key)

### On Your Local Machine (WSL/Terminal):

```bash
# Copy .env file to droplet
scp backend/.env.production root@64.225.17.0:/tmp/env_production
```

### On the Droplet (SSH as root):

```bash
# SSH to droplet
ssh root@64.225.17.0

# Copy commands below (paste into terminal):

# Move .env to correct location
sudo mv /tmp/env_production /home/deploy/global-peds-reading-room/backend/.env

# Set permissions
sudo chown deploy:deploy /home/deploy/global-peds-reading-room/backend/.env
sudo chmod 600 /home/deploy/global-peds-reading-room/backend/.env

# Verify migration applied
cd /home/deploy/global-peds-reading-room/backend
source venv/bin/activate
python manage.py showmigrations cases | tail -5
python manage.py migrate  # Only if 0009_phase1_foundation is not [X]

# Restart services
sudo systemctl restart gunicorn nginx

# Test
curl -I http://64.225.17.0/api/
```

---

## 🖥️ Option 2: Using DigitalOcean Console (No SSH Key Needed)

### Access Console:
1. Go to https://cloud.digitalocean.com/
2. Droplets → global-readingroom → Access → Launch Droplet Console
3. Login as `root`

### Run These Commands:

```bash
# Navigate to project
cd /home/deploy/global-peds-reading-room/backend

# Backup existing .env (if any)
cp .env .env.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# Create new .env file
cat > .env << 'EOF'
SECRET_KEY=fov8yh0cj=j%%x#pwk8r6fbuh4jjg&=#+5p5l^%=te!q3-k36@
DEBUG=False
ALLOWED_HOSTS=64.225.17.0,localhost,127.0.0.1
DB_NAME=globalpeds_db
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
CORS_ALLOWED_ORIGINS=http://64.225.17.0
ACCESS_TOKEN_LIFETIME=60
REFRESH_TOKEN_LIFETIME=7
GEMINI_API_KEY=AIzaSyBozAbFqUCWws_dpkGIK4-sA91lOny0404
GEMINI_API_RATE_LIMIT=10
EOF

# Set permissions
chown deploy:deploy .env
chmod 600 .env

# Verify migration
source venv/bin/activate
python manage.py migrate

# Restart services
sudo systemctl restart gunicorn nginx

# Test
curl -I http://64.225.17.0/api/
```

---

## ✅ Expected Results After Fix

### Test 1: API responds (not 404)
```bash
curl -I http://64.225.17.0/api/
```
**Expected**: `HTTP/1.1 401 Unauthorized` OR `HTTP/1.1 200 OK`
**Not**: `HTTP/1.1 404 Not Found`

### Test 2: Frontend loads
Open in browser: `http://64.225.17.0/app/`
**Expected**: Page loads, no CORS errors in console (F12)

### Test 3: Services running
```bash
systemctl status gunicorn nginx postgresql
```
**Expected**: All show `active (running)` in green

---

## 🐛 If Still Not Working

### Check logs:
```bash
# Gunicorn errors
sudo tail -50 /var/log/gunicorn/gunicorn.log

# Nginx errors
sudo tail -50 /var/log/nginx/globalpeds_error.log
```

### Verify .env loaded:
```bash
cd /home/deploy/global-peds-reading-room/backend
source venv/bin/activate
python manage.py shell -c "import os; print('ALLOWED_HOSTS:', os.environ.get('ALLOWED_HOSTS'))"
```
**Expected**: Should print `ALLOWED_HOSTS: 64.225.17.0,localhost,127.0.0.1`

### Force restart:
```bash
sudo systemctl stop gunicorn
sudo systemctl start gunicorn
sudo systemctl status gunicorn
```

---

## 📋 Quick Checklist

- [ ] `.env` file created at `/home/deploy/global-peds-reading-room/backend/.env`
- [ ] File permissions: `600` (owner read/write only)
- [ ] File ownership: `deploy:deploy`
- [ ] Migration `0009_phase1_foundation` applied (checked `[X]`)
- [ ] Gunicorn restarted
- [ ] Nginx restarted
- [ ] API returns 401 or 200 (not 404)
- [ ] Frontend loads without CORS errors

---

**Full Details**: See `FIX_401_404_DEPLOYMENT_GUIDE.md`
