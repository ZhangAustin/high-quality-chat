import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

import audio
from hqc import Config
from hqc import HQCPhone

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
    # TODO: Have GUI fill in pre-entered values
    #       Currently a blank field means use existing values, even if none exists
    def gettext(self, servername, username, password):
        config = Config('conn.conf')
        if servername != '':
            config.write('ConnectionDetails', 'server', servername)
        if username != '':
            config.write('ConnectionDetails', 'user', username)
        if password != '':
            config.write('ConnectionDetails', 'password', password)

        self.parent.current = 'session'

        phone = HQCPhone(config)
        phone.add_proxy_config()
        phone.add_auth_info()
        phone.make_call(1001, config.get('ConnectionDetails', 'server'))

HQC().run()
