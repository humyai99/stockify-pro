# 🚀 Stockify Pro - Debian/Apache2 Deployment Guide

Complete guide to deploy Stockify Pro on a Debian server with Apache2 + mod_wsgi.

---

## 📋 Prerequisites

- Debian 11/12 Server
- Root or sudo access
- Domain name (optional, can use IP)

---

## 🛠️ Step 1: Install Required Packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y apache2 libapache2-mod-wsgi-py3 python3-pip python3-venv git
```

---

## 📁 Step 2: Setup Project Directory

```bash
# Create directory
sudo mkdir -p /var/www/stockify
sudo chown -R $USER:$USER /var/www/stockify
cd /var/www/stockify

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask yfinance pandas numpy requests
```

---

## 📦 Step 3: Upload Your Files

Upload all project files to `/var/www/stockify/`:

```
/var/www/stockify/
├── server.py          # Flask backend
├── stockify.wsgi      # WSGI entry point
├── index.html         # Main page
├── heatmap.html       # Heatmap page
├── trends.html        # Trends page
├── compare.html       # Compare page (if created)
├── css/
│   └── style.css
├── js/
│   ├── app.js
│   └── core/
│       ├── analyst.js
│       ├── i18n.js
│       ├── portfolio.js
│       └── watchlist.js
└── venv/              # Virtual environment
```

**Using SCP from Windows:**
```powershell
scp -r d:\stock\* user@your-server:/var/www/stockify/
```

---

## 🔧 Step 4: Create WSGI File

Create `/var/www/stockify/stockify.wsgi`:

```python
import sys
import os

# Add project to path
sys.path.insert(0, '/var/www/stockify')

# Activate virtual environment
activate_this = '/var/www/stockify/venv/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})

# Import Flask app
from server import app as application
```

---

## ⚙️ Step 5: Configure Apache Virtual Host

Create `/etc/apache2/sites-available/stockify.conf`:

```bash
sudo nano /etc/apache2/sites-available/stockify.conf
```

Paste this configuration:

```apache
<VirtualHost *:80>
    ServerName your-domain.com
    ServerAdmin admin@your-domain.com

    # WSGI Configuration
    WSGIDaemonProcess stockify python-home=/var/www/stockify/venv python-path=/var/www/stockify
    WSGIProcessGroup stockify
    WSGIApplicationGroup %{GLOBAL}

    # API Routes (Flask Backend)
    WSGIScriptAlias /api /var/www/stockify/stockify.wsgi

    # Static Files (HTML, CSS, JS)
    DocumentRoot /var/www/stockify

    <Directory /var/www/stockify>
        Require all granted
        Options -Indexes +FollowSymLinks
        AllowOverride None
    </Directory>

    # WSGI Directory
    <Directory /var/www/stockify>
        <Files stockify.wsgi>
            Require all granted
        </Files>
    </Directory>

    # Logs
    ErrorLog ${APACHE_LOG_DIR}/stockify_error.log
    CustomLog ${APACHE_LOG_DIR}/stockify_access.log combined
</VirtualHost>
```

> **⚠️ Replace `your-domain.com` with your actual domain or server IP!**

---

## 🔐 Step 6: Set Permissions

```bash
sudo chown -R www-data:www-data /var/www/stockify
sudo chmod -R 755 /var/www/stockify
```

---

## ✅ Step 7: Enable Site & Restart Apache

```bash
# Enable required modules
sudo a2enmod wsgi
sudo a2enmod rewrite

# Disable default site (optional)
sudo a2dissite 000-default.conf

# Enable Stockify site
sudo a2ensite stockify.conf

# Test configuration
sudo apache2ctl configtest

# Restart Apache
sudo systemctl restart apache2
```

---

## 🔄 Step 8: Update Frontend API URLs

**IMPORTANT:** Change all API calls from `localhost:5000` to `/api`.

In `js/app.js`, `js/core/*.js`, and all HTML files:

```javascript
// ❌ Before (localhost development)
fetch('http://localhost:5000/analyze/AAPL')

// ✅ After (production)
fetch('/api/analyze/AAPL')
```

**Quick find & replace in your files:**
- Replace: `http://localhost:5000`
- With: `/api`

---

## 🧪 Step 9: Test Your Deployment

1. **Check Apache status:**
   ```bash
   sudo systemctl status apache2
   ```

2. **Test in browser:**
   - Homepage: `http://your-server-ip/`
   - API Test: `http://your-server-ip/api/analyze/AAPL`

3. **If errors, check logs:**
   ```bash
   sudo tail -100 /var/log/apache2/stockify_error.log
   ```

---

## 🐛 Troubleshooting

### Error: ModuleNotFoundError
```bash
# Activate venv and install missing packages
source /var/www/stockify/venv/bin/activate
pip install flask yfinance pandas numpy requests
```

### Error: Permission Denied
```bash
sudo chown -R www-data:www-data /var/www/stockify
sudo chmod -R 755 /var/www/stockify
```

### Error: 500 Internal Server Error
```bash
sudo tail -50 /var/log/apache2/stockify_error.log
```

### WSGI Not Loading
```bash
# Check if mod_wsgi is installed
sudo a2enmod wsgi
sudo systemctl restart apache2
```

---

## 🔒 Optional: Enable HTTPS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-apache
sudo certbot --apache -d your-domain.com
```

---

## 📝 Quick Commands Reference

| Action | Command |
|--------|---------|
| Restart Apache | `sudo systemctl restart apache2` |
| Reload Apache | `sudo systemctl reload apache2` |
| View Error Logs | `sudo tail -f /var/log/apache2/stockify_error.log` |
| Check Status | `sudo systemctl status apache2` |
| Test Config | `sudo apache2ctl configtest` |

---

**🎉 Your Stockify Pro is now live on production!**
