#!/bin/bash
set -eoux pipefail
INSTALLED_DIRECTORY=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
FACTORIO_VOL=/factorio

mkdir -p "$FACTORIO_VOL"
mkdir -p "$SAVES"
mkdir -p "$CONFIG"
mkdir -p "$MODS"
mkdir -p "$SCENARIOS"
mkdir -p "$SCRIPTOUTPUT"

if [[ ! -f $CONFIG/rconpw ]]; then
  # Generate a new RCON password if none exists
  pwgen 15 1 >"$CONFIG/rconpw"
fi

if [[ ! -f $CONFIG/server-settings.json ]]; then
  # Copy default settings if server-settings.json doesn't exist
  cp /opt/factorio/data/server-settings.example.json "$CONFIG/server-settings.json"
fi

if [[ ! -f $CONFIG/map-gen-settings.json ]]; then
  cp /opt/factorio/data/map-gen-settings.example.json "$CONFIG/map-gen-settings.json"
fi

if [[ ! -f $CONFIG/map-settings.json ]]; then
  cp /opt/factorio/data/map-settings.example.json "$CONFIG/map-settings.json"
fi

NRTMPSAVES=$( find -L "$SAVES" -iname \*.tmp.zip -mindepth 1 | wc -l )
if [[ $NRTMPSAVES -gt 0 ]]; then
  # Delete incomplete saves (such as after a forced exit)
  rm -f "$SAVES"/*.tmp.zip
fi


EXEC=""
if [[ $(id -u) == 0 ]]; then
  # Update the User and Group ID based on the PUID/PGID variables
  usermod -o -u "$PUID" factorio > /dev/null
  groupmod -o -g "$PGID" factorio > /dev/null
  # Take ownership of factorio data if running as root
  chown -R factorio:factorio "$FACTORIO_VOL"
  # Drop to the factorio user
  EXEC="runuser -u factorio -g factorio --"
fi
if [[ -f /bin/box64 ]]; then
  # Use an emulator to run on ARM hosts
  # this only gets installed when the target docker platform is linux/arm64
  EXEC="$EXEC /bin/box64"
fi

sed -i '/write-data=/c\write-data=\/factorio/' /opt/factorio/config/config.ini

# shellcheck disable=SC2086
exec $EXEC /opt/factorio/bin/x64/factorio "$@"
