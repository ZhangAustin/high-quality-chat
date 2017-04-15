import base64
import os
import threading
import time
from datetime import datetime

import kivy
from kivy.app import App
from kivy.config import Config
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.uix.actionbar import ActionItem
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton

import audio
from Config import Config
from chat import constants
from chat.ChatClient import HQCWSClient
from hqc import HQCPhone

# audioClipLayout = GridLayout(cols=3, padding=10, spacing=5,
#                     size_hint=(None, None), width=310)
# layout2 = GridLayout(cols=1, padding=10, spacing=5,
#                      size_hint=(None, None), width=410)

# TODO: REMOVE GLOBAL VARIABLES. Put them in the config, a class definition, or default parameter.
start_recording = False
filenames = []
recorder = None
progress = False
kivy.require('1.0.7')


class HQC(App):
    manager = ObjectProperty(None)
    """
    This represents the main application class
    """
    def __init__(self, **kwargs):
        super(HQC, self).__init__(**kwargs)
        self.config = Config("conn.conf")
        self.phone = HQCPhone(self.config)
        self.chat_client = None
        # Recorder object from audio module
        self.recorder = None
        # Boolean of whether or not the user is recording
        self.recording = False
        # TODO: Description
        self.lq_audio = None

    # Build should only handle setting up GUI-specific items
    def build(self):
        # Kivy is stubborn and overrides self.config with a built-in ConfigParser
        self.config = Config("conn.conf")
        # Give the web socket a reference to the app
        gui = Builder.load_file("HQC.kv")
        self.root = gui
        # Link application to Screen Manager
        self.root.app = self
        return gui

    def update_chat(self, username, message):
        self.root.screens[3].update_chat(username, message)

    def update_role(self, role):
        self.config.update_setting("ChatSettings", "role", role)

    def update_requested_files(self, username, message):
        self.root.screens[3].update_requested_files(username, message)

    def update_send_files(self, username, message):
        self.root.screens[3].update_send_files(username, message)


class MainScreen(Screen):
    app = ObjectProperty(None)
    pass


class ScreenManager(ScreenManager):
    app = ObjectProperty(None)


