import kivy
import audio
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
    def record_audio(self):
        filename = "audio.mp3"
        audio.record_audio(filename)
        audio.split_audio(filename, 2)
class SessionJoiningScreen(Screen):
    def gettext(self, servername, username, password):
        print(password, username, servername)
        self.parent.current = 'session'
HQC().run()
