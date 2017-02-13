import kivy
from kivy.app import App
from kivy.config import Config
from kivy.lang import Builder
from kivy.logger import FileHandler
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.screenmanager import ScreenManager, Screen
import audio
from hqc import Config
from hqc import HQCPhone
import Config
import os
import logging

kivy.require('1.0.7')

#  Load logging configuration from file
logging.config.fileConfig('logging.conf')
#  Reference logger
gui_logger = logging.getLogger('gui')


class HQC(App):
    def build(self):
        gui_logger.debug("Starting GUI")
        gui = Builder.load_file("HQC.kv")
        return gui


class MainScreen(Screen):
    pass


class ScreenManager(ScreenManager):
    pass


class SessionScreen(Screen):

    @staticmethod
    def record_audio():
        filename = "audio.mp3"
        audio.record_audio(filename, 5)
        chunk_list = audio.split_audio_file(filename, 2.5)
        audio.save_audio_chunks(chunk_list, "audio", ".mp3", (os.getcwd() + "/"))


class SessionJoiningScreen(Screen):
    # TODO: Have GUI fill in pre-entered values
    #       Currently a blank field means use existing values, even if none exists
    def get_text(self, servername, username, password):
        config = Config.Config('conn.conf')
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


class SettingsScreen(Screen):
    pass

if __name__ == '__main__':
    HQC().run()
