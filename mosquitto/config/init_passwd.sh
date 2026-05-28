#!/bin/sh
# Tạo passwd file với backend user nếu chưa có
PASSWD_FILE=/mosquitto/config/passwd
if [ ! -f "$PASSWD_FILE" ]; then
    mosquitto_passwd -c -b "$PASSWD_FILE" backend backend_secret
    echo "Created passwd file with backend user"
fi
