import subprocess


class Error:
    def __init__(self, message: str) -> None:
        self.message: str = message

    def to_string(self) -> str:
        return self.message


class WM:
    def __init__(self, name: str):
        self.name = name

    def install(self) -> Error | None:
        with open(f"./install/packages/{self.name}/pacman") as f:
            pacman_packeges = (x for x in f.readlines())
        for pkg in pacman_packeges:
            print(pkg)
        return None


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
    if res.returncode != 0:
        error_msg = (
            res.stderr.strip() or f"Команда завершилась с кодом {res.returncode}"
        )
        return Error(f"Ошибка при выполнении команды '{cmd}': {error_msg}")
    return None


def run_base_commands() -> Error | None:
    for cmd in base_commands:
        try:
            res = wrapped_subprocess(cmd)
            if res:
                return res

        except Exception as e:
            return Error(f"Не удалось запустить команду: {cmd}: {str(e)}")
    return None


def check_pacman_pkg(pkg: str) -> bool:
    res = wrapped_subprocess(f"pacman -Si {pkg}")
    if res:
        return False
    return True


def pacman_install() -> Error | None:
    with open("./install/packages/pacman") as f:
        pkgs = (f" {x.strip()}" for x in f.readlines())
    valid_pkgs = []
    for pkg in pkgs:
        if check_pacman_pkg(pkg):
            valid_pkgs.append(pkg)
        else:
            print(f"Пакет отсутсвует: {pkg}")

    res = wrapped_subprocess(f"sudo pacman -S --noconfirm {''.join(valid_pkgs)}")
    if res:
        return res
    return None


wms = (WM("hypr"), WM("mango"))


def install() -> Error | None:
    # print("Начало установки!\nЗапуск базовых команд...")
    # rbc = run_base_commands()
    # if rbc:
    #     return rbc

    print("Ставим базовые пакеты через пакеты...")
    res = pacman_install()
    if res:
        return res
    print("Базовые пакеты успешно установленны!")

    print("Установка yay...")
    res = wrapped_subprocess(
        r"git clone https://aur.archlinux.org/yay-bin.git && cd yay-bin && makepkg -si && cd .. && rm -rf yay-bin"
    )
    if res:
        return res
    # print("Введите какой оконный менеджер хотите использовать:")
    # for i, wm in enumerate(wms):
    #     print(f"{i}) {wm.name}")
    # wm = int(input())
    # if wm + 1 > len(wms):
    #     return Error("Введен неверный номер оконника")
    # wm = wms[wm]
    # wm.install()


launch = install()

if launch:
    print(launch.message)
else:
    print("Установка завершилась успешно!")
