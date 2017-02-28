import kivy
from kivy.app import App
from kivy.config import Config
from kivy.lang import Builder
from kivy.logger import FileHandler
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.actionbar import ActionBar, ActionView, ActionButton
from kivy.base import runTouchApp
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.screenmanager import ScreenManager, Screen
import audio
import base64
from kivy.uix.popup import Popup
from hqc import HQCPhone
import Config
import ConfigParser
import os
import logging

NUMBER_OF_BUTTONS = 30

kivy.require('1.0.7')

#  Load logging configuration from file
logging.config.fileConfig('../logging.conf')
#  Reference logger
gui_logger = logging.getLogger('gui')
#  Reference config object in Config
config = Config.config


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

    def on_enter(self):
        # create a default grid layout with custom width/height
        layout = GridLayout(cols=4, padding=10, spacing=5,
                size_hint=(None, None), width=500)

        # when we add children to the grid layout, its size doesn't change at
        # all. we need to ensure that the height will be the minimum required
        # to contain all the childs. (otherwise, we'll child outside the
        # bounding box of the childs)
        layout.bind(minimum_height=layout.setter('height'))
        
        labelGrid = GridLayout(cols=1, width=50)
        playGrid = GridLayout(cols=1, orientation = 'vertical')
        # add button into that grid
        for i in range(NUMBER_OF_BUTTONS):
            #a ruse because it freaks out for 3 columns so it uses 4
            label0 = Label(text = " ", size=(.4, .5))

            label = Label(text="Clip_" + str(i), halign='left', size_hint=(.7, .5))
            btn = Button(background_normal= '../img/play.png',
                         size_hint=(.3, 1), allow_stretch=False)
            if i == 2 or i == 5:
                btn2 = Button(text="REQUESTED", size=(100, 50),
                             size_hint=(None, None))
            elif i == 4:
                btn2 = Button(text="Request\nAgain", size=(100, 50),
                             size_hint=(None, None))
            else:
                btn2 = Button(text="Request", size=(100, 50),
                                 size_hint=(None, None))
            layout.add_widget(btn)
            layout.add_widget(label)
            layout.add_widget(btn2)
            layout.add_widget(label0)

      
        # create a scroll view, with a size < size of the grid
        root = ScrollView(size_hint=(None, None), size=(310, 460),
                          pos_hint={'center_x': .5, 'center_y': .5}, do_scroll_x=False)
        root.add_widget(layout)
        self.ids.boxGrid.add_widget(root)

    def record_audio(self):
        filename = "audio.mp3"
        audio.record_audio(filename, 5)
        chunk_list = audio.split_audio_file(filename, 2.5)
        audio.save_audio_chunks(chunk_list, "audio", ".mp3", (os.getcwd() + "/"))


class ProducerJoiningScreen(Screen):
    # TODO: Have GUI fill in pre-entered values
    #       Currently a blank field means use existing values, even if none exists
    def gettext(self, servername, username, password):

        config = Config.Config("conn.conf")
        if servername != '':
            config.update_setting('ConnectionDetails', 'server', servername)
        else:
            servername = config.get('ConnectionDetails', 'server')
        if username != '':
            config.update_setting('ConnectionDetails', 'user', username)
        else:
            username = config.get('ConnectionDetails', 'user')
        if password != '':
            config.update_setting('ConnectionDetails', 'password', password)
        else:
            password = config.get('ConnectionDetails', 'password')
        # Get connection string
        conn_string = username + ';' + password + ";" + servername
        # Encode connection string
        encoded = base64.b64encode(conn_string)
        config.update_setting('ConnectionDetails', 'conn_string', encoded)
        self.parent.current = 'session'

        #  Make BoxLayout for multiple items
        popup_box = BoxLayout(orientation='vertical')
        # Make "Connection String" TextInput
        popup_text = TextInput(text=encoded, size_hint=(1, .8))
        popup_box.add_widget(popup_text)
        # Make "Close" button for popup
        close_button = Button(text='Close', size_hint=(.4, .2), pos_hint={'center_x': .5})
        popup_box.add_widget(close_button)
        popup = Popup(title='Connection String',
                      content=popup_box,
                      size_hint=(None, None), size=(400, 400),
                      auto_dismiss=False)
        close_button.bind(on_press=popup.dismiss)
        # Open the popup
        popup.open()

        phone = HQCPhone(config)
        phone.add_proxy_config()
        phone.add_auth_info()
        phone.make_call(1001, config.get('ConnectionDetails', 'server'))


class ArtistJoiningScreen(Screen):
    # TODO: Have GUI fill in pre-entered values
    #       Currently a blank field means use existing values, even if none exists
    def gettext(self, constring):
        try:
            decoded = base64.b64decode(constring)
            mark1 = decoded.find(';')
            mark2 = decoded.rfind(';')
            username = decoded[:mark1]
            password = decoded[mark1 + 1:mark2]
            server = decoded[mark2 + 1:]
            if server != '':
                config.update_setting('ConnectionDetails', 'server', server)
            if username != '':
                config.update_setting('ConnectionDetails', 'user', username)
            if password != '':
                config.update_setting('ConnectionDetails', 'password', password)

            self.parent.current = 'session'

            phone = HQCPhone(config)
            phone.add_proxy_config()
            phone.add_auth_info()
            phone.make_call(1001, config.get('ConnectionDetails', 'server'))
        except:
            errormessage = 'Sorry, that string is not valid'
            popup = Popup(title='Connection String Error',
                          content=Label(text=errormessage),
                          size_hint=(None, None), size=(400, 400))
            popup.open()


class SettingsScreen(Screen):
    pass

if __name__ == '__main__':
    HQC().run()
