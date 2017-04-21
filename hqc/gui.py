import os
import threading
import time
from datetime import datetime

from kivy.config import Config

# DO NOT MOVE THIS LINE, IT HAS TO BE AT THE TOP
Config.set('graphics', 'resizable', 0)  # This must occur before all other kivy imports

import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.uix.actionbar import ActionItem
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.togglebutton import ToggleButton

import audio
from HQCConfig import HQCConfig as hqc_config
from chat import constants
from chat.ChatClient import HQCWSClient
from hqc import HQCPhone

kivy.require('1.0.7')


class HQC(App):
    manager = ObjectProperty(None)
    """
    This represents the main application class
    """
    def __init__(self, **kwargs):
        super(HQC, self).__init__(**kwargs)
        self.config = hqc_config.get_instance(file="conn.conf")
        self.phone = HQCPhone(self.config)
        self.chat_client = None

        # Recorder object from audio module
        self.recorder = None
        # Recording directory
        self.storage_dir = self.config.get('AudioSettings', 'recording_location')
        self.session_name = datetime.now().strftime(constants.DATETIME_SESSION)
        self.audio_file_location = os.path.join(self.storage_dir, self.session_name)
        if not os.path.exists(self.audio_file_location):
            os.makedirs(self.audio_file_location)

        # color for gui text
        self.dark_blue = '2939b0'

    # Build should only handle setting up GUI-specific items
    def build(self):
        # Kivy is stubborn and overrides self.config with a built-in ConfigParser
        self.config = hqc_config.get_instance(file="conn.conf")
        # Give the web socket a reference to the app
        gui = Builder.load_file("HQC.kv")
        self.root = gui
        # Link application to Screen Manager
        self.root.app = self
        return gui

    def get_own_state(self):
        """
        Retrieves the username's own state from ChatClient
        :return: dict
        """
        return self.chat_client.states[self.chat_client.username]

    def get_latest_audio_file(self):
        return self.get_own_state()['audio_files'][-1]

    def update_chat(self, username, message):
        self.root.screens[3].update_chat(username, message)

    def update_role(self, role):
        self.config.update_setting("ChatSettings", "role", role)

    def update_requested_files(self, username, message):
        self.root.screens[3].update_requested_files(username, message)

    def update_send_files(self, username, message):
        self.root.screens[3].update_send_files(username, message)

    def update_available_files(self, username, filename, length):
        self.root.screens[3].update_available_files(username, filename, length)

    def add_audio_file(self, filename):
        """
        Adds an audio file path to the client state.
        :param filename: name of available file
        :return: None
        """
        self.get_own_state()['audio_files'].append(filename)


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
    stop_theme = '../img/stop_theme.png'
    record_black = '../img/record_black.png'
    record_red = '../img/record_theme2.png'

    # Store a large string of all chat messages
    chat_messages = StringProperty()

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
        btn = ToggleButton(background_normal='../img/play.png',
                           size_hint=(.18, 1), group='play', allow_stretch=False)
        btn.apply_property(clip_no=NumericProperty(SessionScreen.clip_no))
        btn.bind(on_press=self.play_clip)

        # add filename label
        audio_files = self.app.get_own_state()['audio_files']
        label = Label(text=os.path.basename(audio_files[-1])[0:9], halign='left', size_hint=(.5, 0.2))

        # add request button
        btn2 = Button(text="Request", size=(100, 50),
                      size_hint=(0.32, None))
        # Same clip number as play button
        btn2.apply_property(clip_no=NumericProperty(SessionScreen.clip_no))
        btn2.bind(on_press=self.request_file)

        self.ids.audioSidebar.add_widget(btn)
        self.ids.audioSidebar.add_widget(label)
        self.ids.audioSidebar.add_widget(btn2)

    def add_file(self, file):
        # Called when artist receives a sync request file
        if file not in self.requested_files and self.app.chat_client:
            print "Adding file" + file
            self.app.chat_client.send_sync(constants.SYNC_REQUEST_FILE, file)
        else:
            print "Chat client not connected"
        print self.requested_files

    def update_send_files(self, username, message):
        """
        Called upon when the user requests a file
        :param username: name of user requesting file
        :param message: string of files requested
        :return: None
        """
        if message in self.audio_files:
            self.app.chat_client.send_file(message)

    # TODO: GUI update - here is where the sidebar needs to be appended to
    def update_available_files(self, username, filename, length):
        _, tail = os.path.split(filename)
        print "{} has {}: {} bytes".format(username, tail, length)
        self.add_clip()

    def play_clip(self, obj):
        """
        Plays the selected file.
        :param obj: ToggleButton object
        :return:
        """
        # TODO: This plays LQ files, not HQ files.  Call get_audio_from_filename and also give it a length
        # Get filename of the high quality clip associated with this play button
        filename = self.app.get_own_state()['audio_files'][obj.clip_no]
        _, tail = os.path.split(filename)
        # Get base name
        # root, _ = os.path.splitext(tail)

        # Get filename of the session high quality audio stream
        hq_audio = self.app.config.get_file_name(self.app.session_name, tail)

        # Play audio for 5 seconds
        print "playing " + str(hq_audio)
        audio.playback(hq_audio, 0, None, 5)

    def request_file(self, obj):
        """
        Called upon when the user requests a file by clicking "Request" on a recording.
        :param obj: ToggleButton object
        :return: None
        """
        # Get filename of the high quality clip associated with this play button
        filename = self.app.get_own_state()['audio_files'][obj.clip_no]
        _, tail = os.path.split(filename)
        # Get base name
        # root, _ = os.path.splitext(tail)

        # Get filename of the session high quality audio stream
        hq_audio = self.app.config.get_file_name(self.app.session_name, tail)
        print "Requesting {}".format(tail)
        # Send a sync message to request a file.
        self.app.chat_client.send_sync(constants.SYNC_REQUEST_FILE,
                                       filename=tail)

    def record_button(self):
        """
        Records high quality audio files on the artist side.
        :return:
        """
        # Toggle recording
        rec_state = self.app.get_own_state()['recording']
        self.app.get_own_state()['recording'] = not rec_state

        if self.app.get_own_state()['recording']:
            # Update state
            self.app.chat_client.send_sync(constants.SYNC_START_RECORDING)
            # GUI update
            self.ids.record_button.source = SessionScreen.stop_theme
            # Start the progress effect
            progress_thread = threading.Thread(target=self.record_progress)
            progress_thread.start()

            filename = self.app.config.get_file_name(self.app.session_name,
                                                     datetime.now().strftime(constants.DATETIME_HQ))
            head, tail = os.path.split(filename)
            print "Creating: " + tail
            # Make sure folders exist
            if not os.path.exists(head):
                os.makedirs(head)
            # Makes a Recorder with the desired filename
            self.app.recorder = audio.Recorder(filename)
            # Add available audio file to state list
            self.app.add_audio_file(filename)
            # Starts writing to an audio file, including to disk
            self.app.recorder.start()  # Starts recording
            print "Recording..."
        else:
            # Update state
            self.app.chat_client.send_sync(constants.SYNC_STOP_RECORDING)
            # GUI update
            self.ids.record_button.source = SessionScreen.record_red
            # Closes recording threads
            self.app.recorder.stop()

            self.app.phone.stop_start_recording(datetime.now().strftime(constants.DATETIME_LQ))
            self.add_clip()  # adds to gui sidebar

            # Send a sync message for when a clip is available
            available_filename = self.app.get_latest_audio_file()
            self.app.chat_client.send_sync(constants.SYNC_FILE_AVAILABLE,
                                           filename=available_filename,
                                           length=audio.get_length(available_filename))

    def record_progress(self):
        while self.app.get_own_state()['recording']:
            time.sleep(0.05)
            self.ids.progress_bar.value = (self.ids.progress_bar.value + 1) % 31  # datetime.now().second % 6.0

    def toggle_mute(self):
        # Toggles the linphone mic
        self.app.phone.toggle_mic()

        # Update the mic image
        if self.app.phone.core.mic_enabled:
            self.app.chat_client.send_sync(constants.SYNC_MIC_ON)
            self.ids.mute_button.source = SessionScreen.un_muted_mic_image
        else:
            self.app.chat_client.send_sync(constants.SYNC_MIC_OFF)
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
        if self.app.get_own_state()['recording']:
            self.record_button()

