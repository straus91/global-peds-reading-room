# 🚀 Deployment Configuration Templates

**Document Created**: 2025-01-11
**Purpose**: Ready-to-use configuration files for deploying Global Peds Reading Room to production

---

## 📁 Docker Configuration

### Dockerfile (Backend)

Create this file at: `backend/Dockerfile`

```dockerfile
FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /code/

# Collect static files
RUN python manage.py collectstatic --noinput

# Run gunicorn
CMD ["gunicorn", "globalpeds_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

### docker-compose.yml

Create this file at project root: `docker-compose.yml`

```yaml
version: '3.8'

services:
  db:
    image: postgres:13
    container_name: globalpeds_db
    environment:
      - POSTGRES_DB=globalpeds_production
      - POSTGRES_USER=globalpeds_app
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - globalpeds_network
    restart: unless-stopped

  redis:
    image: redis:alpine
    container_name: globalpeds_redis
    ports:
      - "6379:6379"
    networks:
      - globalpeds_network
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: globalpeds_backend
    command: gunicorn globalpeds_project.wsgi:application --bind 0.0.0.0:8000 --workers 3
    volumes:
      - ./backend:/code
      - static_volume:/code/static
      - media_volume:/code/media
    env_file:
      - ./backend/.env.production
    depends_on:
      - db
      - redis
    networks:
      - globalpeds_network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: globalpeds_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/conf.d:/etc/nginx/conf.d
      - static_volume:/static
      - media_volume:/media
      - ./frontend:/usr/share/nginx/html
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
    networks:
      - globalpeds_network
    restart: unless-stopped

volumes:
  postgres_data:
  static_volume:
  media_volume:

networks:
  globalpeds_network:
    driver: bridge
```

---

## 🔧 Nginx Configuration

### nginx.conf

Create this file at: `nginx/nginx.conf`

```nginx
user nginx;
worker_processes auto;

