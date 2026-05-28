#!/bin/sh
set -e

PASSWD=/mosquitto/config/passwd

# Tạo passwd file nếu chưa có
if [ ! -f "$PASSWD" ]; then
    mosquitto_passwd -c -b "$PASSWD" "${MQTT_BACKEND_USER:-backend}" "${MQTT_BACKEND_PASS:-backend_secret}"
    echo "[Mosquitto] Created passwd file with user: ${MQTT_BACKEND_USER:-backend}"
fi

exec mosquitto -c /mosquitto/config/mosquitto.conf
