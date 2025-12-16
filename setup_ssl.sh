#!/bin/bash

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
fi

# Get SSL certificate
echo "Getting SSL certificate from Let's Encrypt..."
sudo certbot certonly --standalone \
    -d support.yourcompany.com \
    --non-interactive \
    --agree-tos \
    --email admin@yourcompany.com

# Create nginx SSL directory
mkdir -p nginx/ssl

# Copy certificates
sudo cp /etc/letsencrypt/live/support.yourcompany.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/support.yourcompany.com/privkey.pem nginx/ssl/

# Set permissions
sudo chmod 644 nginx/ssl/fullchain.pem
sudo chmod 600 nginx/ssl/privkey.pem

echo "✅ SSL certificates installed!"
echo "Certificates will auto-renew. Run 'sudo certbot renew' to manually renew."

# Setup auto-renewal (optional)
echo "Setting up auto-renewal cron job..."
(sudo crontab -l 2>/dev/null; echo "0 0 * * * certbot renew --quiet --post-hook 'docker-compose -f docker-compose.prod.yml restart frontend'") | sudo crontab -

echo "✅ Auto-renewal configured!"
