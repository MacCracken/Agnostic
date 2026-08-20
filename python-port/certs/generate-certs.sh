#!/bin/bash

# Generate self-signed certificates for development
set -e

CERT_DIR="certs"
VALIDITY_DAYS=365

# Create certificate directory
mkdir -p "$CERT_DIR"

# Generate CA certificate
openssl genrsa -out "$CERT_DIR/ca-key.pem" 4096
openssl req -new -x509 -days $VALIDITY_DAYS -key "$CERT_DIR/ca-key.pem" -sha256 -out "$CERT_DIR/ca.pem" -subj "/C=US/ST=CA/L=SF/O=QA System/OU=Development/CN=qa-system-local-ca"

# Generate server certificate for Redis
openssl genrsa -out "$CERT_DIR/redis-key.pem" 4096
openssl req -subj "/CN=redis" -sha256 -new -key "$CERT_DIR/redis-key.pem" -out "$CERT_DIR/redis.csr"
echo "subjectAltName = DNS:redis,DNS:localhost,IP:127.0.0.1" > "$CERT_DIR/redis.ext"
openssl x509 -req -days $VALIDITY_DAYS -sha256 -in "$CERT_DIR/redis.csr" -CA "$CERT_DIR/ca.pem" -CAkey "$CERT_DIR/ca-key.pem" -CAcreateserial -out "$CERT_DIR/redis.pem" -extfile "$CERT_DIR/redis.ext"

# Generate server certificate for RabbitMQ
openssl genrsa -out "$CERT_DIR/rabbitmq-key.pem" 4096
openssl req -subj "/CN=rabbitmq" -sha256 -new -key "$CERT_DIR/rabbitmq-key.pem" -out "$CERT_DIR/rabbitmq.csr"
echo "subjectAltName = DNS:rabbitmq,DNS:localhost,IP:127.0.0.1" > "$CERT_DIR/rabbitmq.ext"
openssl x509 -req -days $VALIDITY_DAYS -sha256 -in "$CERT_DIR/rabbitmq.csr" -CA "$CERT_DIR/ca.pem" -CAkey "$CERT_DIR/ca-key.pem" -CAcreateserial -out "$CERT_DIR/rabbitmq.pem" -extfile "$CERT_DIR/rabbitmq.ext"

# Generate server certificate for WebGUI
openssl genrsa -out "$CERT_DIR/webgui-key.pem" 4096
openssl req -subj "/CN=webgui" -sha256 -new -key "$CERT_DIR/webgui-key.pem" -out "$CERT_DIR/webgui.csr"
echo "subjectAltName = DNS:webgui,DNS:localhost,IP:127.0.0.1" > "$CERT_DIR/webgui.ext"
openssl x509 -req -days $VALIDITY_DAYS -sha256 -in "$CERT_DIR/webgui.csr" -CA "$CERT_DIR/ca.pem" -CAkey "$CERT_DIR/ca-key.pem" -CAcreateserial -out "$CERT_DIR/webgui.pem" -extfile "$CERT_DIR/webgui.ext"

# Set appropriate permissions
chmod 600 "$CERT_DIR"/*-key.pem
chmod 644 "$CERT_DIR"/*.pem
chmod 644 "$CERT_DIR"/*.csr
chmod 644 "$CERT_DIR"/*.ext

# Clean up CSR files
rm "$CERT_DIR"/*.csr "$CERT_DIR"/*.ext

echo "Certificates generated successfully in $CERT_DIR/"
echo "CA Certificate: $CERT_DIR/ca.pem"
echo "Redis Certificate: $CERT_DIR/redis.pem"
echo "RabbitMQ Certificate: $CERT_DIR/rabbitmq.pem"
echo "WebGUI Certificate: $CERT_DIR/webgui.pem"