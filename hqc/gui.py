import base64
import logging
from datetime import datetime

import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.lang import Builder
from kivy.properties import ListProperty, ObjectProperty, StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from kivy.uix.actionbar import ActionItem
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import ScreenManager, Screen

from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton

import audio
import time, threading
from Config import Config
from hqc import HQCPhone
from chat.ChatClient import HQCWSClient
from chat import constants


NUMBER_OF_BUTTONS = 30
# audioClipLayout = GridLayout(cols=3, padding=10, spacing=5,
#                     size_hint=(None, None), width=310)
# layout2 = GridLayout(cols=1, padding=10, spacing=5,
#                      size_hint=(None, None), width=410)
# TODO: REMOVE GLOBAL VARIABLES. Put them in the config, a class definition, or default parameter.
start_recording = False
filenames = []
recorder = None
progress = False
micOn = False
kivy.require('1.0.7')
lq_audio = "undefined in gui"

#  Load logging configuration from file
logging.config.fileConfig('../logging.conf')
#  Reference logger
gui_logger = logging.getLogger('gui')


class HQC(App):
    manager = ObjectProperty(None)
    """
    This represents the main application class
    """
    def build(self):
        gui_logger.debug("Build HQC application")
        self.config = Config("conn.conf")
        self.phone = HQCPhone(self.config)
        self.chat_client = HQCWSClient("Test User", "Test Role", '127.0.0.1', '9000', "C:Users/Boots/Desktop")
        # Give the web socket a reference to the app
        self.chat_client.app = self
        gui = Builder.load_file("HQC.kv")
        self.root = gui
        self.root.app = self
        return gui

    def update_chat(self, username, message):
        self.root.screens[3].update_chat(username, message)

    def update_role(self, role):
        self.chat_client.role = role
        self.config.update_setting("Chat", "role", role)


class MainScreen(Screen):
    app = ObjectProperty(None)
    pass


class ScreenManager(ScreenManager):
    app = ObjectProperty(None)


class SessionScreen(Screen):
    clip_no = -1
    app = ObjectProperty(None)

    un_muted_mic_image = '../img/microphone.png'
    muted_mic_image = '../img/muted.png'

    stop_black = '../img/stop_black.png'
    record_black = '../img/record_black.png'

    chat_messages = StringProperty()

    def on_enter(self):
        # global audioClipLayout

        # when we add children to the grid layout, its size doesn't change at
        # all. we need to ensure that the height will be the minimum required
        # to contain all the childs. (otherwise, we'll child outside the
        # bounding box of the childs)
        self.ids.audioSidebar.bind(minimum_height=self.ids.audioSidebar.setter('height'))
        # create a scroll view, with a size < size of the grid
        # root = ScrollView(size_hint=(None, None), size=(310, 460),
        #                   pos_hint={'center_x': .5, 'center_y': .5}, do_scroll_x=False)
        # root.add_widget(audioClipLayout)
        # self.ids.audioSidebar.add_widget(root)

    def add_clip(self):
        #generate the index number of the clip for referencing in filenames
        SessionScreen.clip_no += 1

        global audioClipLayout
        global filenames

        #add play button and filename index # for later playback
        btn = ToggleButton(background_normal= '../img/play.png',
                   size_hint=(.18, 1), group = 'play', allow_stretch=False)
        btn.apply_property(np=NumericProperty(SessionScreen.clip_no))
        btn.bind(on_press=self.play_clip)
        #audioClipLayout.add_widget(btn)

        # add filename label
        label = Label(text=filenames[-1], halign='left', size_hint=(.5, 0.2))
        #audioClipLayout.add_widget(label)

        #add request button
        btn2 = Button(text="Request", size=(100, 50),
                      size_hint=(0.32, None))
        #audioClipLayout.add_widget(btn2)

        self.ids.audioSidebar.add_widget(btn)
        self.ids.audioSidebar.add_widget(label)
        self.ids.audioSidebar.add_widget(btn2)

    def play_clip(self, obj):

        #get filename of the high quality clip associated with this play button
        global filenames
        filename = filenames[obj.np]

        #get filename of the session low quality audio stream
        global lq_audio

        #get ante/post meridiem of each stream
        start_time_ampm = lq_audio[0:2]
        filename_ampm = filename[0:2]

        #get the # seconds after playback that HQ clip starts in the LQ stream:
        #HQ start time in s - LQ start time in s (= int)
        start_time_seconds = int(lq_audio[3:5]) * 3600 + int(lq_audio[6:8]) * 60 + int (lq_audio[9:11])
        filename_seconds = int(filename[3:5]) * 3600 + int(filename[6:8]) * 60 + int (filename[9:11])

        #if the two times are not in the same part of the day, add 12 hrs to the HQ time in seconds
        # (excluding the 12th hr, e.g. 11am to 12pm are in the same "half" of the day)
        if (start_time_ampm != filename_ampm and filename[3:5] != '12'):
            filename_seconds += 43200

        #gets the offset in seconds of the HQ file start time from the LQ stream
        hq_start_time = filename_seconds - start_time_seconds
        print filename + " session offset: " + str(hq_start_time) + " seconds"
        #gets the file associated with this button's label friend

        #audio.get_length(filename)
        #audio.playback(lq_audio, hq_start_time, None, 2)

    def begin_recording(self):
        global filenames

        #use globals to toggle
        global start_recording
        start_recording = not start_recording
        global recorder

        if start_recording:
            self.ids.record_button.source = SessionScreen.stop_black
            filename = datetime.now().strftime('%p_%I_%M_%S.mp3')
            recorder = audio.Recorder(filename) #creates audio file
            filenames.append(filename) #adds filename to global list
            recorder.start() # Starts recording

            global progress
            progress = True
            mythread = threading.Thread(target=self.record_progress)
            mythread.start()

            print "Recording..."
        else:
            progress = False
            self.ids.record_button.source = SessionScreen.record_black
            recorder.stop()
            self.add_clip() #adds to gui sidebar
            print "Done recording"

    def record_progress(self):
        global progress
        while progress:
            time.sleep(0.05)
            self.ids.progress_bar.value = (self.ids.progress_bar.value + 1) % 31#datetime.now().second % 6.0


    def toggle_mute(self):
        global micOn
        micOn = not micOn
        # Toggles the linphone mic
        #self.app.phone.toggle_mic()

        # Update the mic image
        if micOn:#phone.core.mic_enabled:
            self.ids.mute_button.source = SessionScreen.un_muted_mic_image
        else:
            self.ids.mute_button.source = SessionScreen.muted_mic_image

    def update_chat(self, username, message):
        """
        Called upon when receiving an incoming message
        :param message: string of message received
        :return: None
        """
        chat_message = str(username) + ": " + str(message)
        self.chat_messages += chat_message + "\n"

    def send_message(self, message):
        """
        Called upon entering text to the chat input.
        :param message: string entered in chat
        :return: None
        """
        if self.app.chat_client:
            self.app.chat_client.chat(message)
        else:
            print "Chat client not connected"
        # Reset text input
        self.parent.ids.chatText.text = ''
        # Keep cursor in text chat
        # Clock.schedule_once(self.refocus_input)

    def refocus_input(self):
        """
        Sets the cursor focus inside the session chat
        :return: None
        """
        self.parent.ids.chatText.focus = True


