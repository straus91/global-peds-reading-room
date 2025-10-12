#!/bin/bash
#
# Beta Deployment Script (Backup Manual Option)
#
# This script provides a manual deployment alternative to GitHub Actions.
# Use when you need to deploy directly from the droplet or if GitHub Actions is unavailable.
#
# Usage:
#   ./scripts/deploy_beta.sh
#
# Aligns with:
# - BETA_DEPLOYMENT.md - Step-by-step deployment process
# - BETA_BEST_PRACTICES.md - Safety-first deployment methodology
#

set -e  # Exit on error

echo "🚀 Starting Beta Deployment..."
echo "Server: $(hostname)"
echo "Time: $(date)"
echo ""

# Ensure we're in the project directory
cd /home/deploy/global-peds-reading-room

# Show current branch and commit
echo "📍 Current state:"
git branch --show-current
git log -1 --oneline
echo ""

# Pull latest code
echo "📥 Pulling latest code from online_beta..."
git pull origin online_beta

# Show new commit after pull
echo ""
echo "📍 Deployed commit:"
git log -1 --oneline
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source backend/venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -q -r backend/requirements.txt

# Run database migrations
echo "🗄️ Running migrations..."
python backend/manage.py migrate --noinput

# Collect static files (if needed)
echo "📁 Collecting static files..."
python backend/manage.py collectstatic --noinput || true

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Wait for services to stabilize
echo "⏳ Waiting for services to stabilize..."
sleep 3

# Check service status
echo ""
echo "✅ Service Status:"
gunicorn_status=$(systemctl is-active gunicorn)
nginx_status=$(systemctl is-active nginx)
postgres_status=$(systemctl is-active postgresql)

echo "  Gunicorn: $gunicorn_status"
echo "  Nginx: $nginx_status"
echo "  PostgreSQL: $postgres_status"

# Verify all services are running
if [ "$gunicorn_status" != "active" ] || [ "$nginx_status" != "active" ] || [ "$postgres_status" != "active" ]; then
    echo ""
    echo "⚠️ WARNING: Some services are not active!"
    echo "Check logs with:"
    echo "  sudo journalctl -u gunicorn -n 50"
    echo "  sudo journalctl -u nginx -n 50"
    exit 1
fi

# Test API endpoint
echo ""
echo "🔍 Testing API endpoint..."
if curl -f -s http://localhost:8001/api/ > /dev/null; then
    echo "  ✅ API responding on port 8001"
else
    echo "  ⚠️ API not responding - check logs"
    echo "  Run: tail -50 /var/log/gunicorn/gunicorn.log"
fi

# Show recent logs
echo ""
echo "📊 Recent Gunicorn logs (last 20 lines):"
echo "----------------------------------------"
tail -20 /var/log/gunicorn/gunicorn.log

echo ""
echo "=========================================="
echo "🎉 Deployment complete!"
echo "=========================================="
echo ""
echo "🔍 Monitor at: http://64.225.17.0"
echo ""
echo "📋 Next steps (per BETA_BEST_PRACTICES.md):"
echo "  1. Monitor logs for 5-10 minutes"
echo "     tail -f /var/log/gunicorn/gunicorn.log"
echo ""
echo "  2. Test critical features manually:"
echo "     - User login"
echo "     - Case viewing"
echo "     - Report submission"
echo "     - AI feedback generation"
echo ""
echo "  3. Check metrics after 24-48 hours:"
echo "     python scripts/monitor_metrics.py"
echo ""
echo "  4. Compare to baseline (if quality audit):"
echo "     python scripts/track_ai_baseline.py --history"
echo ""
echo "=========================================="
