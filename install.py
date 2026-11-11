import filecmp
import os
import re
import shutil
import subprocess
import sys
import logging
import tempfile
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

PACMAN_CONF = Path("/etc/pacman.conf")
RESOLV_CONF = Path("/etc/resolv.conf")
RESOLV_STUB = "/run/systemd/resolve/stub-resolv.conf"
NETWORK_TEMPLATES = Path("install/conf/etc/systemd/network")
NETWORK_DIR = Path("/etc/systemd/network")


class Error:
    def __init__(self, message: str) -> None:
        self.message: str = message

    def to_string(self) -> str:
        return self.message


class WM:
    def __init__(self, name: str):
        self.name = name

    def install(self) -> Error | None:
        return pacman_install(f"install/packages/{self.name}/pacman") or yay_install(
            f"install/packages/{self.name}/yay"
        )


network_services = ("iwd", "systemd-networkd", "systemd-resolved")

services = ("keyd", "cups", "bluetooth")

resolv_commands = (
    (f"sudo ln -sf {RESOLV_STUB} {RESOLV_CONF}", None),
    ("sudo systemctl try-restart iwd", None),
)

multilib_commands = (
    (r"sudo sed -i '/^#\[multilib\]/,/^#Include/ s/^#//' /etc/pacman.conf", None),
)

mirrors_command = (
    "rate-mirrors --protocol https --entry-country RU --concurrency 20 arch"
    " > {tmp} && sudo install -m 644 {tmp} /etc/pacman.d/mirrorlist"
    " && sudo pacman -Sy"
)

drivers = ("amd", "nvidia")


def wrapped_subprocess(cmd: str, cwd: str | Path | None = None) -> Error | None:
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    if res.stdout.strip():
        logger.debug("Вывод команды:\n%s", res.stdout.strip())
    if res.returncode != 0:
        error_msg = (
            res.stderr.strip() or f"Команда завершилась с кодом {res.returncode}"
        )
        return Error(f"Ошибка при выполнении команды '{cmd}': {error_msg}")
    return None


def run_commands(commands) -> Error | None:
    for cmd, cwd in commands:
        try:
            err = wrapped_subprocess(cmd, cwd=cwd)
            if err:
                return err
        except Exception as e:
            return Error(f"Не удалось запустить команду: {cmd}: {str(e)}")
    return None


def multilib_enabled() -> bool:
    return re.search(r"^\[multilib\]", PACMAN_CONF.read_text(), re.M) is not None


def outdated_network_templates() -> list[Path]:
    return [
        f
        for f in sorted(NETWORK_TEMPLATES.glob("*.network"))
        if not (NETWORK_DIR / f.name).is_file()
        or not filecmp.cmp(f, NETWORK_DIR / f.name, shallow=False)
    ]


def resolv_linked() -> bool:
    return RESOLV_CONF.is_symlink() and os.readlink(RESOLV_CONF) == RESOLV_STUB


def enable_service(name: str) -> Error | None:
    if wrapped_subprocess(f"systemctl cat {name}"):
        return Error(f"Сервис {name} не найден (пакет не установлен?)")

    enabled = wrapped_subprocess(f"systemctl is-enabled --quiet {name}") is None
    active = wrapped_subprocess(f"systemctl is-active --quiet {name}") is None
    if enabled and active:
        logger.info(f"Сервис {name} уже включён, пропускаем.")
        return None

    logger.info(f"Включаем сервис {name}...")
    return wrapped_subprocess(f"sudo systemctl enable --now {name}")


def enable_services(names) -> None:
    for name in names:
        if err := enable_service(name):
            logger.warning(err.message)


def update_mirrors() -> None:
    if not shutil.which("rate-mirrors"):
        logger.warning("rate-mirrors не найден, пропускаем обновление зеркал.")
        return

    with tempfile.NamedTemporaryFile() as tmp:
        err = wrapped_subprocess(mirrors_command.format(tmp=tmp.name))
    if err:
        logger.warning(err.message)


def run_base_commands() -> Error | None:
    outdated = outdated_network_templates()
    if not outdated:
        logger.info("Шаблоны systemd-networkd уже установлены, пропускаем.")
    for f in outdated:
        logger.info(f"Копируем шаблон {f.name} в {NETWORK_DIR}...")
        if err := wrapped_subprocess(f"sudo install -Dm644 {f} {NETWORK_DIR / f.name}"):
            return err

    enable_services(network_services)

    if outdated and (
        err := wrapped_subprocess("sudo systemctl try-restart systemd-networkd")
    ):
        logger.warning(err.message)

    if resolv_linked():
        logger.info("resolv.conf уже указывает на stub-resolv.conf, пропускаем.")
    elif err := run_commands(resolv_commands):
        return err

    if multilib_enabled():
        logger.info("multilib уже включён, пропускаем.")
    elif err := run_commands(multilib_commands):
        return err

    return wrapped_subprocess("sudo pacman -Sy")


def is_installed(pkg: str) -> bool:
    return wrapped_subprocess(f"pacman -Qq {pkg}") is None


def check_pkg(pkg: str, package_manager: str) -> bool:
    err = wrapped_subprocess(f"{package_manager} -Si {pkg}")
    return err is None