class ProducerSessionScreen(SessionScreen):
    pass

class ArtistSessionScreen(SessionScreen):
    def add_clip(self):
        super(ArtistSessionScreen, self).add_clip()
        btn2 = Button(text="Request", size=(100, 50),
                      size_hint=(0.32, None))
        self.ids.audioSidebar.add_widget(btn2)

class ListenerSessionScreen(SessionScreen):
    pass

class ProducerJoiningScreen(Screen):
    app = ObjectProperty(None)

    def on_enter(self):
        self.app.update_role(constants.PRODUCER)

    # TODO: Have GUI fill in pre-entered values
    #       Currently a blank field means use existing values, even if none exists
    def get_conn(self, producer_connection):
        def is_valid(value):
            if value != '' and len(value) != 0:
                return True
            else:
                return False

        connection_details = self.app.config.get_section('ConnectionDetails')

        self.parent.current = 'producer_session'

        file_name = self.app.config.get_file_name(self.app.session_name, datetime.now().strftime(constants.DATETIME_LQ))
        self.app.phone.make_call(connection_details['call_no'], connection_details['server'], file_name)
        self.app.lq_audio = self.app.phone.recording_start
        print "passing lq_audio to gui: " + self.app.lq_audio

    def get_text(self, servername, username, password, callnumber):
        def is_valid(value):
            if value != '' and len(value) != 0:
                return True
            else:
                return False

        if is_valid(servername) and is_valid(username) and is_valid(password) and is_valid(callnumber):
            self.app.config.update_setting('ConnectionDetails', 'server', servername)
            self.app.config.update_setting('ConnectionDetails', 'user', username)
            self.app.config.update_setting('ConnectionDetails', 'password', password)
            self.app.config.update_setting('ConnectionDetails', 'call_no', callnumber)
            connection_details = {'server': servername, 'user': username, 'password': password, 'call_no': callnumber}

        else:
            connection_details = self.app.config.get_section('ConnectionDetails')

        # TODO: All of this code needs to be moved to another screen
        # The generation of connection strings should occur in a completely different screen
        # that is accessible from the main screen.  The producer should be able to enter in the 4 values
        # and it should output a connection string
        # conn_string = username + ';' + password + ";" + servername + ";" + callnumber
        # encoded = base64.b64encode(conn_string)
        # self.app.config.update_setting('ConnectionDetails', 'conn_string', encoded)
        # self.parent.current = 'session'
        #
        # # Make BoxLayout for multiple items
        # popup_box = BoxLayout(orientation='vertical')
        # # Make "Connection String" TextInput
        # popup_text = TextInput(text=encoded, size_hint=(1, .8))
        # popup_box.add_widget(popup_text)
        # # Make "Close" button for popup
        # close_button = Button(text='Close', size_hint=(.4, .2), pos_hint={'center_x': .5})
        # popup_box.add_widget(close_button)
        # popup = Popup(title='Connection String',
        #               content=popup_box,
        #               size_hint=(None, None), size=(400, 400),
        #               auto_dismiss=False)
        # close_button.bind(on_press=popup.dismiss)
        # # Open the popup
        # popup.open()

        self.parent.current = 'session'

        file_name = self.app.config.get_file_name(self.app.session_name, datetime.now().strftime(constants.DATETIME_LQ))
        self.app.phone.make_call(connection_details['call_no'], connection_details['server'], file_name)
        self.app.lq_audio = self.app.phone.recording_start
        print "passing lq_audio to gui: " + self.app.lq_audio