error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip Settings
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss
               application/rss+xml application/atom+xml image/svg+xml
               text/x-js text/x-cross-domain-policy application/x-font-ttf
               application/x-font-opentype application/vnd.ms-fontobject
               image/x-icon;

    include /etc/nginx/conf.d/*.conf;
}
```

### nginx/conf.d/globalpeds.conf

Create this file at: `nginx/conf.d/globalpeds.conf`

```nginx
upstream backend {
    server backend:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name globalpeds.example.com www.globalpeds.example.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name globalpeds.example.com www.globalpeds.example.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Client body size limit (for file uploads)
    client_max_body_size 100M;

    # Frontend static files
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # Django static files
    location /static/ {
        alias /static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Django media files
    location /media/ {
        alias /media/;
        expires 30d;
    }

    # Django API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Django Admin
    location /admin/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Rate limiting for API endpoints
    location /api/auth/login/ {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health/ {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/s;
```

---

## 🔐 Environment Configuration

### .env.production

Create this file at: `backend/.env.production`

```env
# ==============================================================================
# PRODUCTION ENVIRONMENT CONFIGURATION
# ==============================================================================

# Django Settings
SECRET_KEY=<GENERATE-NEW-50+-CHAR-KEY-HERE>
DEBUG=False
ALLOWED_HOSTS=globalpeds.example.com,www.globalpeds.example.com

# Database Configuration
DB_NAME=globalpeds_production
DB_USER=globalpeds_app
DB_PASSWORD=<STRONG-16+-CHAR-PASSWORD>
DB_HOST=db
DB_PORT=5432

# Redis Cache
REDIS_URL=redis://redis:6379/0

# Google Gemini API
GEMINI_API_KEY=<YOUR-PRODUCTION-API-KEY>
GEMINI_API_RATE_LIMIT=10

# CORS Configuration
CORS_ALLOWED_ORIGINS=https://globalpeds.example.com,https://www.globalpeds.example.com

# JWT Settings
ACCESS_TOKEN_LIFETIME=30
REFRESH_TOKEN_LIFETIME=7

# Email Configuration (for notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@globalpeds.example.com
EMAIL_HOST_PASSWORD=<APP-SPECIFIC-PASSWORD>

# Static/Media Files
STATIC_URL=/static/
STATIC_ROOT=/code/static/
MEDIA_URL=/media/
MEDIA_ROOT=/code/media/

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Monitoring (optional)
SENTRY_DSN=<YOUR-SENTRY-DSN>
```

---

## 🚀 Deployment Scripts

### deploy.sh

Create this file at project root: `deploy.sh`

```bash
#!/bin/bash

# Global Peds Reading Room - Production Deployment Script
# Usage: ./deploy.sh

set -e

echo "🚀 Starting Global Peds Reading Room deployment..."

# Load environment variables
if [ -f backend/.env.production ]; then
    export $(cat backend/.env.production | grep -v '^#' | xargs)
else
    echo "❌ Error: backend/.env.production not found!"
    exit 1
fi

# Pull latest code
echo "📦 Pulling latest code from repository..."
git pull origin main

# Build Docker images
echo "🔨 Building Docker images..."
docker-compose build

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Start database first
echo "🗄️ Starting database..."
docker-compose up -d db
sleep 10

# Run migrations
echo "📝 Running database migrations..."
docker-compose run --rm backend python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
docker-compose run --rm backend python manage.py collectstatic --noinput

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

# Health check
echo "🏥 Performing health check..."
sleep 10
curl -f http://localhost/health/ || exit 1

echo "✅ Deployment complete!"
echo "📊 View logs: docker-compose logs -f"
echo "🌐 Application available at: https://globalpeds.example.com"
```

### backup.sh

Create this file at project root: `backup.sh`

```bash
#!/bin/bash

# Database Backup Script
# Usage: ./backup.sh

set -e

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/backups"
BACKUP_FILE="$BACKUP_DIR/globalpeds_backup_$TIMESTAMP.sql.gz"

echo "🔒 Starting database backup..."

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Perform backup
docker-compose exec -T db pg_dump -U globalpeds_app globalpeds_production | gzip > $BACKUP_FILE

echo "✅ Backup complete: $BACKUP_FILE"

# Optional: Upload to S3 or other storage
# aws s3 cp $BACKUP_FILE s3://your-backup-bucket/

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "🧹 Old backups cleaned up"
```

---

## 🎯 Production Checklist

### Before Deployment

- [ ] Generate new SECRET_KEY for production
- [ ] Set strong database password (16+ characters)
- [ ] Obtain SSL certificates (Let's Encrypt)
- [ ] Configure domain DNS records
- [ ] Set up email service for notifications
- [ ] Review security settings
- [ ] Test deployment in staging environment

### During Deployment

- [ ] Run database migrations
- [ ] Collect static files
- [ ] Create superuser account
- [ ] Verify SSL certificate installation
- [ ] Test all API endpoints
- [ ] Check frontend functionality

### After Deployment

- [ ] Set up monitoring (Sentry, New Relic, etc.)
- [ ] Configure automated backups
- [ ] Set up log rotation
- [ ] Monitor application performance
- [ ] Review security headers
- [ ] Test disaster recovery procedure

---

## 🔍 Monitoring Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# Check container status
docker-compose ps

# Database shell access
docker-compose exec db psql -U globalpeds_app globalpeds_production

# Django shell access
docker-compose exec backend python manage.py shell

# Run tests
docker-compose exec backend python manage.py test

# Check disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

---

## 🚨 Troubleshooting

### Issue: Database connection refused

```bash
# Check if database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Verify environment variables
docker-compose exec backend env | grep DB_
```

### Issue: Static files not loading

```bash
# Recollect static files
docker-compose exec backend python manage.py collectstatic --noinput

# Check nginx configuration
docker-compose exec nginx nginx -t

# Restart nginx
docker-compose restart nginx
```

### Issue: SSL certificate errors

```bash
# Check certificate validity
openssl x509 -in ssl/cert.pem -text -noout

# Test SSL configuration
openssl s_client -connect globalpeds.example.com:443
```

---

## 📚 Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Let's Encrypt SSL](https://letsencrypt.org/)
- [PostgreSQL Backup](https://www.postgresql.org/docs/current/backup.html)

---

**Document Version**: 1.0
**Last Updated**: 2025-01-11