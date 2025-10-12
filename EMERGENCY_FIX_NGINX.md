# Emergency Fix: Apply Nginx Configuration via DigitalOcean Console

## 🚨 Current Situation

**Your site is broken because:**
- ✅ Code deployed with `/app/` prefix paths (HTML/JS files)
- ❌ Nginx still using old configuration (serves from root `/`)
- ❌ Result: All CSS/JS assets return 404 errors

**This guide will:**
1. Show you how to access the droplet via DigitalOcean web console
2. Apply the nginx_app_prefix.conf configuration
3. Test and verify the site works

---

## Step 1: Access DigitalOcean Droplet Console

### 1.1 Log into DigitalOcean Dashboard
1. Go to: https://cloud.digitalocean.com/
2. Log in with your credentials
3. Click on **"Droplets"** in left sidebar

### 1.2 Access Your Droplet
1. Find your droplet: **64.225.17.0**
2. Click on the droplet name to open details
3. Click **"Access"** tab at the top
4. Click **"Launch Droplet Console"** button (or "Launch Recovery Console" if needed)

**Alternative**: Click the dropdown arrow next to "Access" and select "Console"

### 1.3 Log In
- **Username**: `deploy`
- **Password**: (your deploy user password - if you don't have it, see Section 8: Troubleshooting)

---

## Step 2: Verify Current Nginx Configuration

Once logged into the console:

```bash
# Check current Nginx configuration
sudo cat /etc/nginx/sites-available/globalpeds

# Check if it has /app/ location block
sudo grep -n "location /app/" /etc/nginx/sites-available/globalpeds
```

**Expected Result**: If the grep returns nothing, the new config is NOT applied yet.

---

## Step 3: Backup Current Configuration

**⚠️ CRITICAL: Always backup before making changes!**

```bash
# Create timestamped backup
sudo cp /etc/nginx/sites-available/globalpeds \
     /etc/nginx/sites-available/globalpeds.backup.$(date +%Y%m%d_%H%M%S)

# Verify backup exists
ls -lh /etc/nginx/sites-available/globalpeds.backup*
```

**Expected Output**: You should see a file like `globalpeds.backup.20251012_153045`

---

## Step 4: Upload New Nginx Configuration

You have two options to get `nginx_app_prefix.conf` onto the droplet:

### Option A: Copy-Paste via Console (Easier)

1. **On your local machine**, display the file:
```bash
cat /mnt/c/Users/strau/Desktop/gr4-gemini/nginx_app_prefix.conf
```

2. **Copy all the output** (Ctrl+C)

3. **In the droplet console**, create the file:
```bash
# Create temp file
nano /tmp/nginx_app_prefix.conf

# Paste the configuration (Ctrl+Shift+V or right-click paste)
# Save and exit (Ctrl+X, then Y, then Enter)
```

4. **Move to correct location**:
```bash
sudo mv /tmp/nginx_app_prefix.conf /etc/nginx/sites-available/globalpeds
```

### Option B: Use Git to Get the File (Alternative)

```bash
# Navigate to project directory
cd /home/deploy/global-peds-reading-room

# Ensure latest code is pulled (should already be from GitHub Actions)
git pull origin online_beta

# Copy the nginx config from repository
sudo cp nginx_app_prefix.conf /etc/nginx/sites-available/globalpeds
```

---

## Step 5: Set Correct Permissions

```bash
# Set ownership and permissions
sudo chown root:root /etc/nginx/sites-available/globalpeds
sudo chmod 644 /etc/nginx/sites-available/globalpeds
```

---

## Step 6: Test Nginx Configuration

**⚠️ CRITICAL: Always test before applying!**

```bash
# Test configuration syntax
sudo nginx -t
```

**Expected Output**:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

**If you see errors:**
- Double-check the file was copied correctly
- Verify no syntax errors in the configuration
- Check the path: `/home/deploy/global-peds-reading-room/frontend/` exists
- See Section 8: Troubleshooting

---

## Step 7: Apply Configuration and Restart Services

```bash
# Reload Nginx (graceful reload, no downtime)
sudo systemctl reload nginx

# Check Nginx status
sudo systemctl status nginx

# If status shows errors, restart Nginx
sudo systemctl restart nginx

# Verify all services are running
echo "Service Status:"
echo "  Gunicorn: $(systemctl is-active gunicorn)"
echo "  Nginx: $(systemctl is-active nginx)"
echo "  PostgreSQL: $(systemctl is-active postgresql)"
```

**Expected Output**: All services should show `active`

---

## Step 8: Verify Configuration is Applied

```bash
# Test root redirect (should redirect to /app/)
curl -I http://localhost/

# Should return:
# HTTP/1.1 301 Moved Permanently
# Location: /app/

# Test frontend serving
curl -I http://localhost/app/

# Should return:
# HTTP/1.1 200 OK

# Test API still works
curl http://localhost/api/

# Should return JSON response
```

---

## Step 9: Test from Browser

**Open these URLs in your browser:**

1. **Root URL**: http://64.225.17.0/
   - Should redirect to: http://64.225.17.0/app/

2. **Main Page**: http://64.225.17.0/app/
   - Should load without 404 errors
   - Open DevTools (F12) → Console tab
   - **Verify**: No 404 errors for CSS/JS files

3. **Login Page**: http://64.225.17.0/app/login.html
   - Should load with styling
   - All assets should load (check Network tab)

4. **Admin Dashboard**: http://64.225.17.0/app/admin/dashboard.html
   - Login first if needed
   - Should load without errors
   - Navigation should work

5. **API Test**: http://64.225.17.0/api/
   - Should return JSON (not 404)

6. **Django Admin**: http://64.225.17.0/admin/
   - Should redirect to login
   - Should NOT interfere with /app/admin/

---

## Step 10: Monitor Logs for Issues

```bash
# Monitor Nginx error log in real-time
sudo tail -f /var/log/nginx/globalpeds_error.log

# In another terminal/console window, monitor access log
sudo tail -f /var/log/nginx/globalpeds_access.log

# Check Gunicorn logs
tail -f /var/log/gunicorn/gunicorn.log
```

**What to look for:**
- ❌ Any 404 errors for /app/css/... or /app/js/...
- ❌ Any "file not found" errors
- ❌ Any permission denied errors
- ✅ 200 responses for /app/ paths
- ✅ 301 redirect from / to /app/

---

## Troubleshooting

### Issue 1: Can't Log Into Console with `deploy` User

**Solution**: Use root user or recovery console
1. In DigitalOcean, click **"Access"** → **"Reset Root Password"**
2. Check your email for temporary root password
3. Log in as `root`
4. Then switch to deploy user: `su - deploy`

### Issue 2: `nginx -t` Shows Errors

**Common errors:**

1. **"No such file or directory: /home/deploy/global-peds-reading-room/frontend/"**
   ```bash
   # Verify frontend directory exists
   ls -la /home/deploy/global-peds-reading-room/frontend/

   # If missing, check project was pulled correctly
   cd /home/deploy/global-peds-reading-room
   git status
   ```

2. **"Permission denied"**
   ```bash
   # Fix frontend directory permissions
   sudo chmod -R 755 /home/deploy/global-peds-reading-room/frontend/
   ```

3. **Syntax error in configuration**
   - Re-copy the configuration file carefully
   - Ensure no extra characters or missing semicolons

### Issue 3: Services Won't Restart

```bash
# Check for errors
sudo journalctl -u nginx -n 50
sudo journalctl -u gunicorn -n 50

# Try stopping and starting instead of restart
sudo systemctl stop nginx
sudo systemctl start nginx
```

### Issue 4: Still Getting 404 Errors on /app/ Paths

1. **Verify Nginx reloaded**:
   ```bash
   sudo systemctl status nginx
   # Check "Loaded" and "Active" status
   ```

2. **Check Nginx is using correct config**:
   ```bash
   # Verify symlink exists
   ls -la /etc/nginx/sites-enabled/globalpeds

   # Should point to /etc/nginx/sites-available/globalpeds
   ```

3. **Verify config is correct**:
   ```bash
   # Check location block exists
   sudo grep -A 5 "location /app/" /etc/nginx/sites-available/globalpeds
   ```

4. **Clear browser cache**:
   - Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)