class ProducerJoiningScreen(Screen):
    app = ObjectProperty(None)

    def on_enter(self):
        self.app.update_role(constants.PRODUCER)

    # TODO: Have GUI fill in pre-entered values
    #       Currently a blank field means use existing values, even if none exists
    def gettext(self, servername, username, password):
        global lq_audio

        config = self.app.config
        # Reference App
        if servername != '':
            self.app.config.update_setting('ConnectionDetails', 'server', servername)
        else:
            servername = self.app.config.get('ConnectionDetails', 'server')
        if username != '':
            self.app.config.update_setting('ConnectionDetails', 'user', username)
        else:
            username = self.app.config.get('ConnectionDetails', 'user')
        if password != '':
            self.app.config.update_setting('ConnectionDetails', 'password', password)
        else:
            password = self.app.config.get('ConnectionDetails', 'password')
        conn_string = username + ';' + password + ";" + servername
        encoded = base64.b64encode(conn_string)
        self.app.config.update_setting('ConnectionDetails', 'conn_string', encoded)
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

        self.app.phone.add_proxy_config()
        self.app.phone.add_auth_info()
        self.app.phone.make_call(1001, self.app.config.get('ConnectionDetails', 'server'))
        lq_audio = self.app.phone.get_lq_start_time()
        print "passing lq_audio to gui: " + lq_audio


class ArtistJoiningScreen(Screen):
    app = ObjectProperty(None)

    def on_enter(self):
        self.app.update_role(constants.ARTIST)

    # TODO: Have GUI fill in pre-entered values
    #       Currently a blank field means use existing values, even if none exists
    def gettext(self, constring):
        global lq_audio
        try:
            decoded = base64.b64decode(constring)
            mark1 = decoded.find(';')
            mark2 = decoded.rfind(';')
            username = decoded[:mark1]
            password = decoded[mark1 + 1:mark2]
            server = decoded[mark2 + 1:]
            if server != '':
                self.app.config.update_setting('ConnectionDetails', 'server', server)
            if username != '':
                self.app.config.update_setting('ConnectionDetails', 'user', username)
            if password != '':
                self.app.config.update_setting('ConnectionDetails', 'password', password)

            self.parent.current = 'session'

            self.app.phone.add_proxy_config()
            self.app.phone.add_auth_info()
            self.app.phone.make_call(1001, self.app.config.get('ConnectionDetails', 'server'))
            lq_audio = self.app.phone.get_lq_start_time()
            print "passing lq_audio to gui: " + lq_audio

        except Exception as e:
            print "Error: " + str(e)
            error_message = 'Sorry, that string is not valid'
            popup = Popup(title='Connection String Error',
                          content=Label(text=error_message),
                          size_hint=(None, None), size=(400, 400))
            popup.open()


class SettingsScreen(Screen):
    app = ObjectProperty(None)

    def update_username(self, text_input):
        self.app.chat_client.username = text_input
        self.app.config.update_setting("Chat", "username", text_input)
        self.parent.ids.username_setting.text = ""


class FileTransferScreen(Screen):
    app = ObjectProperty(None)

    def on_enter(self):
        files = [["File 1", 60], ["File 2", 40], ["File 3", 80], ["File 4", 20]]
        for file in files:
            print(file[0])
            progress = ProgressBar(max=100)
            progress.value = file[1]
            filename = file[0]
            label = Label(text=filename, size_hint=(1/len(files), None))
            self.ids.filelayout.add_widget(label)
            self.ids.filelayout.add_widget(progress)

class ImageButton(ButtonBehavior, Image):
    pass

class ActionImageButton(ImageButton, ActionItem):
    pass

if __name__ == '__main__':
    HQC().run()
