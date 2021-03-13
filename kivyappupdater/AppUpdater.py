import urllib.request
import json
import platform
import re
from kivy.clock import mainthread, Clock
from kivy.lang import Builder
import threading
from kivy.properties import BooleanProperty, NumericProperty, ListProperty
from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.network.urlrequest import UrlRequest
from kivy.uix.screenmanager import Screen
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.progressbar import MDProgressBar
import jnius
from . import UpdaterBridge as Bridge
from . import UpdaterParser as Parser

import os
import certifi

os.environ['SSL_CERT_FILE'] = certifi.where()  # fixes SSL verification error on Android

# //// Important Values Stored Here ////// #
update_info = {}
app_info = {}
Constants = {
    "PLAY_STORE_URL": "https://play.google.com/store/apps/details?id={name}",
    "GITHUB_URL": "https://api.github.com/repos/",
    "AMAZON_URL": "http://www.amazon.in/gp/mas/dl/android?p="
}


# ////// ----------------------------\\\\\\\#

def run_in_thread(function):
    """Decorator to run a function that does not return anything, directly in thread"""
    from functools import wraps

    @wraps(function)
    def run(*args, **kwargs):
        t = threading.Thread(target=function, args=args, kwargs=kwargs)
        t.start()
        return t

    return run


def handle_exception(function):
    """Decorator to print exception raised by function."""

    def handler(*args, **kwargs):
        try:
            function(*args, **kwargs)
        except Exception as error:
            print("[AppUpdater]", error)
        finally:
            jnius.detach()

    return handler


