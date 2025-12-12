# How to Deploy Stockify Pro on Debian Server

This guide will help you deploy your application to a Debian (or Ubuntu) Linux server. We will use **Gunicorn** as the application server and **Nginx** as the web server.

## Prerequisites
- A Debian/Ubuntu server with root (sudo) access.
- Your code is already on GitHub: `https://github.com/humyai99/stockify-pro.git`

---

## Step 1: Update System & Install Basics
Run these commands to update your server and install necessary tools:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx
```

## Step 2: Clone Your Repository
Navigate to the web root directory and clone your project:

```bash
cd /var/www
sudo git clone https://github.com/humyai99/stockify-pro.git
sudo chown -R $USER:$USER stockify-pro
cd stockify-pro
```

## Step 3: Set Up Python Environment
Create a virtual environment and install your dependencies:

```bash
# Create virtual environment named 'venv'
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Gunicorn (Production Server)
pip install gunicorn
```

## Step 4: Test the Application
Try running it briefly to check for errors:
```bash
# This uses Gunicorn to serve the 'app' object from 'server.py'
gunicorn --bind 0.0.0.0:5000 server:app
```
(Press `Ctrl+C` to stop it after you see it start successfully)

## Step 5: Create a Systemd Service
This keeps your app running in the background and restarts it if it crashes.

1. Create the service file:
```bash
sudo nano /etc/systemd/system/stockify.service
```

2. Paste the following content (Save with `Ctrl+O`, Exit with `Ctrl+X`):
```ini
[Unit]
Description=Gunicorn instance to serve Stockify Pro
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/stockify-pro
Environment="PATH=/var/www/stockify-pro/venv/bin"
ExecStart=/var/www/stockify-pro/venv/bin/gunicorn --workers 3 --bind unix:stockify.sock -m 007 server:app

# Note: We use User=root here for simplicity. 
# If you are logged in as 'ghostpetch', change the line above to: User=ghostpetch
# And ensure you own the files: sudo chown -R ghostpetch:ghostpetch /var/www/stockify-pro

[Install]
WantedBy=multi-user.target
```

3. Start and Enable the service:
```bash
sudo systemctl start stockify
sudo systemctl enable stockify
sudo systemctl status stockify
```
(You should see `Active: active (running)`)

## Step 6: Configure Nginx (Reverse Proxy)
Nginx will handle valid web requests and pass them to your crypto app.

1. Create a new site config:
```bash
sudo nano /etc/nginx/sites-available/stockify
```

2. Paste this configuration:
```nginx
server {
    listen 80;
    server_name YOUR_SERVER_IP_OR_DOMAIN;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/stockify-pro/stockify.sock;
    }

    # Serve static files directly for better performance
    location /static {
        alias /var/www/stockify-pro;
    }
}
```
*Replace `YOUR_SERVER_IP_OR_DOMAIN` with your actual IP address or domain name.*

3. Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/stockify /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## Step 7: Done!
Open your browser and visit: `http://YOUR_SERVER_IP`
Your Stockify Pro app should be live! 🚀

---

## Troubleshooting
- **Logs**: to see errors, run: `sudo journalctl -u stockify -f`
- **Updates**: To update code later:
  ```bash
  cd /var/www/stockify-pro
  git pull origin main
  sudo systemctl restart stockify
  ```
