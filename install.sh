#!/usr/bin/env bash

VALID_PKGS=""

for pkg in $(grep -vE '^\s*#|^\s*$' install/packages/pacman); do
  if pacman -Si "$pkg" &>/dev/null; then
    VALID_PKGS="$VALID_PKGS $pkg"
  else
    echo "Пакет $pkg не найден в репозиториях, пропускаем..."
  fi
done

if [ -n "$VALID_PKGS" ]; then
  sudo pacman -S --needed $VALID_PKGS
fi
