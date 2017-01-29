import ConfigParser
import base64
import logging
import os.path
import sys

import linphone
from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QApplication


class HQCPhone:
    core = ''

    def __init__(self, config):
        global core
        logging.basicConfig(level=logging.INFO)

        def log_handler(level, msg):
            method = getattr(logging, level)
            method(msg)

        def global_state_changed(*args, **kwargs):
            logging.warning("global_state_changed: %r %r" % (args, kwargs))

        def registration_state_changed(core, call, state, message):
            logging.warning("registration_state_changed: " + str(state) + ", " + message)

        callbacks = {
            'global_state_changed': global_state_changed,
            'registration_state_changed': registration_state_changed,
        }

        linphone.set_log_handler(log_handler)
        core = linphone.Core.new(callbacks, None, None)
        core.video_capture_enabled = False  # remove both of these if we get video implemented
        core.video_display_enabled = False
        core.capture_device = config.input
        core.playback_device = config.output

    def parse_conn_string(self, conn_string):
        decoded = base64.b64decode(conn_string)
        mark1 = decoded.find(';')
        mark2 = decoded.rfind(';')
        username = decoded[:mark1]
        password = decoded[mark1 + 1:mark2]
        server = decoded[mark2 + 1:]
        return [username, password, server]

    def make_conn_string(self, username, password, server):
        # For now, conn_string will be sourced from conn.conf
        # Eventually, it will be passed in through the GUI
        # If the b64 encoded conn_strings get too long, we can try compressing them
        conn_string = username + ';' + password + ";" + server
        return base64.b64encode(conn_string)

    def make_call(self, number, server):
        params = core.create_call_params(None)
        params.record_file = './recording.snd'  # I have no idea what format it will dump into
        # Start recording with linphone.Call.start_recording()
        params.audio_enabled = True
        params.video_enabled = False

        url = 'sip:' + str(number) + '@' + server

        core.invite_with_params(url, params)

    # There is no separate array in core for recording and playback devices
    # Just this mega one.  At least there are checks for capabilities
    def get_playback_devices(self):
        arr = []
        for device in core.sound_devices:
            if core.sound_device_can_playback(device):
                arr += [device]
        return arr

    def get_recording_devices(self):
        arr = []
        for device in core.sound_devices:
            if core.sound_device_can_capture(device):
                arr += [device]

        return arr

    def add_proxy_config(self):
        proxy_cfg = core.create_proxy_config()
        proxy_cfg.identity_address = proxy_cfg.normalize_sip_uri("sip:" + config.username + "@" + config.server)
        proxy_cfg.server_addr = "sip:" + config.server
        proxy_cfg.register_enabled = True
        core.add_proxy_config(proxy_cfg)
        print "Added proxy config"

    def add_auth_info(self):
        auth_info = linphone.Core.create_auth_info(core,
                                                   config.username,
                                                   None,
                                                   config.password,
                                                   None,
                                                   None,
                                                   config.server)
        # References to linphone_auth_destroy() in api to securely delete auth_info?

        core.add_auth_info(auth_info)
        print "Added auth info"


class Config:
    confparse = ConfigParser.SafeConfigParser()
    file = None
    def __init__(self, file):
        self.file = file
        if not os.path.isfile(file):
            print "Creating config"
            f = open(file, 'w+')
            f.close()

        self.confparse.read(file)
        print 'Config contains '
        print self.confparse.items('ConnectionDetails')

        if not self.confparse.has_section('ConnectionDetails'):
            self.confparse.add_section('ConnectionDetails')

        if not self.confparse.has_section('Settings'):
            self.confparse.add_section('Settings')

        if not self.confparse.has_option('ConnectionDetails', 'username'):
            self.confparse.set('ConnectionDetails', 'username', 'None')

        # Risky stuff, best to remove in production
        if not self.confparse.has_option('ConnectionDetails', 'password'):
            self.confparse.set('ConnectionDetails', 'password', 'None')

        if not self.confparse.has_option('ConnectionDetails', 'server'):
            self.confparse.set('ConnectionDetails', 'server', 'None')

        if not self.confparse.has_option('Settings', 'mic'):
            self.confparse.set('Settings', 'mic', 'None')

        if not self.confparse.has_option('Settings', 'speakers'):
            self.confparse.set('Settings', 'speakers', 'None')

        f = open(file, 'r+')
        self.confparse.write(f)
        f.close()
        self.confparse.read(file)

    def write(self, section, option, value):
        self.confparse.set(section, option, value)
        f = open(self.file, 'r+')
        self.confparse.write(f)
        f.close()
        self.confparse.read(self.file)


if __name__ == '__main__':
    print "Making config object"
    config = Config('conn.conf')

    print "Making LinPhone.Core"
    phone = HQCPhone(config)

    print "Adding proxy config"
    phone.add_proxy_config()

    print "Adding authentication info"
    phone.add_auth_info()

    print "Dialing..."
    phone.make_call(1001, config.server)

    # Below this is timeout code.  Will sys.exit after some time.
    # Inherited from sample code, remove later.
    # Tried to remove this whole block and the call didn't work anymore.
    # I think everything is non blocking so we have to force the call to stay open.
    app = QApplication(sys.argv)
    iterate_timer = QTimer()
    iterate_timer.timeout.connect(core.iterate)
    stop_timer = QTimer()
    stop_timer.timeout.connect(app.quit)
    iterate_timer.start(20)
    stop_timer.start(50000)

    exitcode = app.exec_()
    sys.exit(exitcode)