#!/bin/bash

# GSC Coin SSL Certificate Setup Script
# Sets up SSL certificates for production deployment

set -e

echo "🔐 GSC Coin SSL Certificate Setup"
echo "================================="

DOMAIN="gsccoin.network"
EMAIL="admin@gsccoin.network"
SSL_DIR="./ssl"

# Create SSL directory
mkdir -p $SSL_DIR

# Function to generate self-signed certificate
generate_self_signed() {
    echo "📝 Generating self-signed SSL certificate..."
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout $SSL_DIR/gsccoin.key \
        -out $SSL_DIR/gsccoin.crt \
        -subj "/C=US/ST=State/L=City/O=GSC Coin/CN=$DOMAIN" \
        -addext "subjectAltName=DNS:$DOMAIN,DNS:www.$DOMAIN,DNS:seed1.$DOMAIN,DNS:seed2.$DOMAIN,DNS:seed3.$DOMAIN,DNS:seed4.$DOMAIN"
    
    echo "✅ Self-signed certificate generated"
    echo "📁 Certificate: $SSL_DIR/gsccoin.crt"
    echo "🔑 Private Key: $SSL_DIR/gsccoin.key"
}

# Function to setup Let's Encrypt certificate
setup_letsencrypt() {
    echo "🔒 Setting up Let's Encrypt certificate..."
    
    # Check if certbot is installed
    if ! command -v certbot &> /dev/null; then
        echo "📦 Installing certbot..."
        
        # Install certbot based on OS
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y certbot python3-certbot-nginx
            elif command -v yum &> /dev/null; then
                sudo yum install -y certbot python3-certbot-nginx
            else
                echo "❌ Unsupported Linux distribution"
                return 1
            fi
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            if command -v brew &> /dev/null; then
                brew install certbot
            else
                echo "❌ Homebrew not found. Please install certbot manually."
                return 1
            fi
        else
            echo "❌ Unsupported operating system"
            return 1
        fi
    fi
    
    # Generate certificate
    echo "🌐 Generating Let's Encrypt certificate for $DOMAIN..."
    
    # Stop nginx if running to free port 80
    if pgrep nginx > /dev/null; then
        echo "🛑 Stopping nginx temporarily..."
        sudo systemctl stop nginx || sudo nginx -s stop || true
    fi
    
    # Generate certificate using standalone mode
    sudo certbot certonly --standalone \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN \
        -d www.$DOMAIN \
        -d seed1.$DOMAIN \
        -d seed2.$DOMAIN \
        -d seed3.$DOMAIN \
        -d seed4.$DOMAIN
    
    # Copy certificates to SSL directory
    sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $SSL_DIR/gsccoin.crt
    sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $SSL_DIR/gsccoin.key
    
    # Set proper permissions
    sudo chown $(whoami):$(whoami) $SSL_DIR/gsccoin.crt $SSL_DIR/gsccoin.key
    chmod 644 $SSL_DIR/gsccoin.crt
    chmod 600 $SSL_DIR/gsccoin.key
    
    echo "✅ Let's Encrypt certificate installed"
    
    # Setup auto-renewal
    echo "🔄 Setting up auto-renewal..."
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet --post-hook 'docker-compose restart nginx'") | crontab -
    
    echo "✅ Auto-renewal configured"
}

# Function to setup custom certificate
setup_custom_cert() {
    echo "📋 Setting up custom certificate..."
    echo "Please provide the following files:"
    echo "1. Certificate file (PEM format)"
    echo "2. Private key file (PEM format)"
    echo "3. Certificate chain file (optional)"
    
    read -p "Enter path to certificate file: " CERT_FILE
    read -p "Enter path to private key file: " KEY_FILE
    read -p "Enter path to certificate chain file (optional): " CHAIN_FILE
    
    if [[ ! -f "$CERT_FILE" ]]; then
        echo "❌ Certificate file not found: $CERT_FILE"
        return 1
    fi
    
    if [[ ! -f "$KEY_FILE" ]]; then
        echo "❌ Private key file not found: $KEY_FILE"
        return 1
    fi
    
    # Copy certificate files
    cp "$CERT_FILE" $SSL_DIR/gsccoin.crt
    cp "$KEY_FILE" $SSL_DIR/gsccoin.key
    
    # Append chain if provided
    if [[ -f "$CHAIN_FILE" ]]; then
        cat "$CHAIN_FILE" >> $SSL_DIR/gsccoin.crt
    fi
    
    # Set proper permissions
    chmod 644 $SSL_DIR/gsccoin.crt
    chmod 600 $SSL_DIR/gsccoin.key
    
    echo "✅ Custom certificate installed"
}

