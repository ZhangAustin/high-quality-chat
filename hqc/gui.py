import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

import audio
import base64
from hqc import Config
from hqc import HQCPhone

import os

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
        audio.record_audio(filename, 5)
        chunk_list = audio.split_audio_file(filename, 2.5)
        audio.save_audio_chunks(chunk_list, "audio", ".mp3", (os.getcwd() + "/"))


class ProducerJoiningScreen(Screen):
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
        conn_string = username + ';' + password + ";" + servername
        encoded = base64.b64encode(conn_string)
        config.write('ConnectionDetails', 'conn_string', encoded)
        self.parent.current = 'session'

        phone = HQCPhone(config)
        phone.add_proxy_config()
        phone.add_auth_info()
        phone.make_call(1001, config.get('ConnectionDetails', 'server'))
class ArtistJoiningScreen(Screen):
    # TODO: Have GUI fill in pre-entered values
    #       Currently a blank field means use existing values, even if none exists
    def gettext(self, constring):
        config = Config('conn.conf')
        decoded = base64.b64decode(constring)
        mark1 = decoded.find(';')
        mark2 = decoded.rfind(';')
        username = decoded[:mark1]
        password = decoded[mark1 + 1:mark2]
        server = decoded[mark2 + 1:]
        if server != '':
            config.write('ConnectionDetails', 'server', server)
        if username != '':
            config.write('ConnectionDetails', 'user', username)
        if password != '':
            config.write('ConnectionDetails', 'password', password)

        self.parent.current = 'session'

        phone = HQCPhone(config)
        phone.add_proxy_config()
        phone.add_auth_info()
        phone.make_call(1001, config.get('ConnectionDetails', 'server'))

if __name__ == '__main__':
    HQC().run()

