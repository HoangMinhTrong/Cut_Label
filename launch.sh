#!/bin/sh
set -eu
cd "$(dirname "$0")"
export CUT_LABEL_DATA_DIR="$PWD"
case "$(uname -m)" in
  arm64) platform=Apple-Silicon ;;
  x86_64) platform=Intel ;;
  *) exit 1 ;;
esac
destination="$PWD/.runtime/v1.0.0-macos-$platform"
if [ ! -f "$destination/Cut Label" ]; then
  printf 'Downloading Cut Label...\n'
  mkdir -p .runtime
  stage=$(mktemp -d "$PWD/.runtime/download.XXXXXX")
  curl --fail --location --retry 3 "https://github.com/HoangMinhTrong/Cut_Label/releases/download/v1.0.0/Cut-Label-macOS-$platform.tar.gz" -o "$stage/app.tar.gz"
  mkdir "$stage/app"
  tar -xzf "$stage/app.tar.gz" -C "$stage/app"
  mv "$stage/app" "$destination"
fi
exec "$destination/Cut Label"