### Issue 5: API Returns 502 Bad Gateway

```bash
# Check if Gunicorn is running
sudo systemctl status gunicorn

# If not running, check logs
sudo journalctl -u gunicorn -n 100

# Restart Gunicorn
sudo systemctl restart gunicorn

# Verify it's listening on port 8001
sudo netstat -tlnp | grep 8001
```

---

## Rollback Procedure (If Something Goes Wrong)

**If the new configuration breaks the site:**

```bash
# Find your backup file
ls -lh /etc/nginx/sites-available/globalpeds.backup*

# Restore the backup (replace YYYYMMDD_HHMMSS with actual timestamp)
sudo cp /etc/nginx/sites-available/globalpeds.backup.YYYYMMDD_HHMMSS \
     /etc/nginx/sites-available/globalpeds

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Verify services
sudo systemctl status nginx
```

**Then investigate the issue before trying again.**

---

## Success Checklist ✅

After completing all steps, verify:

- [ ] Root URL (http://64.225.17.0/) redirects to /app/
- [ ] Main page loads without 404 errors (http://64.225.17.0/app/)
- [ ] Login page loads with styling (http://64.225.17.0/app/login.html)
- [ ] Admin dashboard accessible (http://64.225.17.0/app/admin/dashboard.html)
- [ ] No 404 errors in browser console (F12)
- [ ] API responds (http://64.225.17.0/api/)
- [ ] Django admin accessible (http://64.225.17.0/admin/)
- [ ] All services running: `systemctl is-active nginx gunicorn postgresql`
- [ ] No errors in logs: `tail -50 /var/log/nginx/globalpeds_error.log`

---

## Next Steps After Fix

Once the site is working:

1. **Document this deployment** in your project
2. **Add your SSH key to droplet** (see SSH_KEY_SETUP.md - to be created)
3. **Consider automating Nginx config deployment** via GitHub Actions
4. **Monitor the site for 24 hours** for any issues
5. **Test all critical workflows**:
   - User login/logout
   - Report submission
   - AI feedback generation
   - Admin dashboard operations

---

## Need Help?

If you encounter issues not covered here:

1. **Check logs**:
   ```bash
   sudo tail -100 /var/log/nginx/globalpeds_error.log
   tail -100 /var/log/gunicorn/gunicorn.log
   ```

2. **Verify file structure**:
   ```bash
   ls -la /home/deploy/global-peds-reading-room/frontend/
   ls -la /home/deploy/global-peds-reading-room/frontend/admin/
   ```

3. **Check service status**:
   ```bash
   sudo systemctl status nginx
   sudo systemctl status gunicorn
   sudo systemctl status postgresql
   ```

4. **Collect information**:
   - What error message did you see?
   - What step were you on?
   - What does the Nginx error log show?

---

**Good luck! The site will be working soon. 🚀**
