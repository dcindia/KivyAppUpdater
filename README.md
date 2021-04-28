## Introduction
Many of kivy/kivyMD projects are not available on Play Store for various reasons and thus making it difficult for developers to push updates. Even those are on Play Store, find it difficult to remind users to update their application. We believe that maintenance of software plays key role in bringing trust for it.

## How we help you?
- Automatically checks for updates from Github, Amazon App Store and PlayStore
- Updates according to set arch and api level for Github projects. Similar to what happens on Google Playstore 
- Targets large user base above Android API 26
- Runs in thread without disturbing main application
- Direct Implementation, No Tweaks

## Steps to Follow
#### Step 1:
Copy folder `kivyappupdater` to root directory of your project where your `main.py` located.

#### Step 2:
Keep this block of code whenever or wherever you want to check-for-updates
```python
from kivyappupdater import AppUpdater

updater = AppUpdater.Updater()
updater.update_source = "GITHUB/<user-name>/<repo-name>"  # Can also be "PLAYSTORE" or "AMAZON"

updater.check_for_update()
```

#### Step 3: (For Github only)
You need to upload a file named `upload.json` in your github releases. 

[Visit Wiki](https://github.com/dcindia/KivyAppUpdater/wiki/Format-of-update.json) for a detailed guide on format of json.

#### Step 4:
In your `buildozer.spec` file, do the following:
```spec
# (list) Permissions
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, INSTALL_PACKAGES, REQUEST_INSTALL_PACKAGES
# (int) Minimum API your APK will support.
android.minapi = 26
```

## We always need more [Future Plans]
- Superb control over users, devs can mark certain versions unusable directly from remote
- Set custom frequency of update reminder
- Custom messages or changelogs directly from json file
- More `TODO` at documentation level

## Issues will be there
This project is currently in its beta stage. Further more there are large amount of custom ROMs in the market which are many times problematic for implementation of certain API.
Please visit [**Issues**](https://github.com/darpan5552/KivyAppUpdater/issues) section to get informed on reported issues or register a new issue.
> Added feature in this project? Why not open a pull request.

## We specially thanks to
- kivy/kivyMD team
- [javiersnatos/appupdater](https://github.com/javiersantos/AppUpdater)
- [Real Python](https://realpython.com/) & [Geeks for Geeks](https://www.geeksforgeeks.org/)
