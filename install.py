import subprocess
import sys
import logging

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
        return pacman_install(f"./install/packages/{self.name}/pacman") and yay_install(
            f"./install/packages/{self.name}/yay"
        )


base_commands = (
    "sudo systemctl enable --now iwd",
    "sudo systemctl enable --now systemd-networkd.service",
    "sudo systemctl enable --now systemd-resolved.service",
    "sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf",
    "sudo systemctl restart iwd",
    r"sudo sed -i '/^#\[multilib\]/,/^#Include/ s/^#//' /etc/pacman.conf",
    "sudo cp -rf ./install/conf/etc/systemd/network/ /etc/systemd",
    "sudo pacman -Sy",
)


def wrapped_subprocess(cmd: str) -> Error | None:
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.stdout.strip():
        logger.debug("Вывод команды:\n%s", res.stdout.strip())
    if res.returncode != 0:
        error_msg = (
            res.stderr.strip() or f"Команда завершилась с кодом {res.returncode}"
        )
        return Error(f"Ошибка при выполнении команды '{cmd}': {error_msg}")
    return None


def run_base_commands() -> Error | None:
    for cmd in base_commands:
        try:
            err = wrapped_subprocess(cmd)
            if err:
                return err

        except Exception as e:
            return Error(f"Не удалось запустить команду: {cmd}: {str(e)}")
    return None


def check_pkg(pkg: str, package_maneger: str) -> bool:
    err = wrapped_subprocess(f"{package_maneger} -Si {pkg}")
    if err:
        return False
    return True


def packages_install(path: str, package_maneger: str) -> Error | None:
    with open(path) as f:
        pkgs = (f" {x.strip()}" for x in f.readlines())
    valid_pkgs = []
    for pkg in pkgs:
        if check_pkg(pkg, package_maneger):
            valid_pkgs.append(pkg)
        else:
            logger.error(f"Пакет отсутсвует: {pkg}")

    err = wrapped_subprocess(
        f"sudo {package_maneger} -S --noconfirm {''.join(valid_pkgs)}"
    )
    if err:
        return err
    return None


def pacman_install(path: str):
    return packages_install(path, "pacman")


def yay_install(path: str):
    return packages_install(path, "yay")


wms = (WM("hypr"), WM("mango"), WM("niri"))

specials_dirs = ("~/.config/" + x for x in ("hypr", "waybar", "uwsm", "uwsm/env.d"))


def stow_install(path: str, flags: str = "-v ") -> Error | None:
    return wrapped_subprocess(f"stow {sys.flags} {path}")


def stow_base_install() -> Error | None:
    for spd in specials_dirs:
        res = wrapped_subprocess(f"rm -rf {spd} && mkdir {spd}")
        if res:
            return res
    return stow_install("./base")


def install() -> Error | None:
    logger.info("Начало установки!\nЗапуск базовых команд...")
    rbc = run_base_commands()
    if rbc:
        return rbc

    logger.info("Ставим базовые пакеты через pacman...")
    err = pacman_install("./install/packages/pacman")
    if err:
        return err
    logger.info("Базовые пакеты успешно установленны!")

    logger.info("Установка yay...")
    err = wrapped_subprocess(
        r"git clone https://aur.archlinux.org/yay-bin.git && cd yay-bin && makepkg -si && cd .. && rm -rf yay-bin"
    )
    if err:
        return err
    logger.info("Ставим базовые пакеты yay...")
    err = yay_install("./install/packages/yay")
    if err:
        return err
    logger.info("Установка базовых пакетов yay успешно заввершена!")

    logging.info("Делаем симлинки через stow в .config")
    err = stow_base_install()
    if err:
        return err
    logger.info("Базовые симлинки успешно установленны")

    logger.info("Введите какой оконный менеджер хотите использовать:")
    for i, wm in enumerate(wms):
        logger.info(f"{i}) {wm.name}")
    wm = None
    while True:
        wm = int(input())
        if wm + 1 > len(wms):
            logger.error("Введен неверный номер оконника")
        else:
            break
    wm = wms[wm]
    err = wm.install()
    if err:
        return err

    return None


if __name__ == "__main__":
    launch = install()
    if launch:
        logger.info(launch.message)
        sys.exit(1)
    else:
        logger.error("Установка завершилась успешно!")
        sys.exit(0)
