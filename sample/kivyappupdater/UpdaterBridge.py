"""
Contains methods to obtain special classes of android
"""

from jnius import autoclass, cast
from kivy import platform
from kivy.clock import mainthread

if platform == "android":
    from android import activity

PythonActivity = autoclass('org.kivy.android.PythonActivity')
currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
context = cast('android.content.Context', currentActivity.getApplicationContext())

Intent = autoclass('android.content.Intent')
Uri = autoclass('android.net.Uri')
PackageInstaller = autoclass('android.content.pm.PackageInstaller')


def get_data_dir():
    """Provides External Storage Directory: /storage/emulated/0/Android/data/<package-name>/files"""
    _external_storage_path = PythonActivity.getExternalFilesDir(None).getPath()
    print(_external_storage_path)
    return _external_storage_path


def package_name():
    """Provides package-name: org.dcindia.appupdater"""
    return context.getPackageName()


def current_version(app_info):
    """Provides version name(not code) : 1.0"""
    return context.getPackageManager().getPackageInfo(context.getPackageName(), 0).versionName


def trigger_intent(uri):
    """
    Simply fires android Intent.Action_View to open Android Markets
    :param uri: uri for Android markets
    :return:
    """

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')

    intent = Intent()
    intent.setAction(Intent.ACTION_VIEW)
    intent.setData(Uri.parse(uri))

    currentActivity.startActivity(intent)


def receieve_install_intent(intent):
    """Receives intent from package manager for getting user confirmation"""
    # FIXME: MIUI phones have protection features for not allowing app to install through Session API
    # TODO: Try to Install only if status check for extras is favourable.

    extras = intent.getExtras()
    message = extras.getString(PackageInstaller.EXTRA_STATUS_MESSAGE)
    print(message)
    confirmIntent = Intent(extras.get(Intent.EXTRA_INTENT))
    confirmIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    currentActivity.startActivity(confirmIntent)

@mainthread
def install_intent(file_name: str):
    """Handles all communication with Package Installler"""
    try:
        PackageInstaller = autoclass('android.content.pm.PackageInstaller')
        packageInstaller = context.getPackageManager().getPackageInstaller()

        SessionParams = autoclass('android.content.pm.PackageInstaller$SessionParams')
        params = SessionParams(SessionParams.MODE_FULL_INSTALL)

        sessionId = packageInstaller.createSession(params)
        print("SessionId:", sessionId)
        session = packageInstaller.openSession(sessionId)

        File = autoclass('java.io.File')
        inputFile = File(get_data_dir() + "/" + file_name)

        OutputStream = autoclass('java.io.OutputStream')
        packageInSession = session.openWrite("package", 0, -1)

        Files = autoclass('java.nio.file.Files')
        Files.copy(inputFile.toPath(), packageInSession)

        intent = Intent(context, PythonActivity)

        PendingIntent = autoclass('android.app.PendingIntent')
        pendingIntent = PendingIntent.getActivity(context, 0, intent, 0)

        IntentSender = autoclass('android.content.IntentSender')
        statusReceiver = pendingIntent.getIntentSender()

        packageInSession.close()
        activity.bind(on_new_intent=receieve_install_intent)
        session.commit(statusReceiver)


    except Exception as error:
        import traceback
        print(traceback.format_exc())
        print("[AppUpdater]", error)
    finally:
        session.close()



