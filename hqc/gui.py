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
import audio
import datetime
from datetime import datetime
import threading, signal
import time
NUMBER_OF_BUTTONS = 2
layout = GridLayout(cols=3, padding=10, spacing=5,
                size_hint=(None, None), width=310)
#layout2 = GridLayout(cols=1, padding=10, spacing=5,
 #               size_hint=(None, None), width=410)
startRecording = False
recorder = audio.Recorder("test")
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
        #layout = GridLayout(cols=4, padding=10, spacing=5,
         #       size_hint=(None, None), width=310)

        # when we add children to the grid layout, its size doesn't change at
        # all. we need to ensure that the height will be the minimum required
        # to contain all the childs. (otherwise, we'll child outside the
        # bounding box of the childs)
        layout.bind(minimum_height=layout.setter('height'))
        #slayout2.bind(minimum_height=layout.setter('height'))
        # add button into that grid


      
        # create a scroll view, with a size < size of the grid
        root = ScrollView(size_hint=(None, None), size=(310, 460),
                pos_hint={'center_x': .5, 'center_y': .5}, do_scroll_x=False)
        root.add_widget(layout)
        self.ids.boxGrid.add_widget(root)

        #layout2.add_widget(label)
        #root2 = ScrollView(size_hint=(None, None), size=(410, 200),
        #        pos_hint={'center_x': .5, 'center_y': .5}, do_scroll_x=False)
        #root2.add_widget(layout2)
        #self.ids.chatGrid.add_widget(root2)

    def add_clip(self):

        #time.sleep(2)
        label = Label(text = datetime.now().strftime('%Y-%m-%d %H:%M:%S'), halign='left', size_hint=(.5, 0.2))
        btn = Button(background_normal= '../img/play.png',
                     size_hint=(.18, 1), allow_stretch=False)
        btn2 = Button(text="Request", size=(100, 50),
                     size_hint=(0.32, None))

        layout.add_widget(btn)
        layout.add_widget(label)
        #layout.add_widget(label0)
        layout.add_widget(btn2)

    def begin_Recording(self):
        global startRecording
        global recorder
        startRecording = not startRecording
        if startRecording:
            recorder.start() # Starts recording
            print "Recording..."
        else: 
            recorder.stop()
            print "Done recording"
            self.add_clip()


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
        conn_string = username + ';' + password + ";" + servername
        encoded = base64.b64encode(conn_string)
        config.update_setting('ConnectionDetails', 'conn_string', encoded)
        self.parent.current = 'session'
        popup = Popup(title='Connection String',
                      content=TextInput(text=encoded),
                      size_hint=(None, None), size=(400, 400))
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