class SessionScreen(Screen):
    # Used for giving each audio clip a unique ID
    clip_no = -1
    # Used to reference app
    app = ObjectProperty(None)

    un_muted_mic_image = '../img/microphone.png'
    muted_mic_image = '../img/muted.png'

    stop_black = '../img/stop_black.png'
    record_black = '../img/record_black.png'
    record_red = '../img/record_red.png'

    # Store a large string of all chat messages
    chat_messages = StringProperty()

    # List of audio file names
    audio_files = []
    requested_files = []

    def on_enter(self):

        # when we add children to the grid layout, its size doesn't change at
        # all. we need to ensure that the height will be the minimum required
        # to contain all the childs. (otherwise, we'll child outside the
        # bounding box of the childs)
        self.ids.audioSidebar.bind(minimum_height=self.ids.audioSidebar.setter('height'))
        progress_bar = ProgressBar( value=0, size_hint= (0.5, None))
        label = Label(text = 'Waiting', size_hint= (0.32, None))
        label2 = Label(text='N/A%', size_hint= (0.18, None))
        self.ids.audioSidebar.add_widget(label2)
        self.ids.audioSidebar.add_widget(progress_bar)
        self.ids.audioSidebar.add_widget(label)
        self.app.chat_client = HQCWSClient(self.app.config)
        self.app.chat_client.app = self.app
        self.app.chat_client.config = self.app.config
        # create a scroll view, with a size < size of the grid
        # root = ScrollView(size_hint=(None, None), size=(310, 460),
        #                   pos_hint={'center_x': .5, 'center_y': .5}, do_scroll_x=False)
        # root.add_widget(audioClipLayout)
        # self.ids.audioSidebar.add_widget(root)

    def add_clip(self):
        # Generate the index number of the clip for referencing in filenames
        SessionScreen.clip_no += 1

        # add play button and filename index # for later playback
        btn = ToggleButton(background_normal= '../img/play.png',
                   size_hint=(.18, 1), group = 'play', allow_stretch=False)
        btn.apply_property(clip_no=NumericProperty(SessionScreen.clip_no))
        btn.bind(on_press=self.play_clip)

        # add filename label
        label = Label(text=os.path.basename(self.audio_files[-1])[0:9], halign='left', size_hint=(.5, 0.2))

        # add request button
        filename = self.audio_files[-1]
        print self.audio_files[-1]
        btn2 = Button(text="Request", size=(100, 50),
                      size_hint=(0.32, None))

        self.ids.audioSidebar.add_widget(btn)
        self.ids.audioSidebar.add_widget(label)
        self.ids.audioSidebar.add_widget(btn2)

    def add_file(self, file):
        if file not in self.requested_files:
            if self.app.chat_client:
                print "Adding file" + file
                self.app.chat_client.send_sync(constants.SYNC_REQUESTFILE, file)
            else:
                print "Chat client not connected"
        print self.requested_files

    def update_requested_files(self, username, message):
        """
        Called upon when the user requests a file
        :param username: name of user requesting file
        :param message: string of file requested
        :return: None
        """
        print message
        self.requested_files += [message]

    def update_send_files(self, username, message):
        """
        Called upon when the user requests a file
        :param username: name of user requesting file
        :param message: string of files requested
        :return: None
        """
        if message in self.audio_files:
            self.app.chat_client.send_file(message)

    def play_clip(self, obj):

        # Get filename of the high quality clip associated with this play button
        # TODO: explain what obj.np is/does
        filename = self.audio_files[obj.clip_no]

        # Get filename of the session low quality audio stream
        lq_audio = self.app.lq_audio

        # get the # seconds after playback that HQ clip starts in the LQ stream:
        # HQ start time in s - LQ start time in s (= int)
        start_time_seconds = int(lq_audio[3:5]) * 3600 + int(lq_audio[6:8]) * 60 + int (lq_audio[9:11])
        filename_seconds = int(filename[3:5]) * 3600 + int(filename[6:8]) * 60 + int (filename[9:11])

        # gets the offset in seconds of the HQ file start time from the LQ stream
        hq_start_time = filename_seconds - start_time_seconds
        print filename + " session offset: " + str(hq_start_time) + " seconds"
        # gets the file associated with this button's label friend

        # audio.get_length(filename)
        # audio.playback(lq_audio, hq_start_time, None, 2)

    def record_button(self):

        # Toggle recording
        self.app.recording = not self.app.recording

        if self.app.recording:
            self.ids.record_button.source = SessionScreen.stop_black

            global progress
            progress = True
            mythread = threading.Thread(target=self.record_progress)
            mythread.start()

            filename = self.app.config.get_file_name(datetime.now().strftime('HQ_%H%M%S.mp3'))
            self.app.recorder = audio.Recorder(filename)  # creates audio file
            self.audio_files.append(filename)  # adds filename to global list
            self.app.recorder.start()  # Starts recording
            print "Recording..."
        else:
            progress = False
            self.ids.record_button.source = SessionScreen.record_red
            self.app.recorder.stop()
            self.add_clip()  # adds to gui sidebar
            print "Done recording"

    def record_progress(self):
        global progress
        while progress:
            time.sleep(0.05)
            self.ids.progress_bar.value = (self.ids.progress_bar.value + 1) % 31  # datetime.now().second % 6.0

    def toggle_mute(self):
        # Toggles the linphone mic
        self.app.phone.toggle_mic()

        # Update the mic image
        if self.app.phone.core.mic_enabled:
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

    def on_leave(self, *args):
        """
        Makes sure the SessionScreen is left properly
        :param args: 
        :return: 
        """
        # If leaving the SessionScreen, make sure to stop recording
        if self.app.recording:
            self.record_button()