class ArtistJoiningScreen(Screen):
    app = ObjectProperty(None)

    def on_enter(self):
        self.app.update_role(constants.ARTIST)

    # TODO: Have GUI fill in pre-entered values
    #       Currently a blank field means use existing values, even if none exists

    def get_text(self, conn_string):
        if conn_string is not None and len(conn_string) != 0:  # Use the provided connection string
            connection_details = self.app.config.parse_conn_string()

            if not connection_details['server'] \
                    and not connection_details['user'] \
                    and not connection_details['password'] \
                    and not connection_details['call_no']:
                self.app.config.update_setting('ConnectionDetails', 'server', connection_details['server'])
                self.app.config.update_setting('ConnectionDetails', 'user', connection_details['user'])
                self.app.config.update_setting('ConnectionDetails', 'password', connection_details['password'])
                self.app.config.update_setting('ConnectionDetails', 'call_no', connection_details['call_no'])

            else:
                print "Bad connection string"
                error_message = 'Sorry, that string is not valid'
                popup = Popup(title='Connection String Error',
                              content=Label(text=error_message),
                              size_hint=(None, None), size=(400, 400))
                popup.open()

        else:  # Use the saved config values
            connection_details = self.app.config.get_section('ConnectionDetails')

            def is_valid(value):
                if value != '' and value != 'None' and value is not None:
                    return True
                return False

            if not is_valid(connection_details['server']) \
                    or not is_valid(connection_details['user']) \
                    or not is_valid(connection_details['password']) \
                    or not is_valid(connection_details['call_no']):
                # If the stored values aren't valid, nogood
                print "No connection string and bad config values"
                error_message = 'Sorry, the configuration is not valid'
                popup = Popup(title='Connection String Error',
                              content=Label(text=error_message),
                              size_hint=(None, None), size=(400, 400))
                popup.open()

        if self.app.config.get('ChatSettings', 'role') == "ARTIST":
            self.parent.current = 'artist_session'
        else:
            self.parent.current = 'listener_session'

        filename = self.app.config.get_file_name(self.app.session_name, datetime.now().strftime(constants.DATETIME_LQ))
        self.app.phone.make_call(connection_details['call_no'], connection_details['server'], filename)


