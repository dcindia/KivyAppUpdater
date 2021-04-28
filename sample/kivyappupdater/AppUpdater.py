import urllib.request
from kivy.clock import mainthread
import threading
from kivy.properties import ListProperty
from kivy.uix.label import Label
from kivy.network.urlrequest import UrlRequest
from kivy.uix.screenmanager import Screen
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.progressbar import MDProgressBar
import jnius
from . import UpdaterBridge as Bridge

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


# //// Custom Decorators ////// #
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
            import traceback
            traceback.print_exc()
        finally:
            jnius.detach()

    return handler
# ////// ---------------------------- \\\\\\\ #


def compare_version(current_version, fetched_version):
    """
    Compare two versions and checks if fetched version greater than current version.
    :param current_version: Version Code obtained from Package Manager of host system
    :param fetched_version: Version code obtained from remote source
    :return: True if fetched_version > current_version, otherwise false
    """
    current_version = str(current_version)
    fetched_version = str(fetched_version)
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


def resolve_update_source(source: str):
    update_info['source'] = source.split("/")[0]

    if update_info['source'] == "GITHUB":
        update_info['source-path'] = source[7:]
    else:
        update_info['source-path'] = Bridge.package_name()

    source_path = update_info['source-path']
    if update_info['source'] == 'GITHUB':
        update_url = Constants["GITHUB_URL"] + source_path + '/releases/latest'
    elif update_info['source'] == 'AMAZON':
        update_url = Constants["AMAZON_URL"] + source_path
    elif update_info['source'] == 'PLAYSTORE':
        update_url = Constants["PLAY_STORE_URL"].format(name=source_path)
    else:
        update_url = False

    update_info['version_url'] = update_url


class UpdaterDownloader:
    """
    This class provides some useful functions which will perform general tasks required for updating.
    Re-usable for other purposes wherever required.
    """

    allow_download = True

    def guess_filename(self):
        return 'v{}_update.apk'.format(update_info['latest_version'])

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

        redirect = urllib.request.urlopen(download_url)  # without redirect unable to locate correct file
        final_download_url = redirect.geturl()
        download = UrlRequest(final_download_url, on_progress=update_progress, on_success=update_downloaded,
                              chunk_size=1024 * 100, file_path=filepath)


class UpdateDialog(MDDialog):
    """Customised Dialog for use with updation process."""
    # TODO: Inform main.py about cancellation of dialog
    # TODO: Dynamically change display_label according to internal ongoing process
    progress = ListProperty([0, 0, 0])  # [percent, current_size, total_size]

    def __init__(self, updater, **kwargs):
        self.updater_instance = updater

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
        self.updater_instance.downloader.allow_download = False

    def dismissed(self, instance):
        """Dismiss dialog if user cancelled download"""
        self.dismiss()

    def user_confirmed(self, instance, touch):
        """Changes dialog structure and initiates downloading process through Updater class"""
        if instance.collide_point(touch.x, touch.y) and not instance.disabled:
            self.confirm_button.disabled = True
            self.content_cls.add_widget(self.progress_bar)
            self.updater_instance.on_update_confirmed()


class Updater:
    def __init__(self):
        self.update_source = None
        self.downloader = UpdaterDownloader()
        # self.fetch = UpdaterFetch()
        from . import UpdaterFetch as fetch
        self.fetch = fetch
        self.dialog = UpdateDialog(self)

        app_info['current_version'] = Bridge.current_version(app_info)
        app_info['package_name'] = Bridge.package_name()

    @run_in_thread
    @handle_exception
    def on_update_confirmed(self):
        """Chief responsibility for launching update process when user confirms download."""

        fetch = self.fetch
        source = update_info['source']

        if source == "GITHUB":
            download_url = fetch.download_url
            print("[AppUpdater] User confirmed update, starting download...")
            file_path = os.path.join(Bridge.get_data_dir(), self.downloader.guess_filename())
            self.downloader.file_downloader(download_url, filepath=file_path, caller_instance=self)

        elif source in ("PLAYSTORE", "AMAZON"):
            download_url = fetch.download_url(source, app_info['package_name'])
            Bridge.trigger_intent(download_url)

    def on_update_downloaded(self):
        """
        Launches App Installation Process
        """

        print("[AppUpdater] Update Downloaded!")
        Bridge.install_intent(self.downloader.guess_filename())

    @run_in_thread
    @handle_exception
    def check_for_update(self):
        """Chief responsibility for checking if update is available from remote source."""
        global update_info
        resolve_update_source(self.update_source)  # Converts update_source to much useful update_info

        latest_version = self.fetch.resolve_version(update_info['source'], update_info['version_url'])
        update_info['latest_version'] = latest_version

        is_update_available = compare_version(app_info['current_version'], latest_version)
        if is_update_available:
            self.dialog.set_normal_height()
            self.dialog.open()
            print("[AppUpdater] Update Found! Showing Update Dialog.")
        else:
            print("[AppUpdater] No Update Available !")
