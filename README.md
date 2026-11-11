# 🐧 Dotfiles

🇬🇧 [English version](README.EN.md)

Мои конфиги для **Arch Linux** (Wayland): несколько оконных менеджеров, разделение по железу и установщик на Python. Симлинки раскладываются через [GNU Stow](https://www.gnu.org/software/stow/).

> ⚠️ **Я использую niri.** Конфиги для **Hyprland** и **MangoWM** устарели и могут не работать на свежих версиях этих WM. Они остались в репозитории как база, но актуальны только конфиги `niri`.

| Компонент                  | Что используется                                                                 |
| -------------------------- | -------------------------------------------------------------------------------- |
| WM / композитор            | [niri](https://github.com/YaLTeR/niri) (основной), Hyprland и MangoWM (устарели) |
| Сессия                     | `uwsm`                                                                           |
| Панель / уведомления / OSD | `waybar`, `mako`, `swayosd`                                                      |
| Лаунчер                    | `rofi`                                                                           |
| Терминал / шелл            | `foot`, `fish`                                                                   |
| Редактор                   | `neovim` (на базе LazyVim)                                                       |
| Файловый менеджер          | `yazi` (в терминале), `nautilus`                                                 |
| Сеть                       | `iwd` + `systemd-networkd` + `systemd-resolved`                                  |
| Раскладка клавиатуры       | `keyd` (CapsLock: Esc по тапу, слой навигации по зажатию)                        |

---

## 🗂 Структура репозитория

```
dotfiles/
├── install.py            # установщик
├── base/                 # общие конфиги для любого WM (fish, nvim, foot, rofi, yazi, mako, waybar-стили, ~/.local/bin ...)
├── system/               # системные файлы, раскладываются в /  (например /etc/keyd/default.conf)
├── niri/                 # конфиги niri (актуальные)
├── hypr/                 # конфиги Hyprland (устарели)
├── mango/                # конфиги MangoWM (устарели)
└── install/
    ├── packages/         # списки пакетов (pacman / yay), отдельно для каждого WM и драйверов
    └── conf/etc/systemd/network/   # шаблоны .network для systemd-networkd
```

Внутри каждого WM конфиги разложены по **профилям** (каждый профиль это отдельный stow-пакет):

| Профиль          | Назначение                                                |
| ---------------- | --------------------------------------------------------- |
| `base`           | общие настройки WM: бинды, визуал, автозапуск, правила    |
| `pc` / `laptop`  | мониторы и ввод (тачпад, раскладка) под конкретную машину |
| `amd` / `nvidia` | переменные окружения и настройки под видеокарту           |

Пример: `niri/base`, `niri/laptop`, `niri/nvidia`.

---

## ⚡ Быстрый старт

### 0. Свежая установка Arch

Обновляем систему и ставим то, что нужно для запуска установщика:

```bash
sudo pacman -Syu
sudo pacman -S git python
```

### 1. Клонирование

```bash
git clone https://github.com/Dilikel/dotfiles
cd dotfiles
```

### 2. Автоматическая установка

```bash
python install.py
```

Что делает установщик по шагам:

1. Копирует шаблоны `install/conf/etc/systemd/network/*.network` в `/etc/systemd/network/`, включает `iwd`, `systemd-networkd`, `systemd-resolved`, делает `/etc/resolv.conf` ссылкой на `stub-resolv.conf` (чтобы DNS шёл через `systemd-resolved`) и включает `multilib` в `pacman.conf`.
2. Ставит базовые пакеты из `install/packages/pacman`.
3. Обновляет зеркала через `rate-mirrors` (подбирает самые быстрые для RU и перезаписывает `/etc/pacman.d/mirrorlist`; если что-то пошло не так, старый список остаётся).
4. Собирает и ставит `yay`, затем пакеты из `install/packages/yay`.
5. Спрашивает, какие **драйверы видеокарты** ставить (`amd`, `nvidia`, оба или пропустить) и ставит пакеты из `install/packages/drivers/<имя>`.
6. Включает сервисы `keyd`, `cups` и `bluetooth` (см. [Сервисы](#-сервисы)).
7. Раскладывает `base` в `~` и `system` в `/` через stow.
8. Спрашивает, какой WM ставить (`hypr`, `mango` или `niri`), ставит его пакеты и раскладывает `base` выбранного WM.
9. Спрашивает, какие профили подключить (например `pc nvidia` или `laptop amd`) и раскладывает их.

Установщик можно безопасно запускать повторно: уже установленные пакеты, `yay`, включённые сервисы, `multilib` и симлинки он пропускает или пересоздаёт (`stow -R`). Если на месте будущего симлинка лежит обычный файл, stow сообщит о конфликте, и его нужно убрать или перенести вручную.

### 3. Установка отдельных пакетов

Все пакеты перечислены списками в `install/packages/` (один пакет на строку, `#` для комментариев), так что можно поставить что-то выборочно:

```bash
sudo pacman -S <пакет>         # пакет из официальных репозиториев
yay -S <пакет>                 # пакет из AUR (yay нельзя запускать через sudo)
```

Или поставить целый список разом:

```bash
sudo pacman -S --needed - < install/packages/pacman
```

### 4. Ручная установка (через stow)

Если не хочется запускать установщик, всё делается руками. Пример для **niri на ПК с NVIDIA** (для AMD вместо `nvidia` пиши `amd`, для ноутбука вместо `pc` пиши `laptop`):

```bash
# общие конфиги и системные файлы
stow -v -t ~ base
sudo stow -v -t / system

# конфиги выбранного WM
cd niri
stow -v -t ~ base pc nvidia
```

Сеть при ручной установке настраивается так:

```bash
sudo cp install/conf/etc/systemd/network/*.network /etc/systemd/network/
sudo systemctl enable --now iwd systemd-networkd systemd-resolved
sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
```

### 5. Запуск

Подключи `~/.local/bin` в `PATH` для fish и сделай скрипты исполняемыми:

```fish
fish_add_path ~/.local/bin
chmod +x ~/.local/bin/*
```

Запуск WM делается через `uwsm` (например, из TTY: `uwsm start niri.desktop`).

---

## 🔌 Сервисы

Установщик включает эти сервисы сам. Если ставил вручную, включи их командой `sudo systemctl enable --now <сервис>`:

| Сервис                                 | Зачем                                                  |
| -------------------------------------- | ------------------------------------------------------ |
| `iwd`                                  | Wi-Fi, с ним работает `impala`                         |
| `systemd-networkd`, `systemd-resolved` | сеть и DNS                                             |
| `keyd`                                 | переназначение клавиш (CapsLock и слой навигации)      |
| `cups`                                 | сервер печати: без него не работают принтеры и сканеры |
| `bluetooth`                            | демон `bluez`, с ним работает `bluetui`                |

`impala` и `bluetui` это только TUI-клиенты: сами они в фоне не запускаются, но общаются с сервисами `iwd` и `bluetooth`, и без них ничего не покажут.

Слой навигации `keyd`: `CapsLock + h/j/k/l` это стрелки, `a`/`e` это Home/End, `u`/`d` это PageUp/PageDown.

---

## 🔧 Управление симлинками

Все команды выполняются из корня репозитория (или из папки WM для её профилей).

| Задача                                | Команда                    |
| ------------------------------------- | -------------------------- |
| Создать ссылки                        | `stow -v -t ~ <пакет>`     |
| Удалить ссылки                        | `stow -D -t ~ <пакет>`     |
| Обновить ссылки (добавил новые файлы) | `stow -R -t ~ <пакет>`     |
| Системные файлы (в `/`)               | `sudo stow -v -t / system` |

**Удалить все конфиги:**

```bash
stow -D -t ~ base
sudo stow -D -t / system
cd niri
stow -D -t ~ base pc nvidia
```

**Переключить GPU (например, с NVIDIA на AMD):**

```bash
cd niri
stow -D -t ~ nvidia
stow -v -t ~ amd
```

**Добавить новый конфиг:** положи файл в нужный пакет с сохранением пути относительно `~` (например `base/.config/foo/foo.conf`) и выполни `stow -R -t ~ base`.

> Файлы `*.md`, `*.sh`, `*.png` и `*touchpad.conf` исключены из stow через `.stow-local-ignore`.

---

## 🛠 Удобные команды

**Перезагрузка конфигов:**

```bash
makoctl reload                      # уведомления
sudo systemctl restart keyd         # keyd (после правки /etc/keyd/default.conf)
```

niri подхватывает изменения своего конфига сам, перезапускать его не нужно.

**Система и пакеты:**

```bash
sudo pacman -Syu                    # обновить систему
yay -Syu                            # обновить систему + AUR
sudo pacman -Rns <пакет>            # удалить пакет вместе с зависимостями
pacman -Qdtq | sudo pacman -Rns -   # удалить пакеты-сироты
```

**Обновить зеркала** (установщик делает это сам, команда нужна для ручного обновления):

```bash
rate-mirrors --protocol https --entry-country RU --concurrency 20 arch | sudo tee /etc/pacman.d/mirrorlist
sudo pacman -Sy
```

**Быстрые клавиши:**

| Бинд              | Что открывается                             |
| ----------------- | ------------------------------------------- |
| `Mod + Shift + W` | `impala`, Wi-Fi                             |
| `Mod + Shift + B` | `bluetui`, Bluetooth                        |
| `Mod + Shift + A` | `wiremix`, звук                             |
| `Mod + Shift + T` | `btop`, мониторинг                          |
| `Mod + Shift + P` | переключение профиля питания                |
| `Mod + Shift + V` | история буфера обмена (`cliphist` + `rofi`) |

**Полезное:**

```bash
systemctl --user status <сервис>    # статус пользовательского сервиса
journalctl -b -p err                # ошибки текущей загрузки
powerprofilesctl get                # текущий профиль питания
```
