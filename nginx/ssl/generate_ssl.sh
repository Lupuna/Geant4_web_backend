#!/bin/bash

SSL_DIR="./nginx/ssl"

mkdir -p "$SSL_DIR"

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$SSL_DIR/selfsigned.key" \
  -out "$SSL_DIR/selfsigned.crt" \
  -subj "/C=US/ST=State/L=City/O=Organization/OU=IT/CN=92.63.76.159"

echo "SSL generated successfully in $SSL_DIR."

