import base64
import logging
import os
import time
from datetime import datetime

import linphone

from Config import Config

#  Load logging configuration from file
logging.config.fileConfig('../logging.conf')
#  Reference logger
linphone_logger = logging.getLogger('linphone')
debug_logger = logging.getLogger('debug')


class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instance


class HQCPhone(object):
    __metaclass__ = Singleton
    core = ''
    mic_gain = 0
    call = ''

    # For testing purposes, these are relative paths
    # For implementation, these are absolute paths as defined in the config
    # The initial LQ recording file, set in make_call
    recording_start = ''

    # The current LQ recording file, first set in make_call and later in stop_start_recording
    recording_current = ''

    # An array of filenames containing the actual filenames of finalized LQ recordings
    recording_locations = []

    def __init__(self, config):
        self.config = config

        def global_state_changed(*args, **kwargs):
            debug_logger.warning("global_state_changed: %r %r" % (args, kwargs))

        def registration_state_changed(core, call, state, message):
            debug_logger.warning("registration_state_changed: " + str(state) + ", " + message)
        callbacks = {
            'global_state_changed': global_state_changed,
            'registration_state_changed': registration_state_changed,
        }
        self.core = linphone.Core.new(callbacks, None, None)
        self.add_proxy_config()
        self.add_auth_info()

        def log_handler(level, msg):
            """
            Handles logging for linphone
            :param level: level of logging message (ex. INFO, DEBUG, ERROR)
            :param msg: message to be logged
            :return: None
            """
            #  Choose the appropriate logging handle
            debug_method = getattr(linphone_logger, 'info')
            debug_method(msg)

        linphone.set_log_handler(log_handler)
        self.core.video_capture_enabled = False  # remove both of these if we get video implemented
        self.core.video_display_enabled = False
        self.core.capture_device = self.config.get('AudioSettings', 'mic')
        self.core.playback_device = self.config.get('AudioSettings', 'speakers')

    @staticmethod
    def get_lq_start_time():
        print "====================================="
        print "=== WARNING: DEPRECIATED FUNCTION ==="
        print "===  Use self.recording_location  ==="
        print "====================================="

    def make_call(self, number, server, lq_file=datetime.now().strftime('%p_%I_%M_%S.wav')):
        """
        Make a SIP call to a number on a server
        :param number: number to call (should be a conference number)
        :param server: server which hosts the call
        :param lq_file: filename to store the LQ recordings
        :return:
        """
        params = self.core.create_call_params(None)
        params.record_file = self.recording_start = self.recording_current = lq_file
        # Output file (on devel sys) is constant 128Kbps 8kHz 16 bit 1 channel PCM
        params.audio_enabled = True
        params.video_enabled = False

        url = 'sip:' + str(number) + '@' + server

        self.call = self.core.invite_with_params(url, params)

        while self.call.media_in_progress():
            self.hold_open()

        # start_recording() is a linphone built-in function
        self.call.start_recording()

    def stop_start_recording(self, lq_file=datetime.now().strftime('%I_%M_%S.wav'), final=False):
        """
        Stops, then starts the LQ recording process. Recordings need to be finalized before they can be accessed.
        :param lq_file: New file name to record into
        :param final: If true, do not start the recording after stopping it.
        :return: the new recording location
        """
        def generate_name(path):
            """
            Generates a finalized pathname by appending an incrementing counter
            :param path: Path to update
            :return: Updated path name
            """
            absolute_path = os.path.abspath(path)
            file_name = os.path.basename(absolute_path)
            folder_name = os.path.dirname(absolute_path)
            # Add the number of the recording to the start of the file
            file_name = str(len(self.recording_locations)) + '_' + file_name
            return os.path.join(folder_name, file_name)

        self.call.stop_recording()
        # Move the file specified by recording_start into recording_current
        new_name = generate_name(self.recording_current)
        os.rename(self.recording_start, new_name)
        self.recording_locations.append(new_name)

        if not final:
            # Update the new recording file
            # Will still be recorded into recording_start, but allows us to rename it afterwards
            self.recording_current = lq_file
            self.call.start_recording()

    def mute_mic(self):
        """
        Handles muting the Linphone. core.mic_enable is built-in
        :return: None
        """
        self.core.mic_enabled = False

    def unmute_mic(self):
        """
        Handles un-muting the Linphone. core.mic_enable is built-in
        :return: None
        """
        self.core.mic_enabled = True

    def toggle_mic(self):
        self.core.mic_enabled = not self.core.mic_enabled

    def hold_open(self, total_time=-1, cycle_time=0.03):
        if total_time != -1:
            cycles = int(total_time / cycle_time)  # We don't care about being exact
            for i in range(0, cycles):
                self.core.iterate()
                time.sleep(cycle_time)
        else:
            self.core.iterate()
            time.sleep(cycle_time)  # I don't know why this value but it's what is used in RPi Example Code

    def get_playback_devices(self):
        """
        Retrieves references to all available playback devices
        :return: list of playback device strings
        """
        playback_devices = []
        # Get the available sound devices
        for device in self.core.sound_devices:
            # Check if the device can play sound
            if self.core.sound_device_can_playback(device):
                playback_devices.append(device)
        return playback_devices

    # TODO: add call to reload_sound_devices() somewhere
    # This refreshes the list of available sound devices (such as USB event)
    def get_recording_devices(self):
        """
        Retrieves references to all available recording devices
        :return: list of recording device strings
        """
        recording_devices = []
        for device in self.core.sound_devices:
            if self.core.sound_device_can_capture(device):
                recording_devices.append(device)
        return recording_devices

    def get_codecs(self):
        """
        Retrieves all available codecs
        :return: An array of lists containing codec details
        """
        printable_codecs = []
        for codec in self.core.audio_codecs:
            printable_codec = [codec.mime_type, codec.normal_bitrate, codec.channels]
            printable_codecs.append(printable_codec)

        for printable_codec in printable_codecs:
            print printable_codec

    def force_codec_type(self, codec):
        """
        Disables all codecs except for the specified codec.  If the specified codec is not found, enable all codecs
        :param codec: an array returned from get_codecs
        :return: 1 on success, 0 on failure (no matching codec)
        """
        # Cannot reliably use core.find_audio_codec due to issue with bitrate selection
        selected_codec = -1
        for payload in self.core.audio_codecs:
            if payload.mime_type == codec[0]:
                if payload.normal_bitrate == codec[1]:
                    if payload.channels == codec[2]:
                        selected_codec = payload

        # We double iterate audio_codecs because if we can't find a matching codec we don't want to disable everything
        if selected_codec != -1:
            # We found a matching codec
            for payload in self.core.audio_codecs:
                if not self.codecs_match(payload, selected_codec):
                    self.core.enable_payload_type(payload, False)
                else:
                    self.core.enable_payload_type(payload, True)
            return 1
        else:
            return 0

    def codecs_match(self, codec1, codec2):
        """
        Determines if two codecs are the same
        For whatever reason, 
            a = self.core.audio_codec[0]
            a in self.core.audio_codec
            > false
        :param codec1: The first codec
        :param codec2: The second codec
        :return: true if the codecs match, false if they don't
        """
        if codec1.mime_type == codec2.mime_type:
            if codec1.normal_bitrate == codec2.normal_bitrate:
                if codec1.channels == codec2.channels:
                    return True
        return False

    def add_proxy_config(self):
        proxy_cfg = self.core.create_proxy_config()
        proxy_cfg.identity_address = proxy_cfg.normalize_sip_uri("sip:" +
                                                                 self.config.get('ConnectionDetails', 'user') +
                                                                 "@" +
                                                                 self.config.get('ConnectionDetails', 'server'))
        proxy_cfg.server_addr = "sip:" + self.config.get('ConnectionDetails', 'server')
        proxy_cfg.register_enabled = True
        self.core.add_proxy_config(proxy_cfg)
        debug_logger.info("Added proxy config")

    def add_auth_info(self):
        auth_info = self.core.create_auth_info(self.config.get('ConnectionDetails', 'user'),
                                               None,
                                               self.config.get('ConnectionDetails', 'password'),
                                               None,
                                               None,
                                               self.config.get('ConnectionDetails', 'server'))
        # References to linphone_auth_destroy() in api to securely delete auth_info?

        self.core.add_auth_info(auth_info)
        debug_logger.info("Added auth info")


