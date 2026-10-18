import subprocess
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class Error:
    def __init__(self, message: str) -> None:
        self.message: str = message

    def to_string(self) -> str:
        return self.message


class WM:
    def __init__(self, name: str):
        self.name = name

    def install(self) -> Error | None:
        return pacman_install(f"install/packages/{self.name}/pacman") and yay_install(
            f"install/packages/{self.name}/yay"
        )


base_commands = (
    ("sudo systemctl enable --now iwd", None),
    ("sudo systemctl enable --now systemd-networkd.service", None),
    ("sudo systemctl enable --now systemd-resolved.service", None),
    ("sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf", None),
    ("sudo systemctl restart iwd", None),
    (r"sudo sed -i '/^#\[multilib\]/,/^#Include/ s/^#//' /etc/pacman.conf", None),
    ("sudo pacman -Sy", None),
)


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


def run_base_commands() -> Error | None:
    for cmd, cwd in base_commands:
        try:
            err = wrapped_subprocess(cmd, cwd=cwd)
            if err:
                return err
        except Exception as e:
            return Error(f"Не удалось запустить команду: {cmd}: {str(e)}")
    return None


def check_pkg(pkg: str, package_manager: str) -> bool:
    err = wrapped_subprocess(f"{package_manager} -Si {pkg}")
    return err is None


def packages_install(path: str, package_manager: str) -> Error | None:
    pkg_path = Path(path)
    if not pkg_path.exists():
        logger.warning(f"Файл пакетов не найден: {path}, пропускаем.")
        return None

    with open(pkg_path) as f:
        pkgs = (x.strip() for x in f.readlines() if x.strip() and not x.startswith("#"))

    valid_pkgs = []
    for pkg in pkgs:
        if check_pkg(pkg, package_manager):
            valid_pkgs.append(pkg)
        else:
            logger.error(f"Пакет отсутствует в репозитории: {pkg}")

    if not valid_pkgs:
        return None

    return wrapped_subprocess(
        f"sudo {package_manager} -S --noconfirm {' '.join(valid_pkgs)}"
    )


def pacman_install(path: str):
    return packages_install(path, "pacman")


def yay_install(path: str):
    return packages_install(path, "yay")


wms = (WM("hypr"), WM("mango"), WM("niri"))


def stow_install(
    path: str,
    target: str = "~",
    flags: str = "-v",
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

    err = stow_install("system", target="/", flags="-v", use_sudo=True)
    if err:
        return err

    return None


def install() -> Error | None:
    logger.info("Начало установки!\nЗапуск базовых команд...")
    if err := run_base_commands():
        return err

    logger.info("Ставим базовые пакеты через pacman...")
    if err := pacman_install("install/packages/pacman"):
        return err
    logger.info("Базовые пакеты успешно установлены!")

    logger.info("Установка yay...")
    yay_cmd = (
        "git clone https://aur.archlinux.org/yay-bin.git && "
        "cd yay-bin && makepkg -si --noconfirm && cd .. && rm -rf yay-bin"
    )
    if err := wrapped_subprocess(yay_cmd):
        return err

    logger.info("Ставим пакеты через yay...")
    if err := yay_install("install/packages/yay"):
        return err
    logger.info("Установка пакетов yay успешно завершена!")

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

    logger.info("Выберите нужные конфиги для установки (через пробел):")
    wm_path = Path(selected_wm.name)
    available_dirs = (
        f.name for f in wm_path.iterdir() if f.is_dir() and f.name != "base"
    )
    for i, d in enumerate(available_dirs):
        logger.info(f"{i}: {d}")

    need_dirs = input("Ваш выбор: ").split()
    for d in need_dirs:
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
