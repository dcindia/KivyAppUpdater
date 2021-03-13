# TODO: Build mechanism to choose apk to install according to their api and cpu build. For Example: Playstore

import json
import urllib.request
import urllib.error
import threading
from . import UpdaterBridge


update_json = {}  # To store raw data fetched from json url
update_info = {}  # To store processed data from update_json
Constants = {
    "PLAY_STORE_URL": "https://play.google.com/store/apps/details?id={name}",
    "GITHUB_URL": "https://api.github.com/repos/",
    "AMAZON_URL": "http://www.amazon.in/gp/mas/dl/android?p="
}


def get_json(url: str):

    request = urllib.request.urlopen(url, timeout=3.5)
    response = request.read()
    json_info = json.loads(response)
    print("[AppUpdater]", json_info)
    return json_info


def _source_path():
    if update_info['source'] == "GITHUB":
        source_path = update_json["source"][7:]
        return source_path
    else:
        source_path = UpdaterBridge.package_name()
        return source_path


def _update_source():
    update_source = update_json["source"].split("/")[0]
    return update_source


def version_url():
    source_path = update_info['source-path']
    if update_info['source'] == 'GITHUB':
        update_url = Constants["GITHUB_URL"] + source_path + '/releases/latest'
    elif update_info['source'] == 'AMAZON':
        update_url = Constants["AMAZON_URL"] + source_path
    elif update_info['source'] == 'FDROID':
        update_url = Constants["FDROID_URL"] + source_path
    elif update_info['source'] == 'PLAYSTORE':
        update_url = Constants["PLAY_STORE_URL"].format(name=source_path)
    else:
        update_url = False
    return update_url


def auto_fill(url: str):

    global update_json
    update_json = get_json(url)
    update_info['source'] = _update_source()
    update_info['source-path'] = _source_path()
    update_info['version_url'] = version_url()
    return update_info
