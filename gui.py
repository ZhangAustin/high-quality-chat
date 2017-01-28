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
        config = open("conn.conf", 'a')
        config.write("[ConnectionDetails] \n")
        config.write("user=")
        config.write(username)
        config.write("\n")
        config.write("password=")
        config.write(password)
        config.write("\n")
        config.write("server=")
        config.write(servername)
        config.write("\n")
        config.write("[Settings] \n")
        config.write("mic=")
        config.write("None")
        config.write("\n")
        config.write("speakers=")
        config.write("None")
        config.write("\n")
        config.close()

        self.parent.current = 'session'
HQC().run()

