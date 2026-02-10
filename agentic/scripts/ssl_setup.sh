#!/bin/bash

# SSL Certificate Management Script for QA System
# Uses Let's Encrypt for automatic SSL certificate renewal

set -e

# Configuration
DOMAIN=${DOMAIN:-yourcompany.com}
EMAIL=${EMAIL:-admin@yourcompany.com}
CERTBOT_DIR="/etc/letsencrypt"
NGINX_SSL_DIR="/etc/nginx/ssl"
WEBROOT_PATH="/var/www/certbot"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
    fi
}

# Install dependencies
install_dependencies() {
    log "Installing dependencies..."
    
    # Update package list
    apt-get update
    
    # Install required packages
    apt-get install -y \
        certbot \
        python3-certbot-nginx \
        curl \
        openssl
    
    log "Dependencies installed successfully"
}

# Create necessary directories
create_directories() {
    log "Creating directories..."
    
    mkdir -p $NGINX_SSL_DIR
    mkdir -p $WEBROOT_PATH
    mkdir -p /var/log/letsencrypt
    
    log "Directories created successfully"
}

# Generate self-signed certificate for initial setup
generate_self_signed() {
    log "Generating self-signed certificate for initial setup..."
    
    # Generate private key
    openssl genrsa -out $NGINX_SSL_DIR/key.pem 2048
    
    # Generate certificate signing request
    openssl req -new -key $NGINX_SSL_DIR/key.pem -out $NGINX_SSL_DIR/cert.csr -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
    
    # Generate self-signed certificate valid for 90 days
    openssl x509 -req -days 90 -in $NGINX_SSL_DIR/cert.csr -signkey $NGINX_SSL_DIR/key.pem -out $NGINX_SSL_DIR/cert.pem
    
    # Clean up CSR
    rm $NGINX_SSL_DIR/cert.csr
    
    log "Self-signed certificate generated successfully"
    warn "This is a temporary certificate. Run 'setup_letsencrypt.sh' to get a proper SSL certificate."
}

