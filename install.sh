#!/usr/bin/env bash

set -e

echo "=== Запрос прав sudo ==="
sudo -v
while true; do
  sudo -n true
  sleep 60
  kill -0 "$$" || exit
done 2>/dev/null &

echo ""
echo "=== Настройка сети и системных служб ==="
sudo systemctl enable --now iwd
sudo systemctl enable --now systemd-networkd.service
sudo systemctl enable --now systemd-resolved.service
sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
sudo systemctl restart iwd
sudo sed -i '/^#\[multilib\]/,/^#Include/ s/^#//' /etc/pacman.conf

echo ""
echo "=== Конфигурация оборудования ==="

GPU_CHOICE=""
PS3="Выберите ваш GPU (или пропустите): "
gpu_options=("amd" "nvidia" "Пропустить")
select opt in "${gpu_options[@]}"; do
  case $opt in
  "amd")
    GPU_CHOICE="amd"
    break
    ;;
  "nvidia")
    GPU_CHOICE="nvidia"
    break
    ;;
  "Пропустить")
    GPU_CHOICE=""
    break
    ;;
  *) echo "Неверный выбор" ;;
  esac
done

FORM_CHOICE=""
PS3="Выберите тип устройства (или пропустите): "
form_options=("laptop" "pc" "Пропустить")
select opt in "${form_options[@]}"; do
  case $opt in
  "laptop")
    FORM_CHOICE="laptop"
    break
    ;;
  "pc")
    FORM_CHOICE="pc"
    break
    ;;
  "Пропустить")
    FORM_CHOICE=""
    break
    ;;
  *) echo "Неверный выбор" ;;
  esac
done

echo ""
echo "Выбранные профили:"
echo " - GPU: ${GPU_CHOICE:-нет}"
echo " - Form-factor: ${FORM_CHOICE:-нет}"

echo ""
echo "=== Установка yay (AUR Helper) ==="
if ! command -v yay &>/dev/null; then
  sudo pacman -S --needed --noconfirm base-devel git
  TMP_DIR=$(mktemp -d)
  git clone https://aur.archlinux.org/yay.git "$TMP_DIR/yay"
  (cd "$TMP_DIR/yay" && makepkg -si --noconfirm)
  rm -rf "$TMP_DIR"
else
  echo "yay уже установлен, пропускаем..."
fi

echo ""
echo "=== Сбор списка пакетов ==="
PKG_FILES=("install/packages/pacman")

if [ -n "$GPU_CHOICE" ] && [ -f "install/packages/$GPU_CHOICE" ]; then
  PKG_FILES+=("install/packages/$GPU_CHOICE")
fi

if [ -n "$FORM_CHOICE" ] && [ -f "install/packages/$FORM_CHOICE" ]; then
  PKG_FILES+=("install/packages/$FORM_CHOICE")
fi

RAW_PKGS=""
for file in "${PKG_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "Чтение пакетов из $file..."
    RAW_PKGS="$RAW_PKGS $(grep -vE '^\s*#|^\s*$' "$file")"
  fi
done

echo ""
echo "=== Проверка доступности пакетов ==="
VALID_PKGS=""
for pkg in $RAW_PKGS; do
  if yay -Si "$pkg" &>/dev/null || yay -Gi "$pkg" &>/dev/null; then
    VALID_PKGS="$VALID_PKGS $pkg"
  else
    echo "⚠️ Пакет $pkg не найден в репозиториях/AUR, пропускаем..."
  fi
done

if [ -n "$VALID_PKGS" ]; then
  echo ""
  echo "=== Установка пакетов ==="
  yay -S --needed --noconfirm $VALID_PKGS
fi

echo ""
echo "=== Включение дополнительных служб ==="
sudo systemctl restart keyd || true
sudo systemctl enable --now swayosd-libinput-backend.service || true

if [ -d "./install/conf/etc/systemd/network/" ]; then
  sudo cp -rf ./install/conf/etc/systemd/network/ /etc/systemd
fi

echo ""
echo "=== Создание симлинков через Stow (Принудительный режим) ==="

stow_force() {
  local target="$1"
  shift
  stow --adopt -v -R -t "$target" "$@"
  git checkout . 2>/dev/null || true
}

stow_force ~ base

HYPR_TARGETS=("base")
[ -n "$GPU_CHOICE" ] && HYPR_TARGETS+=("$GPU_CHOICE")
[ -n "$FORM_CHOICE" ] && HYPR_TARGETS+=("$FORM_CHOICE")

if [ -d "hypr" ]; then
  cd hypr
  echo "Применение stow в hypr/ для директорий: ${HYPR_TARGETS[*]}"
  stow_force ~ "${HYPR_TARGETS[@]}"
  cd ..
fi

sudo stow --adopt -v -R -t / system
git checkout system/ 2>/dev/null || true

echo ""
echo "=== Проверка подключения к GitHub ==="
ssh -T git@github.com || true

echo ""
echo "✨ Установка успешно завершена!"
