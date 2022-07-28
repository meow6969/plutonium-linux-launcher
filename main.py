import os
import json
import shlex
import pick

import funcs
import wine_prefix


class launcher:
    def __init__(self):
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
               "4) Exit"
        switch = {
            "1": self.run_game,
            "2": self.select_dxvk_version,
            "3": self.select_proton_version,
            "4": exit
        }
        while True:
            print(menu)
            choice = input("Enter a number for what you want to do\n")
            switch[choice]()
            print()

    @staticmethod
    def create_preferences():
        install_path = os.path.expanduser("~/.local/share/linux-pluto")

        trying = True
        while trying:
            print("It seems you are a new user, please create a wine prefix for plutonium")
            print("If it asks you to install mono or gecko, don't")
            path = input(f"Where do you want to save the programs data? (default is {install_path})\n")
            if path.strip() == "":
                break

            # sanitize the input
            special_characters = "\'\"!@#$%^&*()+?=,<>\\"
            if any(c in special_characters for c in path):
                print("No special characters in the path")
                continue

            path = os.path.realpath(os.path.expanduser(path))
            # print(path)
            if int(os.system(f"mkdir -p {shlex.quote(path)} > /dev/null 2>&1")) == 0:  # if program has write perms
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
        # os.system(f"{self.prefix.ENV_VARS} wine64 {shlex.quote(f'{self.prefix.INSTALL_LOCATION}/plutonium.exe')}")
        print(f"{self.prefix.ENV_VARS} wine64 --version")
        os.system(f"{self.prefix.ENV_VARS} wine64 --version")

    def select_dxvk_version(self):
        options = funcs.get_github_releases("https://api.github.com/repos/doitsujin/dxvk/releases?per_page=100",
                                            self.prefix.CONFIG)
        selection = list(pick.pick(options, "    Pick your desired DXVK version", indicator="==>"))
        if "latest" in selection[0]:
            selection[0] = "latest"
        if "installed" not in selection[0]:
            self.prefix.download_dxvk(selection[0])

    def select_proton_version(self):
        options = funcs.get_github_releases(
            "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases?per_page=100",
            self.prefix.CONFIG)
        options.insert(0, "Use native wine")  # allows the user to select their native wine version
        selection = list(pick.pick(options, "    Pick your desired Proton version", indicator="==>"))
        if selection[0] != "Use native wine":
            if "(latest)" in selection[0]:
                selection[0] = selection[0][:-9]  # removes the (latest) at the end of its name
            if "installed" not in selection[0]:
                self.prefix.download_proton(selection[0])
            self.prefix.CONFIG = funcs.update_config(self.prefix.CONFIG, proton_version=f"Proton-{selection[0]}")
        else:
            self.prefix.CONFIG = funcs.update_config(self.prefix.CONFIG, proton_version=f"wine-native")
        self.prefix.ENV_VARS = self.prefix.set_env_vars()  # refreshes the self.prefix.ENV_VARS variable


if __name__ == "__main__":
    launcher()
