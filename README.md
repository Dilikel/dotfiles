# Dotfiles

install:

```
sudo pacman -S --needed - < install/packages/pacman
```

Это мои личные конфигурационные файлы для системы на базе **[Omarchy](https://omarchy.org)**.

> [!IMPORTANT]
> На данный момент конфиги адаптированы под текущий сетап. В будущем планируется полноценный переезд на чистый **Arch Linux**, как только появится свободное время от экзаменов.

---

## 🚀 Быстрый старт

### 1. Подготовка

Убедись, что в системе установлен `stow`:

```bash
sudo pacman -S stow

```

### 2. Клонирование

```bash
git clone https://github.com/Dilikel/dotfiles
cd ~/dotfiles

```

### 3. Развертывание (Deployment)

Используй команду `stow` для создания символьных ссылок.

**Для системы с NVIDIA (Анологично для AMD):**

```bash
stow -v base
cd hypr
stow -v -t ~ base nvidia
sudo stow -v -t / system
```

Добавить ~/.local/bin в PATH в fish:

```
fish_add_path ~/.local/bin
chmod +x ~/.local/bin
```

Запустить keyd:

```
sudo systemctl enable --now keyd
```

Для раздела «Развертывание» это критически важное дополнение, так как при переезде с одной видеокарты на другую (или при желании «откатить» конфиги) нужно знать, как правильно разорвать связи, не удалив сами файлы.

---

### 4. Удаление и Переключение (Management)

Если тебе нужно удалить ссылки из системы (например, при переезде с NVIDIA на AMD или для очистки `~`), используй флаг `-D` (Delete):

- **Удалить все конфиги:**

```bash
stow -D base
sudo stow -D -t / system
cd hypr
stow -D -t ~ base nvidia pc
```

- **Переключить GPU (например, с NVIDIA на AMD):**

```bash
cd hypr
stow -D -t ~ nvidia
stow -v -t ~ amd

```

- **Обновить ссылки (Restow):**
  Если ты добавил новые файлы в папки внутри `dotfiles`, используй флаг `-R` для пересоздания ссылок:

```bash
stow -R base

```

Обновить hyprland:

```bash
hyprctl reload

```

Обновить mako

```bash
makoctl reload

```

Обновить keyd:

```
sudo systemctl restart keyd
```
