#!/usr/bin/env python3

"""
Android 11+
Pair and connect devices for wireless debug on terminal

python-zeroconf: A pure python implementation of multicast DNS service discovery
https://github.com/jstasiak/python-zeroconf
"""

import logging
import subprocess
from random import randint
from shutil import which
from sys import argv, exit

from colorama import Fore, just_fix_windows_console
from qrcode import QRCode
from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf

# Constants
TYPE = "_adb-tls-pairing._tcp.local."
NAME = "debug"
PASSWORD = randint(100000, 999999)
FORMAT_QR = "WIFI:T:ADB;S:{name};P:{password};;"
CMD_PAIR = "adb pair {ip}:{port} {code}"
SUCCESS_MSG = "Successfully paired"


class ADBListener(ServiceListener):
    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        logging.debug(f"Service {name} removed.")

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info: ServiceInfo | None = zc.get_service_info(type_, name)
        assert info, f"Service {name} not found."
        logging.debug(f"Service {name} added.")
        logging.debug(f"Service info: {info}")
        self.pair(info)

    def pair(self, info: ServiceInfo) -> None:
        cmd = CMD_PAIR.format(ip=info.server, port=info.port, code=PASSWORD)
        logging.debug(f"Executing command: {cmd}")
        process = subprocess.run(cmd, capture_output=True)
        stdout = process.stdout.decode()
        logging.debug(f"{stdout=}\n{process.stderr=}")

        if process.returncode != 0:
            print("Pairing failed.")
            exit(1)

        if stdout.startswith(SUCCESS_MSG):
            print(
                f"{Fore.GREEN}Successfully paired with {Fore.LIGHTYELLOW_EX}{info.ip_addresses_by_version(IPVersion.All)[0].exploded}{Fore.WHITE}:{Fore.LIGHTYELLOW_EX}{info.port}{Fore.RESET}"
            )
            exit(0)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass


def main() -> None:
    just_fix_windows_console()

    logging.basicConfig(
        level=logging.DEBUG if len(argv) > 1 else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    if not which("adb"):
        print(
            f"{Fore.RED}[Error] adb not found in your PATH. Please ensure that adb is installed and added to your PATH.{Fore.RESET}",
        )
        exit(1)

    qr = QRCode()
    qr.add_data(FORMAT_QR.format(name=NAME, password=PASSWORD))
    qr.make(fit=True)
    qr.print_ascii(invert=True)

    print(f"{Fore.YELLOW}Scan QR code to pair device.{Fore.RESET}")
    print(
        f"{Fore.CYAN}[System]{Fore.WHITE}->{Fore.CYAN}[Developer options]{Fore.WHITE}->{Fore.CYAN}[Wireless debugging]{Fore.WHITE}->{Fore.CYAN}[Pair device with QR code]{Fore.RESET}"
    )

    zeroconf = Zeroconf()
    listener = ADBListener()
    browser = ServiceBrowser(zeroconf, TYPE, listener)

    browser.join()  # Waiting until thread ends

    zeroconf.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\rClosing...")
