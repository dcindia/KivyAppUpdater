from kivy.lang import Builder
from kivymd.app import MDApp
import threading


class SampleUpdater(MDApp):

    def build(self):
        kv = """
FloatLayout:
    MDFlatButton:
        id: chk_update_button
        text: "Check for Updates"
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
        on_release: self.text = "Checking..."
        on_release: app.open_dialog()
        
        """
        return Builder.load_string(kv)

    def open_dialog(self):
        print(self._get_user_data_dir())

        from kivyappupdater import AppUpdater

        updater = AppUpdater.Updater()
        updater.json_update_url = "https://raw.githubusercontent.com/darpan5552/KivyAppUpdater/master/update.json"

        updater.check_for_update()



SampleUpdater().run()