def packages_install(path: str, package_manager: str) -> Error | None:
    pkg_path = Path(path)
    if not pkg_path.exists():
        logger.warning(f"Файл пакетов не найден: {path}, пропускаем.")
        return None

    with open(pkg_path) as f:
        pkgs = [x.strip() for x in f.readlines() if x.strip() and not x.startswith("#")]

    valid_pkgs = []
    for pkg in pkgs:
        if is_installed(pkg):
            logger.debug(f"Пакет уже установлен: {pkg}")
        elif check_pkg(pkg, package_manager):
            valid_pkgs.append(pkg)
        else:
            logger.error(f"Пакет отсутствует в репозитории: {pkg}")

    if not valid_pkgs:
        logger.info(f"{path}: нечего ставить, всё уже установлено.")
        return None

    prefix = "sudo " if package_manager == "pacman" else ""
    return wrapped_subprocess(
        f"{prefix}{package_manager} -S --needed --noconfirm {' '.join(valid_pkgs)}"
    )


def pacman_install(path: str):
    return packages_install(path, "pacman")


def yay_install(path: str):
    return packages_install(path, "yay")


def yay_setup() -> Error | None:
    if shutil.which("yay"):
        logger.info("yay уже установлен, пропускаем.")
        return None

    if not shutil.which("git"):
        return Error("git не найден, установите его: sudo pacman -S git")

    with tempfile.TemporaryDirectory() as tmp:
        return wrapped_subprocess(
            "git clone https://aur.archlinux.org/yay-bin.git && "
            "cd yay-bin && makepkg -si --noconfirm",
            cwd=tmp,
        )


wms = (WM("hypr"), WM("mango"), WM("niri"))


def drivers_install() -> Error | None:
    logger.info(
        "Выберите драйверы видеокарты (через пробел, пустой ввод - пропустить):"
    )
    for i, d in enumerate(drivers):
        logger.info(f"{i}: {d}")

    while True:
        try:
            choices = sorted({int(x) for x in input("Ваш выбор: ").split()})
            if all(0 <= c < len(drivers) for c in choices):
                break
        except ValueError:
            pass
        logger.error("Введен неверный номер, попробуйте снова")

    for c in choices:
        logger.info(f"Ставим драйверы {drivers[c]}...")
        if err := pacman_install(f"install/packages/drivers/{drivers[c]}"):
            return err
    return None


def stow_install(
    path: str,
    target: str = "~",
    flags: str = "-R -v",
    cwd: str | Path | None = None,
    use_sudo: bool = False,
) -> Error | None:
    target_path = Path(target).expanduser()
    cmd_prefix = "sudo " if use_sudo or target_path == Path("/") else ""
    cmd = f"{cmd_prefix}stow {flags} -t {target_path} {path}"
    return wrapped_subprocess(cmd, cwd=cwd)


def stow_base_install() -> Error | None:
    specials_dirs = (
        Path("~/.config") / x for x in ("hypr", "waybar", "uwsm", "uwsm/env.d")
    )
    for spd in specials_dirs:
        spd = spd.expanduser()
        spd.mkdir(parents=True, exist_ok=True)

    err = stow_install("base", target="~", use_sudo=False)
    if err:
        return err

    err = stow_install("system", target="/", use_sudo=True)
    if err:
        return err

    return None


def choose_profiles(available_dirs: list[str]) -> list[str]:
    logger.info("Выберите нужные конфиги для установки (через пробел, номер или имя):")
    for i, d in enumerate(available_dirs):
        logger.info(f"{i}: {d}")

    while True:
        chosen = []
        for token in input("Ваш выбор: ").split():
            if token in available_dirs:
                chosen.append(token)
            elif token.isdigit() and int(token) < len(available_dirs):
                chosen.append(available_dirs[int(token)])
            else:
                logger.error(f"Нет такого конфига: {token}, попробуйте снова")
                break
        else:
            return list(dict.fromkeys(chosen))


def install() -> Error | None:
    logger.info("Начало установки!\nЗапуск базовых команд...")
    if err := run_base_commands():
        return err

    logger.info("Ставим базовые пакеты через pacman...")
    if err := pacman_install("install/packages/pacman"):
        return err
    logger.info("Базовые пакеты успешно установлены!")

    logger.info("Обновляем зеркала...")
    update_mirrors()

    logger.info("Установка yay...")
    if err := yay_setup():
        return err

    logger.info("Ставим пакеты через yay...")
    if err := yay_install("install/packages/yay"):
        return err
    logger.info("Установка пакетов yay успешно завершена!")

    logger.info("Установка драйверов...")
    if err := drivers_install():
        return err

    logger.info("Включаем сервисы...")
    enable_services(network_services + services)

    logger.info("Делаем симлинки через stow...")
    if err := stow_base_install():
        return err

    logger.info("Выберите оконный менеджер:")
    for i, wm in enumerate(wms):
        logger.info(f"{i}) {wm.name}")

    while True:
        try:
            choice = int(input("Введите номер: "))
            if 0 <= choice < len(wms):
                selected_wm = wms[choice]
                break
        except ValueError:
            pass
        logger.error("Введен неверный номер, попробуйте снова")

    if err := selected_wm.install():
        return err

    logger.info(f"Делаем симлинки для {selected_wm.name}...")
    if err := stow_install("base", target="~", cwd=selected_wm.name):
        return err

    wm_path = Path(selected_wm.name)
    available_dirs = sorted(
        f.name for f in wm_path.iterdir() if f.is_dir() and f.name != "base"
    )
    for d in choose_profiles(available_dirs):
        if err := stow_install(d, target="~", cwd=selected_wm.name):
            return err

    return None


if __name__ == "__main__":
    launch = install()
    if launch:
        logger.error(launch.message)
        sys.exit(1)
    else:
        logger.info("Установка завершилась успешно!")
        sys.exit(0)