class SettingsScreen(Screen):
    app = ObjectProperty(None)
    initialize = True
    recording_devices_main = Button(text='Default', size = (250, 75), size_hint = (None, None),
                                    halign="center", valign="middle")
    audio_devices_main = Button(text='Default', size = (250, 75), size_hint = (None, None),
                                halign="center", valign="middle")
    codec_main = Button(id='codec', text='Default', size = (250, 75), size_hint=(None, None),
                        halign="center", valign="middle")
    dropdown1 = DropDown(id='dropdown1')
    dropdown2 = DropDown(id='dropdown2')
    dropdown3 = DropDown(id='dropdown3')

    def save_settings(self, setting1):
        children = self.ids.devices.children[:]
        index = 0
        while children:
            child = children.pop()
            if index == 0:
                self.app.config.update_setting("AudioSettings", "mic", child.text)
            if index == 1:
                self.app.config.update_setting("AudioSettings", "speakers", child.text)
            if index == 2 and child.text == "Default":
                self.app.config.update_setting("LQRecordingSettings", "codec", "Default")
            if index == 2 and child.text != "Codec":
                codec = child.text
                newcodec = [codec[0:codec.find(',')]]
                newcodec += [codec[(codec.find(',')+ 1): codec.find("bps")]]
                newcodec += [codec[(codec.find("bps") + 3): codec.find("channels")]]
                self.app.config.update_setting("LQRecordingSettings", "codec", codec)
            index += 1
        if setting1 != '':
            self.app.config.update_setting("ChatSettings", "username", setting1)
        print self.app.config.get_section("AudioSettings")
        print self.app.config.get_section("LQRecordingSettings")

    def on_enter(self):
        if self.initialize:
            default1 = Button(text='Default', size_hint_y=None, height=60, halign="center", valign="middle")
            default2 = Button(text='Default', size_hint_y=None, height=60, halign="center", valign="middle")
            default3 = Button(text='Default', size_hint_y=None, height=60, halign="center", valign="middle")
            recording_devices = self.app.phone.get_recording_devices()
            recording_btns = [default1]

            for i in range(len(recording_devices)):
                btn1 = Button(text=recording_devices[i], size_hint_y=None, height = 60, halign="center", valign="middle")
                recording_btns = recording_btns + [btn1]
            for button in recording_btns:
                button.bind(size=button.setter('text_size'))
                button.bind(on_release=lambda btn: self.dropdown1.select(btn.text))
                self.dropdown1.add_widget(button)
            self.recording_devices_main.bind(on_release = self.dropdown1.open)
            self.dropdown1.bind(on_select = lambda instance, x: self.change_text(1, x))
            self.recording_devices_main.bind(size=self.recording_devices_main.setter('text_size'))
            self.ids.devices.add_widget(self.recording_devices_main)
            audio_devices = self.app.phone.get_playback_devices()
            audio_btns = [default2]
            for i in range(len(audio_devices)):
                btn2 = Button(text=audio_devices[i],  size_hint_y=None, height = 60, halign="center", valign="middle")
                audio_btns = audio_btns + [btn2]
            for button in audio_btns:
                button.bind(size=button.setter('text_size'))
                button.bind(on_release=lambda btn: self.dropdown2.select(btn.text))
                self.dropdown2.add_widget(button)
            self.audio_devices_main.bind(on_release = self.dropdown2.open)
            self.dropdown2.bind(on_select = lambda instance, x: self.change_text(2, x))
            self.audio_devices_main.bind(size=self.audio_devices_main.setter('text_size'))
            self.ids.devices.add_widget(self.audio_devices_main)
            codec = self.app.phone.get_codecs()
            codecbtns = [default3]
            for i in range(len(codec)):
                codec_text = str(codec[i][0]) + ", " + str(codec[i][1]) + "bps, " + str(codec[i][2]) + " channels"
                btn3 = Button(text=codec_text, size_hint_y=None, height = 60, halign="center", valign="middle")
                codecbtns = codecbtns + [btn3]
            for button in codecbtns:
                button.bind(size=button.setter('text_size'))
                button.bind(on_release=lambda btn: self.dropdown3.select(btn.text))
                self.dropdown3.add_widget(button)
            self.codec_main.bind(on_release=self.dropdown3.open)
            self.dropdown3.bind(on_select=lambda instance, x: self.change_text(3, x))
            self.codec_main.bind(size=self.codec_main.setter('text_size'))
            self.ids.devices.add_widget(self.codec_main)
            self.initialize = False

    def change_text(self, instance, x):
        if instance == 1:
            self.recording_devices_main.text = x
            self.recording_devices_main.text_size=self.recording_devices_main.size
        if instance == 2:
            setattr(self.audio_devices_main, 'text', x)
            self.audio_devices_main.text_size = self.audio_devices_main.size
        if instance == 3:
            setattr(self.codec_main, 'text', x)
            self.codec_main.text_size = self.codec_main.size
    def on_leave(self, *args):
        if self.recording_devices_main != 'Recording Devices':
            self.recording_devices_main.text = 'Recording Devices'
        if self.audio_devices_main != 'Audio Devices':
            self.audio_devices_main.text = 'Audio Devices'
        if self.codec_main != 'Codec':
            self.codec_main.text = 'Codec'


