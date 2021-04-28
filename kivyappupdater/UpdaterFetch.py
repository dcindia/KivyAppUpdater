
"""
    Fetches needed resources from web
    """
import re
import json
import urllib.request
from . import UpdaterBridge as Bridge
from .AppUpdater import Constants, compare_version

download_url = ''
github_json = None

# Constants = AppUpdater.Constants
# compare_version = AppUpdater.compare_version


def find_compatible_build(update_manifest):
    # FIXME: min_sdk and sdk should be checked with compare_version method instead of integer comparison
    supported_abi = Bridge.compatible_abi()  # List of abis that device supports
    for build in update_manifest['builds']:
        for abi in supported_abi:  # Checks for compatibility with device abi
            if abi in build['arch']:
                break  # Stop searching for api compatibility, if found in particular build
        else:
            continue  # If not found, go for next build

        if 'min_api' in build.keys():
            # Least sdk for which build is available
            if not compare_version(build['min_api'], Bridge.sdk_version()):
                continue
        if 'api' in build.keys():
            # Max sdk for which particular build is available
            if compare_version(build['api'], Bridge.sdk_version()):
                continue

        # If all conditions match, returns corresponding artifact name as mentioned in build
        return build['artifact']
    else:
        return None  # If no compatible build found


def resolve_version(source, version_url):
    """
    Query for latest version code available from remote sources.
    :param source: services where application can be stored and distributed.
    :param version_url: URL of service where latest version of app resides.
    :return version: Trimmed version code gained from source.
    """

    global download_url

    if source == "GITHUB":
        headers = {"Accept": "application/vnd.github.v3+json",
                   "User-Agent": "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11"}
        request = urllib.request.Request(version_url, headers=headers)
        response = urllib.request.urlopen(request, timeout=5)
        # Provided by github, includes all details of latest published version
        github_json = json.loads(response.read())

        # Release tag name used for semantic versioning
        raw_version = github_json['tag_name']

        # Searching for update.json file uploaded in assets
        for asset in github_json['assets']:
            if asset['name'] == 'update.json' and asset['content_type'] == 'application/json':
                # Download url of update.json
                asset_url = asset['browser_download_url']
                request = urllib.request.urlopen(asset_url, timeout=3.5)
                response = request.read()
                # update_manifest (update.json)
                update_manifest = json.loads(response)

                # Suitable Installable file to download
                artifact = find_compatible_build(update_manifest)
                if artifact is None:
                    raw_version = '0.0'  # If no suitable file found, workaround to abandon update process
                    break

                # Searching for suitable installable from list of assets
                for asset2 in github_json['assets']:
                    if asset2['name'] == artifact:
                        # Download link of installable file
                        download_url = asset2['browser_download_url']
                        break
                else:
                    # if mentioned artifact not available in release assets
                    raise FileNotFoundError(
                        "[AppUpdater] Artifact not found in releases to download")
                break
        else:
            raise FileNotFoundError(
                "[AppUpdater] update.json invalid or missing")

    elif source == "PLAYSTORE":
        update_website = urllib.request.urlopen(
            version_url, timeout=5).read()
        in_version = re.findall(
            r"Version.*?htlgb\">.*?</span>", str(update_website))
        raw_version = re.sub(r"<.*?>", '', in_version[-1])

        intent_url = "market://" + Constants['PLAY_STORE_URL'].split(
            '/')[-1].format(name=version_url)  # Market link to open playstore
        download_url = intent_url

    elif source == "AMAZON":
        # FIXME: This part is returning captcha verification due to anti-scraping policies of amazon.com
        # Using amazon.in fixes above problem but not sure if it works everytime.

        headers = {'User-Agent': "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11",
                   'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"}
        update_url = urllib.request.Request(version_url, headers=headers)

        update_website = urllib.request.urlopen(
            update_url, timeout=5).read()
        in_version = re.findall(
            r">Version:<.*?>.*?</span>", str(update_website))
        raw_version = re.sub(r"<.*?>", '', in_version[-1])

        # Market link to open Amazon App Store
        intent_url = Constants['AMAZON_URL'] + version_url
        download_url = intent_url

    # Formats version string to strict semantic versioning,
    trimmed_version = re.sub(r'[^0-9?!\\.]', '', raw_version)
    # containing only numbers and dots
    version = re.sub(r'\\.(\\.|$)', r"\\.0$1", trimmed_version)
    return version
