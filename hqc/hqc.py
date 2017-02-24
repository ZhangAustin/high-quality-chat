import base64
import Config
import logging
import logging.handlers
from logging.config import fileConfig
import os.path
import time
import linphone

#  Load logging configuration from file
logging.config.fileConfig('../logging.conf')
#  Reference logger
linphone_logger = logging.getLogger('linphone')
debug_logger = logging.getLogger('debug')


class HQCPhone:
    core = ''
    config = ''
    mic_gain = 0
    call = ''

    def __init__(self, config):
        self.config = config

        #  Handles logging for linphone
        def log_handler(level, msg):
            #  Choose the appropriate logging handle
            debug_method = getattr(linphone_logger, level)
            debug_method(msg)

        def global_state_changed(*args, **kwargs):
            debug_logger.warning("global_state_changed: %r %r" % (args, kwargs))

        def registration_state_changed(core, call, state, message):
            debug_logger.warning("registration_state_changed: " + str(state) + ", " + message)

        callbacks = {
            'global_state_changed': global_state_changed,
            'registration_state_changed': registration_state_changed,
        }

        linphone.set_log_handler(log_handler)
        self.core = linphone.Core.new(callbacks, None, None)
        self.core.video_capture_enabled = False  # remove both of these if we get video implemented
        self.core.video_display_enabled = False
        self.core.capture_device = config.get('Settings', 'mic')
        self.core.playback_device = config.get('Settings', 'speakers')

    @staticmethod
    def parse_conn_string(conn_string):
        decoded = base64.b64decode(conn_string)
        mark1 = decoded.find(';')
        mark2 = decoded.rfind(';')
        username = decoded[:mark1]
        password = decoded[mark1 + 1:mark2]
        server = decoded[mark2 + 1:]
        return [username, password, server]

    @staticmethod
    def make_conn_string(username, password, server):
        # For now, conn_string will be sourced from conn.conf
        # Eventually, it will be passed in through the GUI
        # If the b64 encoded conn_strings get too long, we can try compressing them
        conn_string = username + ';' + password + ";" + server
        return base64.b64encode(conn_string)

    def make_call(self, number, server):
        params = self.core.create_call_params(None)
        params.record_file = './recording.snd'  # I have no idea what format it will dump into
        # Start recording with linphone.Call.start_recording()
        params.audio_enabled = True
        params.video_enabled = False

        url = 'sip:' + str(number) + '@' + server

        self.call = self.core.invite_with_params(url, params)

    def mute_mic(self):
        self.mic_gain = self.call.microphone_volume_gain
        self.call.microphone_volume_gain = -1000.0

    def unmute_mic(self):
        self.call.microphone_volume_gain = self.mic_gain

    def hold_open(self):
        self.core.iterate()
        time.sleep(0.03)  # I don't know why this value but it's what is used in RPi Example Code

    # There is no separate array in core for recording and playback devices
    # Just this mega one.  At least there are checks for capabilities
    def get_playback_devices(self):
        arr = []
        for device in self.core.sound_devices:
            if self.core.sound_device_can_playback(device):
                arr += [device]
        return arr

    def get_recording_devices(self):
        arr = []
        for device in self.core.sound_devices:
            if self.core.sound_device_can_capture(device):
                arr += [device]

        return arr

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


if __name__ == '__main__':
    debug_logger.debug("Importing config object")
    #  Reference config settings from Config
    config = Config.config

    debug_logger.info("Making LinPhone.Core")
    phone = HQCPhone(config)

    debug_logger.info("Adding proxy config")
    phone.add_proxy_config()

    debug_logger.info("Adding authentication info")
    phone.add_auth_info()

    debug_logger.info("Dialing...")
    phone.make_call(1001, config.get('ConnectionDetails', 'server'))

    while True:
        phone.hold_open()