# Function to verify certificate
verify_certificate() {
    echo "🔍 Verifying SSL certificate..."
    
    if [[ ! -f "$SSL_DIR/gsccoin.crt" ]] || [[ ! -f "$SSL_DIR/gsccoin.key" ]]; then
        echo "❌ Certificate files not found"
        return 1
    fi
    
    # Check certificate validity
    if openssl x509 -in $SSL_DIR/gsccoin.crt -text -noout > /dev/null 2>&1; then
        echo "✅ Certificate is valid"
        
        # Show certificate details
        echo "📋 Certificate Details:"
        openssl x509 -in $SSL_DIR/gsccoin.crt -text -noout | grep -E "(Subject:|Issuer:|Not Before:|Not After:|DNS:)"
        
        # Check if private key matches certificate
        CERT_HASH=$(openssl x509 -noout -modulus -in $SSL_DIR/gsccoin.crt | openssl md5)
        KEY_HASH=$(openssl rsa -noout -modulus -in $SSL_DIR/gsccoin.key | openssl md5)
        
        if [[ "$CERT_HASH" == "$KEY_HASH" ]]; then
            echo "✅ Private key matches certificate"
        else
            echo "❌ Private key does not match certificate"
            return 1
        fi
    else
        echo "❌ Certificate is invalid"
        return 1
    fi
}

# Function to setup HTTPS redirect
setup_https_redirect() {
    echo "🔀 Setting up HTTPS redirect..."
    
    cat > nginx_https_redirect.conf << 'EOF'
server {
    listen 80;
    server_name gsccoin.network www.gsccoin.network seed1.gsccoin.network seed2.gsccoin.network seed3.gsccoin.network seed4.gsccoin.network;
    
    # Redirect all HTTP traffic to HTTPS
    return 301 https://$server_name$request_uri;
}
EOF
    
    echo "✅ HTTPS redirect configuration created"
    echo "📁 File: nginx_https_redirect.conf"
}

# Function to test SSL configuration
test_ssl_config() {
    echo "🧪 Testing SSL configuration..."
    
    # Test certificate with openssl
    echo "Testing certificate with OpenSSL..."
    if openssl s_client -connect localhost:443 -servername $DOMAIN < /dev/null 2>/dev/null | grep -q "Verify return code: 0"; then
        echo "✅ SSL connection test passed"
    else
        echo "⚠️ SSL connection test failed (this is normal if server is not running)"
    fi
    
    # Create SSL test script
    cat > test_ssl.py << 'EOF'
#!/usr/bin/env python3
import ssl
import socket
import sys

def test_ssl_connection(hostname, port=443):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                print(f"✅ SSL connection to {hostname}:{port} successful")
                print(f"📋 Protocol: {ssock.version()}")
                print(f"🔐 Cipher: {ssock.cipher()}")
                cert = ssock.getpeercert()
                print(f"📜 Subject: {cert['subject']}")
                print(f"📅 Expires: {cert['notAfter']}")
                return True
    except Exception as e:
        print(f"❌ SSL connection to {hostname}:{port} failed: {e}")
        return False

if __name__ == "__main__":
    hostname = sys.argv[1] if len(sys.argv) > 1 else "gsccoin.network"
    test_ssl_connection(hostname)
EOF
    
    chmod +x test_ssl.py
    echo "✅ SSL test script created: test_ssl.py"
}

# Main menu
echo "Please choose SSL certificate setup option:"
echo "1. Generate self-signed certificate (for testing)"
echo "2. Setup Let's Encrypt certificate (for production)"
echo "3. Use custom certificate"
echo "4. Verify existing certificate"
echo "5. Setup HTTPS redirect"
echo "6. Test SSL configuration"

read -p "Enter your choice (1-6): " CHOICE

case $CHOICE in
    1)
        generate_self_signed
        verify_certificate
        setup_https_redirect
        ;;
    2)
        setup_letsencrypt
        verify_certificate
        setup_https_redirect
        ;;
    3)
        setup_custom_cert
        verify_certificate
        setup_https_redirect
        ;;
    4)
        verify_certificate
        ;;
    5)
        setup_https_redirect
        ;;
    6)
        test_ssl_config
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 SSL Certificate Setup Complete!"
echo "=================================="
echo ""
echo "📁 Certificate files location: $SSL_DIR/"
echo "🔐 Certificate: gsccoin.crt"
echo "🔑 Private Key: gsccoin.key"
echo ""
echo "📝 Next Steps:"
echo "1. Update your DNS records to point to this server"
echo "2. Start your GSC Coin mainnet with: ./deploy.sh"
echo "3. Test HTTPS access: https://$DOMAIN/api/v1/info"
echo "4. Monitor certificate expiration and renewal"
echo ""
echo "🔒 Security Recommendations:"
echo "• Keep private key file secure (600 permissions)"
echo "• Regularly update certificates before expiration"
echo "• Monitor SSL certificate validity"
echo "• Use strong cipher suites in nginx configuration"
echo ""
echo "Happy secure mining! 🚀"