class FileTransferScreen(Screen):
    app = ObjectProperty(None)

    def on_enter(self):
        if self.app.config.get('ChatSettings', 'role') == "PRODUCER":
            files = self.app.get_own_state()['requested_files']
            for file in files:
                label = Label(text=file, size_hint=(1 / len(files), None))
                self.ids.filelayout.add_widget(label)
        elif self.app.config.get('ChatSettings', 'role') == "ARTIST":
            files = self.app.get_own_state()['requested_files']
            for file in files:
                full_path = self.app.config.get_file_name(self.app.session_name, file)
                self.app.chat_client.send_file(full_path)
                label = Label(text=file, size_hint=(1 / len(files), None))
                self.ids.filelayout.add_widget(label)

    def leave_session(self):
        self.app.chat_client.finish()
        self.app.phone.hangup()
        App.get_running_app().stop()

class ConnectionStringGenerationScreen(Screen):
    pass

# popup = Popup(title='Test popup',
#              content=Label(text='Hello world'),
#              size_hint=(None, None), size=(400, 400))
# popup.open()

# <ConnectionStringGenerationScreen>
#     name: "connection_string_generation_screen"
#     Image:
#         source: '../img/please_enter.png'
#         size_hint: (0.35, 0.35)
#         pos: (270, 440)
#     Image:
#         source: '../img/server_address.png'
#         size_hint: (0.28, 0.28)
#         pos: (70, 380)
#     Image:
#         source: '../img/username.png'
#         size_hint: (0.195, 0.195)
#         pos: (145, 330)
#     Image:
#         source: '../img/password.png'
#         size_hint: (0.16, 0.16)
#         pos: (160, 275)
#     Image:
#         source: '../img/call_number.png'
#         size_hint: (0.2, 0.2)
#         pos: (130, 190)

# ---

# ConnectionStringGenerationScreen:
#         manager: screen_manager
#         app: self.manager.app
#         canvas.before:
#             Color:
#                 rgba: 0.95, 0.95, 0.95, 0.95
#             Rectangle:
#                 pos: self.pos
#                 size: self.size
#         TextInput:
#             id: servername
#             size_hint: (.5, .1)
#             font_size: '24sp'
#             multiline: False
#             hint_text: 'servername'
#             pos: (330, 430)
#         TextInput:
#             id: callnumber
#             size_hint: (.5, .1)
#             font_size: '24sp'
#             multiline: False
#             password: False
#             hint_text: 'e.g. 1004'
#             pos: (330, 360)
#         TextInput:
#             id: username
#             size_hint: (.5, .1)
#             font_size: '24sp'
#             multiline: False
#             hint_text: 'your_username'
#             pos: (330, 290)
#         TextInput:
#             id: password
#             size_hint: (.5, .1)
#             font_size: '24sp'
#             multiline: False
#             password: True
#             hint_text: '********'
#             pos: (330, 220)
#         ImageButton:
#             id: producerjoinsess
#             source: '../img/enter_string.png'
#             halign: 'center'
#             valign: 'middle'
#             size_hint: (.25, .25)
#             text_size: root.width, None
#             font_size: '25sp'
#             pos: (275, 30)
#             on_release: self.parent.get_text(servername.text, username.text, password.text, callnumber.text)
#         ImageButton:
#             id: main_menu
#             source: '../img/arrow_left.png'
#             text: 'Main Menu'
#             halign: 'center'
#             valign: 'middle'
#             size_hint: (.20, .10)
#             text_size: root.width, None
#             font_size: '25sp'
#             pos: (-25, 510)
#             on_release: app.root.current = 'settings'

class ImageButton(ButtonBehavior, Image):
    pass


class ActionImageButton(ImageButton, ActionItem):
    pass

if __name__ == '__main__':
    HQC().run()
