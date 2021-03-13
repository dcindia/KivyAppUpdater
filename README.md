## Introduction
Many of kivy/kivyMD projects are not available on Play Store for various reasons and thus making it difficult for developers to push updates. Even those are on Play Store, find it difficult to remind users to update their application. We believe that maintenance of software plays key role in bringing trust for it.

## How we help you?
- Automatically checks for updates
- Supports updates from Github, Amazon App Store and PlayStore
- Targets large user base above Android API 26
- Runs in thread without disturbing main application
- Direct Implementation, No Tweaks
- Well Documented Code

## Steps to Follow
#### Step 1:
Copy folder `kivyappupdater` to root directory of your project where your `main.py` located.

#### Step 2:
Upload a `.json` file somewhere on github or any other json server.
```json
{
  "source": "GITHUB/<user-name>/<repo-name>"
} 
```

> OR
 
```json
{
  "source": "AMAZON"
}
``` 

> OR 
 
```json
{
  "source": "PLAYSTORE"
}
```
#### Step 3:
Keep this block of code whenever or wherever you want to check-for-updates
```python
from kivyappupdater import AppUpdater
updater = AppUpdater.Updater()
updater.json_update_url = "<your-json-url>"
updater.check_for_update()
```
#### Step 4:
In your `buildozer.spec` file, do the following:
```spec
# (list) Permissions
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, INSTALL_PACKAGES, REQUEST_INSTALL_PACKAGES
# (int) Minimum API your APK will support.
android.minapi = 26
```

## We always need more [Future Plans]
- Updates according to set arch and api level. Somewhat similar to what happens on Google Playstore
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