class UpdaterFetch:
    """
    Fetches needed resources from web
    """

    def download_url(self, source, version_url):
        """
        Provides url from where update needs to be downloaded. Actual download in case of Github. In other cases,
        only intent is fired.
        :param version_url: Helps to fetch download url. In Playstore and Amazon they are download_url themselves.
        :param source: Services where application can be stored and distributed.
        :return: Ready-to-use url directly used to reach binary package.
        """

        if source == "GITHUB":

            github_json = {'assets': None}
            headers = {'Accept': "application/vnd.github.v3+json",
                       'User-Agent': "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11"}
            update_url = urllib.request.Request(version_url, headers=headers)

            github_json = json.loads(urllib.request.urlopen(update_url, timeout=5).read())

            absolute_url = github_json['assets'][0]['browser_download_url']
            redirect = urllib.request.urlopen(absolute_url)
            final_url = redirect.geturl()
            return final_url
        elif source == "PLAYSTORE":
            intent_url = "market://" + Constants['PLAY_STORE_URL'].split('/')[-1].format(name=version_url)
            return intent_url
        elif source == "AMAZON":
            intent_url = Constants['AMAZON_URL'] + version_url
            return intent_url

    def latest_version(self, source, version_url):
        """
        Query for latest version code available from remote sources.
        :param source: services where application can be stored and distributed.
        :param version_url: URL of service where latest version of app resides.
        :return version: Trimmed version code gained from source.
        """
        raw_version = None

        if source == "PLAYSTORE":
            update_website = urllib.request.urlopen(version_url, timeout=5).read()
            in_version = re.findall(r"Version.*?htlgb\">.*?</span>", str(update_website))
            raw_version = re.sub(r"<.*?>", '', in_version[-1])

        elif source == "GITHUB":
            headers = {"Accept": "application/vnd.github.v3+json",
                       "User-Agent": "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11"}
            request = urllib.request.Request(version_url, headers=headers)
            response = urllib.request.urlopen(request, timeout=5)
            github_json = json.loads(response.read())
            raw_version = github_json['tag_name']

        elif source == "AMAZON":
            # FIXME: This part is returning captcha verification due to anti-scraping policies of amazon.com
            # Using amazon.in fixes above problem but not sure if it works everytime.

            headers = {'User-Agent': "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11",
                       'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"}
            update_url = urllib.request.Request(version_url, headers=headers)

            update_website = urllib.request.urlopen(update_url, timeout=5).read()
            in_version = re.findall(r">Version:<.*?>.*?</span>", str(update_website))
            raw_version = re.sub(r"<.*?>", '', in_version[-1])

        trimmed_version = re.sub(r'[^0-9?!\\.]', '', raw_version)
        version = re.sub(r'\\.(\\.|$)', r"\\.0$1", trimmed_version)

        return version


class UpdaterUtils:
    """
    This class provides some useful functions which will perform general tasks required for updating.
    Re-usable for other purposes wherever required.
    """

    allow_download = True

    def guess_filename(self):
        return '{}_update.apk'.format(update_info['latest_version'])

    def file_downloader(self, download_url, filepath="AppUpdater/install.apk", caller_instance=None):
        """
        Used to download file for provided download url. Also provides live downloading status.
        :param caller_instance: Updater instance to gain greater control over other parts of program.
        :param download_url:
        :param filepath: Contains name and path where file going to be downloaded
        :return: 
        """

        @mainthread
        def update_progress(request, current_size, total_size):
            """Sends download progress to dialog. Also checks if user cancelled download."""
            print(request)
            if not self.allow_download:
                request.cancel()

            print("[AppUpdater]", current_size / (1024 * 1024), "/", total_size / (1024 * 1024))

            caller_instance.dialog.progress = [
                int((current_size / total_size) * 100),
                current_size / (1024 * 1024),
                total_size / (1024 * 1024)
            ]

        def update_downloaded(*args):
            """Initiates post download processes through Updater class"""
            caller_instance.on_update_downloaded()

        download = UrlRequest(download_url, on_progress=update_progress, on_success=update_downloaded,
                              chunk_size=1024 * 100, file_path=filepath)

    @staticmethod
    def compare_version(current_version, fetched_version):
        """
        Compare two versions and checks if fetched version greater than current version.
        :param current_version: Version Code obtained from Package Manager of host system
        :param fetched_version: Version code obtained from remote source
        :return: True if fetched_version > current_version, otherwise false
        """
        current_parts = current_version.split(".")
        fetched_parts = fetched_version.split(".")
        part_length = max(len(current_parts), len(fetched_parts))
        for k in range(0, part_length):
            current_compare_part = 0
            fetched_compare_part = 0
            if len(current_parts) > k:
                current_compare_part = current_parts[k]
            if len(fetched_parts) > k:
                fetched_compare_part = fetched_parts[k]
            if int(current_compare_part) < int(fetched_compare_part):
                return True
        else:
            return False


class UpdateDialog(MDDialog):
    """Customised Dialog for use with updation process."""
    # TODO: Inform main.py about cancellation of dialog
    # TODO: Dynamically change display_label according to internal ongoing process
    progress = ListProperty([0, 0, 0])  # [percent, current_size, total_size]

    def __init__(self, updater, **kwargs):
        self.updater_instance = updater
        # self.download_thread = threading.Thread(target=self.updater_instance.on_update_confirmed)

        self.title = "Update Available!"
        self.type = "custom"

        display_label = Label(text="New Feature")
        self.ignore_button = MDFlatButton(text="Ignore", on_press=self.dismissed)
        self.content_cls = Screen()
        self.progress_bar = MDProgressBar(value=self.progress[0])
        self.confirm_button = MDRaisedButton(text="Update", on_touch_down=self.user_confirmed)
        self.buttons = [self.ignore_button, self.confirm_button, ]

        super().__init__(**kwargs)

    def on_progress(self, *args):
        """Responsible for updating progress_bar"""
        print("Value Changed:", int(self.progress[0]))
        self.progress_bar.value = self.progress[0]

    def on_dismiss(self):
        """Mark Download Flag as False to stop download"""
        self.updater_instance.utils.allow_download = False

    def dismissed(self, instance):
        """Stops downloading process and dismiss dialog if user cancelled download"""
        # self.updater_instance.utils.allow_download = False
        self.dismiss()

    def user_confirmed(self, instance, touch):
        """Changes dialog structure and initiates downloading process through Updater class"""
        if instance.collide_point(touch.x, touch.y) and not instance.disabled:
            self.confirm_button.disabled = True
            self.content_cls.add_widget(self.progress_bar)
            self.updater_instance.on_update_confirmed()


class Updater:
    def __init__(self):
        self.json_update_url = None
        self.utils = UpdaterUtils()
        self.fetch = UpdaterFetch()
        self.dialog = UpdateDialog(self)

        app_info['current_version'] = Bridge.current_version(app_info)
        app_info['package_name'] = Bridge.package_name()

    @run_in_thread
    @handle_exception
    def on_update_confirmed(self):
        """Chief responsibility for launching update process when user confirms download."""

        fetch = self.fetch
        source = update_info['source']
        version_url = update_info['version_url']
        if source == "GITHUB":
            download_url = fetch.download_url(source, version_url)
            print("[AppUpdater] User confirmed update, starting download...")
            file_path = os.path.join(Bridge.get_data_dir(), '{}_update.apk'.format(update_info['latest_version']))
            self.utils.file_downloader(download_url, filepath=file_path, caller_instance=self)

        elif source in ("PLAYSTORE", "AMAZON"):
            download_url = fetch.download_url(source, app_info['package_name'])
            Bridge.trigger_intent(download_url)

    def on_update_downloaded(self):
        # TODO: Write code to install downloaded update

        print("[AppUpdater] Update Downloaded!")
        Bridge.install_intent(self.utils.guess_filename())
        

    @run_in_thread
    @handle_exception
    def check_for_update(self):
        """Chief responsibility for checking if update is available from remote source."""
        global update_info
        update_info = Parser.auto_fill(self.json_update_url)
        latest_version = self.fetch.latest_version(update_info['source'], update_info['version_url'])
        update_info['latest_version'] = latest_version
        is_update_available = self.utils.compare_version(app_info['current_version'], latest_version)
        if is_update_available:
            self.dialog.set_normal_height()
            self.dialog.open()
            print("[AppUpdater] Update Found! Showing Update Dialog.")
            # Bridge.install_intent(self.utils.guess_filename())  # Temporary for testing only, should be in on_update_downloaded
        else:
            print("[AppUpdater] No Update Available !")