# Setup Let's Encrypt certificate
setup_letsencrypt() {
    log "Setting up Let's Encrypt certificate for domain: $DOMAIN"
    
    # Check if domain is reachable
    if ! curl -f "http://$DOMAIN" > /dev/null 2>&1; then
        error "Domain $DOMAIN is not reachable. Please ensure DNS is configured correctly."
    fi
    
    # Request certificate
    certbot certonly \
        --webroot \
        --webroot-path=$WEBROOT_PATH \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --non-interactive \
        -d $DOMAIN
    
    # Copy certificates to nginx directory
    cp $CERTBOT_DIR/live/$DOMAIN/fullchain.pem $NGINX_SSL_DIR/cert.pem
    cp $CERTBOT_DIR/live/$DOMAIN/privkey.pem $NGINX_SSL_DIR/key.pem
    
    # Set proper permissions
    chmod 600 $NGINX_SSL_DIR/*.pem
    chown root:root $NGINX_SSL_DIR/*.pem
    
    log "Let's Encrypt certificate setup completed successfully"
}

# Setup automatic renewal
setup_renewal() {
    log "Setting up automatic certificate renewal..."
    
    # Create renewal cron job
    cat > /etc/cron.d/certbot-renewal << EOF
# Let's Encrypt certificate renewal for QA System
0 3 * * * root /usr/bin/certbot renew --quiet --deploy-hook "systemctl reload nginx" >> /var/log/letsencrypt/renewal.log 2>&1
EOF
    
    # Test renewal
    certbot renew --dry-run
    
    log "Automatic renewal setup completed"
}

# Setup certificate monitoring
setup_monitoring() {
    log "Setting up certificate monitoring..."
    
    cat > /usr/local/bin/check-cert-expiry.sh << 'EOF'
#!/bin/bash

# Certificate expiry monitoring script

DOMAIN=${DOMAIN:-yourcompany.com}
ALERT_EMAIL=${ALERT_EMAIL:-admin@yourcompany.com}
DAYS_THRESHOLD=30

# Get certificate expiry date
EXPIRY_DATE=$(openssl x509 -enddate -noout -in /etc/nginx/ssl/cert.pem | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))

if [ $DAYS_LEFT -lt $DAYS_THRESHOLD ]; then
    echo "WARNING: SSL certificate for $DOMAIN expires in $DAYS_LEFT days ($EXPIRY_DATE)" | \
    mail -s "SSL Certificate Expiry Warning" $ALERT_EMAIL
fi
EOF

    chmod +x /usr/local/bin/check-cert-expiry.sh
    
    # Add monitoring cron job (daily check)
    echo "0 9 * * * root /usr/local/bin/check-cert-expiry.sh" >> /etc/cron.d/cert-monitoring
    
    log "Certificate monitoring setup completed"
}

# Backup certificates
backup_certificates() {
    log "Creating certificate backup..."
    
    BACKUP_DIR="/backup/ssl-$(date +%Y%m%d-%H%M%S)"
    mkdir -p $BACKUP_DIR
    
    cp -r $CERTBOT_DIR $BACKUP_DIR/
    cp -r $NGINX_SSL_DIR $BACKUP_DIR/
    
    # Create tarball
    tar -czf "/backup/ssl-backup-$(date +%Y%m%d-%H%M%S).tar.gz" -C $BACKUP_DIR .
    
    # Remove temporary directory
    rm -rf $BACKUP_DIR
    
    log "Certificate backup completed"
}

# Restore certificates from backup
restore_certificates() {
    local backup_file=$1
    
    if [[ -z "$backup_file" ]]; then
        error "Please specify backup file to restore from"
    fi
    
    if [[ ! -f "$backup_file" ]]; then
        error "Backup file $backup_file not found"
    fi
    
    log "Restoring certificates from backup: $backup_file"
    
    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    
    # Extract backup
    tar -xzf $backup_file -C $TEMP_DIR
    
    # Restore certificates
    cp -r $TEMP_DIR/letsencrypt/* $CERTBOT_DIR/
    cp -r $TEMP_DIR/ssl/* $NGINX_SSL_DIR/
    
    # Set proper permissions
    chmod 600 $NGINX_SSL_DIR/*.pem
    chown root:root $NGINX_SSL_DIR/*.pem
    
    # Clean up
    rm -rf $TEMP_DIR
    
    # Reload nginx
    systemctl reload nginx
    
    log "Certificate restoration completed"
}

# Show certificate information
show_certificate_info() {
    log "Certificate Information:"
    
    if [[ -f $NGINX_SSL_DIR/cert.pem ]]; then
        echo "Certificate Details:"
        openssl x509 -in $NGINX_SSL_DIR/cert.pem -text -noout | grep -A 2 "Subject:"
        openssl x509 -in $NGINX_SSL_DIR/cert.pem -text -noout | grep -A 1 "Not Before"
        openssl x509 -in $NGINX_SSL_DIR/cert.pem -text -noout | grep -A 1 "Not After"
        
        # Calculate days until expiry
        EXPIRY_DATE=$(openssl x509 -enddate -noout -in $NGINX_SSL_DIR/cert.pem | cut -d= -f2)
        EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
        CURRENT_EPOCH=$(date +%s)
        DAYS_LEFT=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))
        
        echo "Days until expiry: $DAYS_LEFT"
    else
        warn "No certificate found at $NGINX_SSL_DIR/cert.pem"
    fi
}

# Main function
main() {
    local action=${1:-setup}
    
    case $action in
        "setup")
            check_root
            install_dependencies
            create_directories
            generate_self_signed
            log "Initial SSL setup completed. Run '$0 letsencrypt' to get a proper certificate."
            ;;
        "letsencrypt")
            check_root
            setup_letsencrypt
            setup_renewal
            setup_monitoring
            backup_certificates
            log "Let's Encrypt SSL setup completed"
            ;;
        "renew")
            check_root
            certbot renew --deploy-hook "systemctl reload nginx"
            backup_certificates
            log "Certificate renewal completed"
            ;;
        "info")
            show_certificate_info
            ;;
        "backup")
            check_root
            backup_certificates
            ;;
        "restore")
            check_root
            restore_certificates $2
            ;;
        "monitor")
            check_root
            /usr/local/bin/check-cert-expiry.sh
            ;;
        *)
            echo "Usage: $0 {setup|letsencrypt|renew|info|backup|restore|monitor} [backup_file]"
            echo ""
            echo "Commands:"
            echo "  setup     - Initial setup with self-signed certificate"
            echo "  letsencrypt - Setup Let's Encrypt certificate"
            echo "  renew     - Renew certificates"
            echo "  info      - Show certificate information"
            echo "  backup    - Backup certificates"
            echo "  restore   - Restore certificates from backup"
            echo "  monitor   - Check certificate expiry"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"