#!/bin/bash

mkdir -p /etc/nginx/ssl

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
-keyout /etc/nginx/ssl/selfsigned.key \
-out /etc/nginx/ssl/selfsigned.crt \
-subj "/C=US/ST=State/L=City/O=Organization/OU=IT/CN=92.63.76.159"

echo "SSL made succsessfully."
