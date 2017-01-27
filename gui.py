import kivy
kivy.require('1.0.7')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition


class HQC(App):
    def build(self):
        gui = Builder.load_file("HQC.kv")
        return gui
class MainScreen(Screen):
    pass
class ScreenManager(ScreenManager):
    pass
class SessionScreen(Screen):
    pass
class SessionJoiningScreen(Screen):
    def get_text(self, *args):
        textinput= self.ids.user_text
        user = textinput.text
        print(user)
HQC().run()
