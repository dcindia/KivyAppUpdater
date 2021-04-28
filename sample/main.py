from kivy.lang import Builder
from kivymd.app import MDApp


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

        from kivyappupdater import AppUpdater

        updater = AppUpdater.Updater()
        updater.update_source = "GITHUB/darpan5552/KivyAppUpdater"

        updater.check_for_update()


SampleUpdater().run()
