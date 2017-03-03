import base64
import Config
import linphone
import logging.handlers
import time

#  Load logging configuration from file
logging.config.fileConfig('../logging.conf')
#  Reference logger
linphone_logger = logging.getLogger('linphone')
debug_logger = logging.getLogger('debug')
#  Reference config settings from Config
config = Config.config


class HQCPhone(object):
    core = ''
    config = ''
    mic_gain = 0
    call = ''

    def __init__(self, config):
        self.config = config

        def log_handler(level, msg):
            """
            Handles logging for linphone
            :param level: level of logging message (ex. INFO, DEBUG, ERROR)
            :param msg: message to be logged
            :return: None
            """
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

    def make_call(self, number, server, lq_file='recording.wav'):
        """
        Make a SIP call to a number on a server
        :param number: number to call (should be a conference number)
        :param server: server which hosts the call
        :param lq_file: filename to store the LQ recordings
        :return:
        """
        params = self.core.create_call_params(None)
        params.record_file = lq_file
        # Output file (on devel sys) is constant 128Kbps 8kHz 16 bit 1 channel PCM
        params.audio_enabled = True
        params.video_enabled = False

        url = 'sip:' + str(number) + '@' + server

        self.call = self.core.invite_with_params(url, params)

        while self.call.media_in_progress():
            self.hold_open()

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
    debug_logger.info("Making LinPhone.Core")
    phone = HQCPhone(config)

    debug_logger.info("Adding proxy config")
    phone.add_proxy_config()

    debug_logger.info("Adding authentication info")
    phone.add_auth_info()

    debug_logger.info("Dialing...")
    phone.make_call(1001, config.get('ConnectionDetails', 'server'))

    while True:
        phone.hold_open(5)
        phone.mute_mic()
        phone.hold_open(2)
        phone.unmute_mic()
        phone.hold_open(10)
