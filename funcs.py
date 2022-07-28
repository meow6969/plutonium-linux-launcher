import json
import os
import urllib.request
import packaging.version


def download_file(link, destination):
    req = urllib.request.Request(link)
    with urllib.request.urlopen(req) as r:
        if destination == "memory":
            return r.read()  # returns the data of the request as a variable
        with open(destination, "wb") as f:
            f.write(r.read())


def check_dxvk_version(install_path, return_dxvk_info=False):
    req = urllib.request.Request("https://api.github.com/repos/doitsujin/dxvk/releases/latest")
    write = False
    with urllib.request.urlopen(req) as r:
        file = r.read()
        dxvk_info = json.loads(file)
        if os.path.exists(f"{install_path}/dxvk/info.json"):
            with open(f"{install_path}/dxvk/info.json", "r") as old_dxvk_info_:
                old_dxvk_info = json.loads(old_dxvk_info_.read())
                if packaging.version.parse(dxvk_info["tag_name"]) > packaging.version.parse(old_dxvk_info["tag_name"]):
                    replace_dxvk = True
                    write = True
                else:
                    replace_dxvk = False
        else:
            write = True
            replace_dxvk = True

    if write:  # if should write to the file writes to it
        with open(f"{install_path}/dxvk/info.json", "w+") as f:
            json.dump(dxvk_info, f, indent=2)

    # returns True if there is a newer version of DXVK available, False if latest is installed
    if return_dxvk_info:
        return replace_dxvk, dxvk_info
    else:
        return replace_dxvk


def update_config(config, install_location=False, prefix_complete=False, dxvk_version=False, proton_version=False,
                  write=True):
    if install_location:  # python marks strings with content as True in this scenario
        config["install_location"] = install_location
    if prefix_complete:
        config["prefix_complete"] = prefix_complete
    if dxvk_version:
        config["dxvk_version"] = dxvk_version
    if proton_version:
        config["proton_version"] = proton_version
    with open("preferences.json", "w+") as f:
        if write:  # checks if we want to save the config file to disk
            json.dump(config, f, indent=2)
    return config


def get_github_releases(repo, config):
    versions = download_file(repo, "memory")
    # print(dxvk_versions)
    versions = json.loads(versions)
    options = []
    for i in range(len(versions)):
        if versions[i]["tag_name"] == config["dxvk_version"]:
            options.append(f'{versions[i]["tag_name"]} (installed)')
        elif versions[i]["tag_name"] == config["proton_version"]:
            options.append(f'{versions[i]["tag_name"]} (installed)')
        else:
            options.append(versions[i]["tag_name"])
    options[0] = f"{options[0]} (latest)"
    return options


def check_config(config, default_config):  # checks if the config file has every entry it needs
    config_keys = config.keys()
    new_config = {}

    for key in default_config:
        if key not in config_keys:
            new_config[key] = default_config[key]
        else:
            new_config[key] = config[key]
    update_config(new_config)
    return new_config
