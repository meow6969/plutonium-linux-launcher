import os
import json
import shlex
import pick

from utils import funcs, wine_prefix

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class launcher:
    def __init__(self):
        if not os.path.isfile("/usr/bin/wine"):
            # we don't try to install wine for the user as this process can be weird on different distros, for example
            # arch linux requires enabling of multilib
            print("Please install wine, then run this installer")
            exit()

        # creates the preferences.json
        if not os.path.exists("preferences.json"):
            self.create_preferences()
        config = json.load(open("preferences.json"))

        # initializes the prefix class and checks if the wineprefix is there, and if no then creates one
        self.prefix = wine_prefix.prefix()

        # checks if the user both has the latest DXVK selected and if so will check what the latest DXVK version is
        if config["dxvk_version"] == "latest":
            funcs.check_dxvk_version(config["install_location"])

        # check if user has all needed directories created
        if not os.path.exists(f"{self.prefix.INSTALL_LOCATION}/prefix"):
            self.prefix.create_prefix()  # the prefix is missing for whatever reason, so we need to recreate it
        if not os.path.exists(f"{self.prefix.INSTALL_LOCATION}/dxvk"):
            self.prefix.setup_dxvk()
        if not os.path.exists(f"{self.prefix.INSTALL_LOCATION}/proton"):
            self.prefix.setup_proton()
        if not os.path.exists(f"{self.prefix.INSTALL_LOCATION}/plutonium.exe"):
            funcs.download_file("https://cdn.plutonium.pw/updater/plutonium.exe",
                                shlex.quote(f"{self.prefix.INSTALL_LOCATION}/plutonium.exe"))
        print()
        menu = "1) Start the Plutonium Launcher\n" \
               "2) Select a specific DXVK version\n" \
               "3) Select a specific Proton version\n" \
               "4) Enter a command to be ran inside the WINEPREFIX\n" \
               "5) Print current environment variables\n" \
               "6) Exit"
        switch = {
            "1": self.run_game,
            "2": self.select_dxvk_version,
            "3": self.select_proton_version,
            "4": self.enter_command,
            "5": self.print_env_vars,
            "6": exit
        }
        # make sure no processes are running that might mess up plutonium in the custom proton wine
        os.system(f"{self.prefix.ENV_VARS[28:]} wineserver -k")
        os.system(f"wineserver -k")  # kills all processes running in the system wine
        while True:
            print(menu)
            choice = input("Enter a number for what you want to do\n")
            try:
                switch[choice]()
            except KeyError:
                pass
            print()

    @staticmethod
    def create_preferences():
        install_path = os.path.expanduser("~/.local/share/linux-pluto")

        trying = True
        while trying:
            print("It seems you are a new user, please create a wine prefix for plutonium")
            print(f"{bcolors.BOLD}If it asks you to install mono or gecko, don't{bcolors.ENDC}")
            path = input(f"Where do you want to save the programs data? (default is "
                         f"{bcolors.OKGREEN}{install_path}{bcolors.ENDC})\n"
                         f"Press enter to use the default installation path, or enter a custom one.")
            if path.strip() == "":
                path = install_path
            correct_path = input(f"Is {bcolors.OKGREEN}{path}{bcolors.ENDC} the correct directory? Y/N ")
            if correct_path.strip().lower() != "y":
                continue

            # sanitize the input
            special_characters = "\'\"!@#$%^&*()+?=,<>\\"
            if any(c in special_characters for c in path):
                print("No special characters in the path")
                continue

            path = os.path.realpath(os.path.expanduser(path))
            # print(path)
            if int(os.system(f"mkdir -p {shlex.quote(path)} > /dev/null 2>&1")) == 0:
                try:
                    if len(os.listdir(path)) == 0:
                        install_path = path
                        trying = False
                    else:
                        print("Directory is not empty")
                except FileNotFoundError:  # path doesn't exist, so need to create it for the user
                    os.makedirs(path)
                    install_path = path
                    trying = False
            else:
                print("Cannot write to that location")

        funcs.update_config({}, install_location=install_path, prefix_complete="N", dxvk_version="latest")

    def run_game(self):
        # uses wine64 instead of wine because wine64 seems to work better
        # removes the first 28 characters because we need the WINEDLLOVERRIDES variable only for installing the prefix
        os.system(f"{self.prefix.ENV_VARS[28:]} wine64 {shlex.quote(f'{self.prefix.INSTALL_LOCATION}/plutonium.exe')}")
        # print(f"{self.prefix.ENV_VARS[28:]} wine64 --version")
        # os.system(f"{self.prefix.ENV_VARS} wine64 --version")
        os.system(f"{self.prefix.ENV_VARS[28:]} wineserver -w")  # this makes the process wait until the game has closed

    def select_dxvk_version(self):
        options = funcs.get_github_releases("https://api.github.com/repos/doitsujin/dxvk/releases?per_page=100",
                                            self.prefix.CONFIG)
        selection = list(pick.pick(options, "    Pick your desired DXVK version (UP/DOWN/ENTER)", indicator="==>"))
        if "latest" in selection[0]:
            selection[0] = "latest"
        if "installed" not in selection[0]:
            self.prefix.download_dxvk(selection[0])

    def select_proton_version(self):
        options = funcs.get_github_releases(
            "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases?per_page=100",
            self.prefix.CONFIG
        )
        options.insert(0, "Use native wine")  # allows the user to select their native wine version
        selection = list(pick.pick(options, "    Pick your desired Proton version (UP/DOWN/ENTER)", indicator="==>"))
        if selection[0] != "Use native wine":
            if "(latest)" in selection[0]:
                selection[0] = selection[0][:-9]  # removes the (latest) at the end of its name
            if "installed" not in selection[0]:
                self.prefix.download_proton(selection[0])
            self.prefix.CONFIG = funcs.update_config(self.prefix.CONFIG, proton_version=f"{selection[0]}")
        else:
            self.prefix.CONFIG = funcs.update_config(self.prefix.CONFIG, proton_version=f"wine-native")
        self.prefix.ENV_VARS = self.prefix.set_env_vars()  # refreshes the self.prefix.ENV_VARS variable

    def enter_command(self):
        command = input("Enter your command\n")
        print()
        # the 28 characters sliced off here is the WINEDLLOVERRIDES="mscoree="
        os.system(f"{self.prefix.ENV_VARS[28:]} {command}")
        os.system(f"{self.prefix.ENV_VARS[28:]} wineserver -w")

    def print_env_vars(self):
        print(self.prefix.ENV_VARS)


if __name__ == "__main__":
    launcher()
