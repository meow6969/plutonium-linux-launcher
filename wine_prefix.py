import os
import json
import shlex

import funcs


class prefix:
    def __init__(self):
        self.CONFIG = json.load(open("preferences.json"))
        # print(os.path.expanduser(CONFIG["install_location"]))
        self.default_config = {
            "install_location": os.path.expanduser("~/.local/share/linux-pluto"),
            "prefix_complete": "N",
            "dxvk_version": "latest",
            "proton_version": "Proton-6.14-GE-2"  # Proton GE 6.14 is chosen here since it seems to work the best for me
        }

        self.CONFIG = funcs.check_config(self.CONFIG, self.default_config)
        self.INSTALL_LOCATION = os.path.realpath(os.path.expanduser(self.CONFIG["install_location"]))
        self.WINEPREFIX = shlex.quote(f"{self.INSTALL_LOCATION}/prefix")
        self.ENV_VARS = self.set_env_vars()
        if self.CONFIG["prefix_complete"] != "Y" or not os.path.exists(f"{self.INSTALL_LOCATION}/prefix"):
            self.create_prefix()

    def set_env_vars(self):
        # WINEDLLOVERRIDES part is to disable the gecko dialogue
        ENV_VARS = f'WINEDLLOVERRIDES="mscoree=" WINEARCH=win64 WINEPREFIX={self.WINEPREFIX}'

        if os.path.exists(f"{self.INSTALL_LOCATION}/proton/{self.CONFIG['proton_version']}/files"):
            proton_special_folder = "files"  # different versions of Proton GE put wine executables in different folders
        else:
            proton_special_folder = "dist"

        if self.CONFIG["proton_version"] != "wine-native":
            winepath = shlex.quote(f"{self.INSTALL_LOCATION}/proton/{self.CONFIG['proton_version']}/"
                                   f"{proton_special_folder}/bin")
            ENV_VARS += f" PATH={winepath}:$PATH"
        return ENV_VARS

    def setup_dxvk(self):
        print("\n\n\ninstalling DXVK")
        # make sure the dxvk folder exists
        os.system(f'mkdir -p {shlex.quote(f"{self.INSTALL_LOCATION}/dxvk")}')

        # checking if the installed DXVK is the latest
        replace_dxvk, dxvk_info = funcs.check_dxvk_version(self.INSTALL_LOCATION, True)
        # print(replace_dxvk)
        if replace_dxvk:
            os.system(f'mkdir -p {shlex.quote(f"{self.INSTALL_LOCATION}/dxvk")}')
            with open(f"{self.INSTALL_LOCATION}/dxvk/info.json", "w+") as f:
                # f.write(str(dxvk_info))
                json.dump(dxvk_info, f, indent=2)

            ### since there isn't DXVK in that folder or the DXVK is outdated we download the latest version
            self.download_dxvk("latest")
        version = dxvk_info["tag_name"]
        os.system(f'{self.ENV_VARS} {shlex.quote(f"{self.INSTALL_LOCATION}/dxvk/dxvk-{version[1:]}/setup_dxvk.sh")}'
                  f' install')

    def setup_proton(self):
        print("\n\n\ninstalling Proton")

        # make sure the proton folder exists
        os.system(f'mkdir -p {shlex.quote(f"{self.INSTALL_LOCATION}/proton")}')

        # we don't keep Proton up-to-date because changing the Proton version has more of an effect than changing the
        # DXVK version

        if os.path.exists(f"{self.INSTALL_LOCATION}/proton/{self.CONFIG['proton_version']}"):
            self.ENV_VARS = self.set_env_vars()  # refreshes the self.prefix.ENV_VARS variable
        else:  # the Proton version is not downloaded, so we need to do that
            self.download_proton(self.CONFIG["proton_version"])
            self.ENV_VARS = self.set_env_vars()  # refreshes the self.prefix.ENV_VARS variable

    def download_dxvk(self, version):
        # make sure the dxvk folder exists
        os.system(f'mkdir -p {shlex.quote(f"{self.INSTALL_LOCATION}/dxvk")}')

        if version == "latest":
            info = funcs.check_dxvk_version(self.INSTALL_LOCATION, True)[1]
            version = info["tag_name"]
        if not os.path.exists(f"{self.INSTALL_LOCATION}/dxvk/dxvk-{version[1:]}"):  # don't redownload versions
            print(f"Downloading DXVK {version}...")
            funcs.download_file(f"https://github.com/doitsujin/dxvk/releases/download/{version}/"
                                f"dxvk-{version[1:]}.tar.gz", "/tmp/dxvk_tarball.tar.gz")

            print("Extracting and installing...")
            os.system(f'tar xf /tmp/dxvk_tarball.tar.gz --directory {shlex.quote(f"{self.INSTALL_LOCATION}/dxvk")}')
            # mark the setup script as executable
            os.system(f'chmod +x {shlex.quote(f"{self.INSTALL_LOCATION}/dxvk/dxvk-{version[1:]}/setup_dxvk.sh")}')
        # install DXVK to the wine prefix
        os.system(f"{self.ENV_VARS} "
                  f"{shlex.quote(f'{self.INSTALL_LOCATION}/dxvk/dxvk-{version[1:]}/setup_dxvk.sh')} "
                  f"install > /dev/null")

        # mark in the preferences.json file what version of DXVK to use
        self.CONFIG = funcs.update_config(self.CONFIG, dxvk_version=version)

    def download_proton(self, version):
        # make sure the proton folder exists
        os.system(f'mkdir -p {shlex.quote(f"{self.INSTALL_LOCATION}/proton")}')

        if not os.path.exists(f"{self.INSTALL_LOCATION}/proton/{version}") and \
                not os.path.exists(f"{self.INSTALL_LOCATION}/proton/Proton-{version}"):
            print(f"Downloading {version}...")
            # original Proton GE builds used a different naming structure so we have to account for that
            if "Proton" not in version:
                file_name = f"Proton-{version}"
            else:
                file_name = version
            if version.startswith("Proton-"):
                version = version[7:]
            # print(f"https://github.com/GloriousEggroll/proton-ge-custom/releases/download/{version}/{file_name}.tar.gz")
            funcs.download_file(f"https://github.com/GloriousEggroll/proton-ge-custom/releases/download/{version}/"
                                f"{file_name}.tar.gz",
                                "/tmp/proton_tarball.tar.gz")

            print("Extracting and installing...")
            os.system(f'tar xf /tmp/proton_tarball.tar.gz --directory {shlex.quote(f"{self.INSTALL_LOCATION}/proton")}')

    def create_prefix(self):
        # install_path = os.path.expanduser(self.CONFIG["install_location"])
        # installing winetricks stuff
        print(f"Setting up a Plutonium prefix in {self.INSTALL_LOCATION}/prefix")

        dependencies = ["--force dotnet48",
                        "d3dcompiler_47 corefonts",
                        "vcrun2005 vcrun2019 vcrun2008 vcrun2012",
                        "d3dcompiler_43 d3dx11_42 d3dx11_43",
                        "gfw msasn1 physx",
                        "xact_x64 xact xinput"]
        print("Do not install mono or gecko")
        for dep in dependencies:
            return_code = os.system(f'{self.ENV_VARS} winetricks -q {dep}')
            if int(return_code) != 0:
                print("An error has occurred while installing dependencies with winetricks\n"
                      'Ensure winetricks is fully updated with the command "sudo winetricks --self-update"')
                input()
                exit()
            pass

        # turns on the "Automatically capture the mouse in full-screen windows" option in winecfg
        # also reg is the name of a character in made in abyss and thats pretty cool
        os.system(f'{self.ENV_VARS} wine regedit AutoCaptureMouse.reg')

        if not os.path.exists(f"{self.INSTALL_LOCATION}/dxvk"):
            self.setup_dxvk()
        if not os.path.exists(f"{self.INSTALL_LOCATION}/proton"):
            self.setup_proton()

        # download the plutonium.exe file
        # print(f"{self.INSTALL_LOCATION}/plutonium.exe")
        funcs.download_file("https://cdn.plutonium.pw/updater/plutonium.exe",
                            shlex.quote(f"{self.INSTALL_LOCATION}/plutonium.exe"))

        # mark in the preferences.json file that the wine prefix is complete
        self.CONFIG = funcs.update_config(self.CONFIG, prefix_complete="Y")


if __name__ == "__main__":
    prefix()