class ProducerJoiningScreen(Screen):
    app = ObjectProperty(None)

    def on_enter(self):
        self.app.update_role(constants.PRODUCER)

    # TODO: Have GUI fill in pre-entered values
    #       Currently a blank field means use existing values, even if none exists
    def get_text(self, servername, username, password, callnumber):

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
        if callnumber != '':
            self.app.config.update_setting('ConnectionDetails', 'call_no', callnumber)
        else:
            callnumber = self.app.config.get('ConnectionDetails', 'call_no')
        conn_string = username + ';' + password + ";" + servername + ";" + callnumber
        encoded = base64.b64encode(conn_string)
        self.app.config.update_setting('ConnectionDetails', 'conn_string', encoded)
        self.parent.current = 'session'

        # Make BoxLayout for multiple items
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
        file_name = self.app.config.get_file_name(datetime.now().strftime('LQ_%H%M%S.wav'))
        self.app.phone.make_call(callnumber, self.app.config.get('ConnectionDetails', 'server'), file_name)
        self.app.lq_audio = self.app.phone.recording_start
        print "passing lq_audio to gui: " + self.app.lq_audio


class ArtistJoiningScreen(Screen):
    app = ObjectProperty(None)

    def on_enter(self):
        self.app.update_role(constants.ARTIST)

    # TODO: Have GUI fill in pre-entered values
    #       Currently a blank field means use existing values, even if none exists
    def get_text(self, conn_string):
        if conn_string is not None:
            # TODO: Why is this done manually? There are functions for this
            decoded = base64.b64decode(conn_string)
            mark1 = decoded.find(';')
            mark2 = decoded.rfind(';')
            mark3 = decoded.rfind(';')
            username = decoded[:mark1]
            password = decoded[mark1 + 1:mark2]
            server = decoded[mark2 + 1:mark3]
            callnumber = decoded[mark3 + 1:]

            if server != '':
                self.app.config.update_setting('ConnectionDetails', 'server', server)
            if username != '':
                self.app.config.update_setting('ConnectionDetails', 'user', username)
            if password != '':
                self.app.config.update_setting('ConnectionDetails', 'password', password)
            if callnumber != '':
                self.app.config.update_setting('ConnectionDetails', 'call_no', callnumber)
            self.parent.current = 'session'

            self.app.phone.add_proxy_config()
            self.app.phone.add_auth_info()
            # TODO: Update make_call, it now takes a mandatory file name
            filename = self.app.config.get_file_name(datetime.now().strftime('LQ_%H%M%S.mp3'))
            self.app.phone.make_call(callnumber, self.app.config.get('ConnectionDetails', 'server'), filename)
            self.app.lq_audio = self.app.phone.recording_start
            print "passing lq_audio to gui: " + self.app.lq_audio

        else:
            error_message = 'Sorry, that string is not valid'
            popup = Popup(title='Connection String Error',
                          content=Label(text=error_message),
                          size_hint=(None, None), size=(400, 400))
            popup.open()


class SettingsScreen(Screen):
    app = ObjectProperty(None)

    def update_username(self, text_input):
        self.app.chat_client.username = text_input
        self.app.config.update_setting("ChatSettings", "username", text_input)
        self.parent.ids.username_setting.text = ""


class FileTransferScreen(Screen):
    app = ObjectProperty(None)

    def on_enter(self):
        if self.app.config.get('ChatSettings', 'role') == "PRODUCER":
            files = self.app.root.screens[3].requested_files
            for file in files:
                label = Label(text=file, size_hint=(1 / len(files), None))
                self.ids.filelayout.add_widget(label)
        elif self.app.config.get('ChatSettings', 'role') == "ARTIST":
            files = self.app.root.screens[3].requested_files
            for file in files:
                self.app.chat_client.send_file(file)
                label = Label(text=file, size_hint=(1 / len(files), None))
                self.ids.filelayout.add_widget(label)

    def leave_session(self):
        self.app.chat_client.finish()
        self.app.phone.hangup()
        App.get_running_app().stop()

class ImageButton(ButtonBehavior, Image):
    pass


class ActionImageButton(ImageButton, ActionItem):
    pass

if __name__ == '__main__':
    HQC().run()
