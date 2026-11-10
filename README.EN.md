# 🐧 Dotfiles

🇷🇺 [Русская версия](README.md)

My configs for **Arch Linux** (Wayland): several window managers, per-hardware profiles and a Python installer. Symlinks are managed with [GNU Stow](https://www.gnu.org/software/stow/).

> ⚠️ **I use niri.** The **Hyprland** and **MangoWM** configs are outdated and may not work on recent versions of those WMs. They are kept in the repo as a starting point, but only the `niri` configs are maintained.

| Component                 | Used                                                                           |
| ------------------------- | ------------------------------------------------------------------------------ |
| WM / compositor           | [niri](https://github.com/YaLTeR/niri) (main), Hyprland and MangoWM (outdated) |
| Session                   | `uwsm`                                                                         |
| Bar / notifications / OSD | `waybar`, `mako`, `swayosd`                                                    |
| Launcher                  | `rofi`                                                                         |
| Terminal / shell          | `foot`, `fish`                                                                 |
| Editor                    | `neovim` (LazyVim based)                                                       |
| File manager              | `yazi` (terminal), `nautilus`                                                  |
| Networking                | `iwd` + `systemd-networkd` + `systemd-resolved`                                |
| Keyboard layout           | `keyd` (CapsLock: Esc on tap, navigation layer on hold)                        |

---

## 🗂 Repository layout

```
dotfiles/
├── install.py            # installer
├── base/                 # configs shared by every WM (fish, nvim, foot, rofi, yazi, mako, waybar styles, ~/.local/bin ...)
├── system/               # system files, stowed into /  (e.g. /etc/keyd/default.conf)
├── niri/                 # niri configs (maintained)
├── hypr/                 # Hyprland configs (outdated)
├── mango/                # MangoWM configs (outdated)
└── install/
    ├── packages/         # package lists (pacman / yay), separate for each WM and for drivers
    └── conf/etc/systemd/network/   # .network templates for systemd-networkd
```

Inside each WM directory configs are split into **profiles** (each profile is a separate stow package):

| Profile          | Purpose                                                      |
| ---------------- | ------------------------------------------------------------ |
| `base`           | shared WM settings: binds, visuals, autostart, rules         |
| `pc` / `laptop`  | monitors and input (touchpad, layout) for a specific machine |
| `amd` / `nvidia` | environment variables and settings for the GPU               |

Example: `niri/base`, `niri/laptop`, `niri/nvidia`.

---

## ⚡ Quick start

### 0. Fresh Arch install

Update the system and install what the installer needs:

```bash
sudo pacman -Syu
sudo pacman -S git python
```

### 1. Clone

```bash
git clone https://github.com/Dilikel/dotfiles
cd dotfiles
```

### 2. Automatic install

```bash
python install.py
```

What the installer does, step by step:

1. Enables `iwd`, `systemd-networkd`, `systemd-resolved`, sets up `resolv.conf` and enables `multilib` in `pacman.conf`.
2. Installs base packages from `install/packages/pacman`.
3. Updates the mirrors with `rate-mirrors` (picks the fastest ones for RU and overwrites `/etc/pacman.d/mirrorlist`; if anything fails, the old list is kept).
4. Builds and installs `yay`, then installs packages from `install/packages/yay`.
5. Asks which **GPU drivers** to install (`amd`, `nvidia`, both, or skip) and installs the packages from `install/packages/drivers/<name>`.
6. Enables the `keyd`, `cups` and `bluetooth` services (see [Services](#-services)).
7. Stows `base` into `~` and `system` into `/`.
8. Asks which WM to install (`hypr`, `mango` or `niri`), installs its packages and stows the WM's `base`.
9. Asks which profiles to enable (for example `pc nvidia` or `laptop amd`) and stows them.

The installer is safe to re-run: already installed packages, `yay`, enabled services, `multilib` and symlinks are skipped or recreated (`stow -R`). If a regular file sits where a symlink should go, stow reports a conflict and you need to move or remove that file yourself.

> The `install/conf/etc/systemd/network/*.network` templates are not copied by the installer. If you want networking through `systemd-networkd`, copy them yourself:
>
> ```bash
> sudo cp install/conf/etc/systemd/network/*.network /etc/systemd/network/
> sudo systemctl restart systemd-networkd
> ```

### 3. Installing individual packages

Every package is listed in `install/packages/` (one per line, `#` for comments), so you can pick only what you need:

```bash
sudo pacman -S <package>       # package from the official repositories
yay -S <package>               # package from the AUR (never run yay with sudo)
```

Or install a whole list at once:

```bash
sudo pacman -S --needed - < install/packages/pacman
```

### 4. Manual install (with stow)

If you don't want to run the installer, everything can be done by hand. Example for **niri on a desktop PC with NVIDIA** (use `amd` instead of `nvidia` for AMD, and `laptop` instead of `pc` for a laptop):

```bash
# shared configs and system files
stow -v -t ~ base
sudo stow -v -t / system

# configs of the chosen WM
cd niri
stow -v -t ~ base pc nvidia
```

### 5. Launch

Add `~/.local/bin` to `PATH` in fish and make the scripts executable:

```fish
fish_add_path ~/.local/bin
chmod +x ~/.local/bin/*
```

Start the WM through `uwsm` (for example from a TTY: `uwsm start niri.desktop`).

---

## 🔌 Services

The installer enables these services itself. If you installed manually, enable them with `sudo systemctl enable --now <service>`:

| Service                                | What for                                          |
| -------------------------------------- | ------------------------------------------------- |
| `iwd`                                  | Wi-Fi, used by `impala`                           |
| `systemd-networkd`, `systemd-resolved` | networking and DNS                                |
| `keyd`                                 | key remapping (CapsLock and the navigation layer) |
| `cups`                                 | print server: printers and scanners need it       |
| `bluetooth`                            | the `bluez` daemon, used by `bluetui`             |

`impala` and `bluetui` are only TUI clients: they don't run in the background, but they talk to the `iwd` and `bluetooth` services and show nothing without them.

`keyd` navigation layer: `CapsLock + h/j/k/l` are arrows, `a`/`e` are Home/End, `u`/`d` are PageUp/PageDown.

---

## 🔧 Managing symlinks

Run all commands from the repo root (or from the WM directory for its profiles).

| Task                                   | Command                    |
| -------------------------------------- | -------------------------- |
| Create links                           | `stow -v -t ~ <package>`   |
| Remove links                           | `stow -D -t ~ <package>`   |
| Refresh links (after adding new files) | `stow -R -t ~ <package>`   |
| System files (into `/`)                | `sudo stow -v -t / system` |

**Remove all configs:**

```bash
stow -D -t ~ base
sudo stow -D -t / system
cd niri
stow -D -t ~ base pc nvidia
```

**Switch GPU (for example from NVIDIA to AMD):**

```bash
cd niri
stow -D -t ~ nvidia
stow -v -t ~ amd
```

**Add a new config:** put the file into the right package keeping its path relative to `~` (for example `base/.config/foo/foo.conf`) and run `stow -R -t ~ base`.

> `*.md`, `*.sh`, `*.png` and `*touchpad.conf` files are excluded from stow via `.stow-local-ignore`.

---

## 🛠 Handy commands

**Reloading configs:**

```bash
makoctl reload                      # notifications
sudo systemctl restart keyd         # keyd (after editing /etc/keyd/default.conf)
```

niri picks up changes to its own config automatically, no restart needed.

**System and packages:**

```bash
sudo pacman -Syu                    # update the system
yay -Syu                            # update the system + AUR
sudo pacman -Rns <package>          # remove a package with its dependencies
pacman -Qdtq | sudo pacman -Rns -   # remove orphaned packages
```

**Update mirrors** (the installer does this itself, the command is for manual updates):

```bash
rate-mirrors --protocol https --entry-country RU --concurrency 20 arch | sudo tee /etc/pacman.d/mirrorlist
sudo pacman -Sy
```

**Shortcuts:**

| Bind              | Opens                                   |
| ----------------- | --------------------------------------- |
| `Mod + Shift + W` | `impala`, Wi-Fi                         |
| `Mod + Shift + B` | `bluetui`, Bluetooth                    |
| `Mod + Shift + A` | `wiremix`, audio                        |
| `Mod + Shift + T` | `btop`, monitoring                      |
| `Mod + Shift + P` | toggle power profile                    |
| `Mod + Shift + V` | clipboard history (`cliphist` + `rofi`) |

**Misc:**

```bash
systemctl --user status <service>   # status of a user service
journalctl -b -p err                # errors from the current boot
powerprofilesctl get                # current power profile
```
