#!/bin/sh
cd "$(dirname "$0")" || exit 1
chmod +x "./Cut Label" 2>/dev/null
exec "./Cut Label"
