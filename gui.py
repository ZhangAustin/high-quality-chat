import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

import audio
from hqc import Config

kivy.require('1.0.7')


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
        config = Config('conn.conf')
        config.write('ConnectionDetails', 'server', servername)
        config.write('ConnectionDetails', 'user', username)
        config.write('ConnectionDetails', 'password', password)

        self.parent.current = 'session'
HQC().run()

