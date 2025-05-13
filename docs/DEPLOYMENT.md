# Deployment Guide

## Production Checklist

### Security
- [ ] Set DEBUG = False
- [ ] Update SECRET_KEY
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up HTTPS
- [ ] Configure CORS properly

### Database
- [ ] Set up production PostgreSQL
- [ ] Run migrations
- [ ] Create admin user
- [ ] Backup strategy

### Static Files
- [ ] Configure static file serving
- [ ] Set up CDN if needed
- [ ] Minify CSS/JS

### Environment
- [ ] Create .env file
- [ ] Set environment variables
- [ ] Configure logging

## Basic Deployment Steps

1. Clone repository
2. Set up virtual environment
3. Install dependencies
4. Configure environment variables
5. Run migrations
6. Collect static files
7. Set up web server (Nginx/Apache)
8. Configure WSGI server (Gunicorn)
9. Set up SSL certificate
10. Start services