def parse_conn_string(conn_string):
    """
    Decode the connection string and return its elements
    :param conn_string: Base64 encoded connection string
    :return: List containing decoded username, password, and server
    """
    decoded = base64.b64decode(conn_string)
    mark1 = decoded.find(';')
    mark2 = decoded.rfind(';')
    username = decoded[:mark1]
    password = decoded[mark1 + 1:mark2]
    server = decoded[mark2 + 1:]
    return [username, password, server]


def make_conn_string(username, password, server):
    """
    Given a username, password, and server address, base64 encode them together
    :param username: username (or phone number) to register to the SIP server
    :param password: password associated with the username
    :param server: IP or hostname of the SIP server
    :return: a base 64 encoded string containing all parameters
    """
    conn_string = username + ';' + password + ";" + server
    return base64.b64encode(conn_string)

if __name__ == '__main__':
    def test_lq_recording_toggle():
        # This code should generate two 2 second low quality recordings
        dial_conference_no()

        phone.hold_open(5)
        phone.stop_start_recording()
        phone.hold_open(5)
        phone.stop_start_recording(final=True)
        phone.hold_open()

    def dial_conference_no():
        debug_logger.info("Adding proxy config")
        phone.add_proxy_config()

        debug_logger.info("Adding authentication info")
        phone.add_auth_info()

        debug_logger.info("Dialing...")
        phone.make_call(2000, config.get('ConnectionDetails', 'server'))


    def test_codec_selection():
        print phone.force_codec_type(['opus', 20000, 2])

        test_codec = []
        for codec in phone.core.audio_codecs:
            test_codec.append(
                [phone.core.payload_type_enabled(codec), codec.mime_type, codec.normal_bitrate, codec.channels])
        for codec in test_codec:
            print codec


    def test_custom_hold_open_and_mic_status():
        dial_conference_no()

        while True:
            phone.hold_open(5)
            phone.mute_mic()
            phone.hold_open(2)
            phone.unmute_mic()
            phone.hold_open(10)


    def make_core_objects():
        config = Config('conn.conf')

        debug_logger.info("Making LinPhone.Core")
        phone = HQCPhone(config)
        return phone, config


    phone, config = make_core_objects()
    test_lq_recording_toggle()
