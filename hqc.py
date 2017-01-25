import ConfigParser
import base64
import logging
import sys

import linphone
from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QApplication


def main():
    # Parse and load the config
    # This is for ease of testing and will be replaced with a GUI conn_string input
    confparse = ConfigParser.SafeConfigParser()
    confparse.read('conn.conf')
    config_username = confparse.get('ConnectionDetails', 'user')
    config_password = confparse.get('ConnectionDetails', 'password')
    config_server = confparse.get('ConnectionDetails', 'server')
    config_capture = confparse.get('Settings', 'mic')

    # Create the conn_string.
    # This is for testing only.  Eventually only the producer will be able to do this.
    # We will also probably have to revise what 'starting a server' looks like.
    # We will probably have to give the client config files that matches his infrastructure.
    # We might have this server in the cloud or installed locally, depending on how the client feels.
    conn_string = make_conn_string(config_username, config_password, config_server)

    # Parse the conn string
    values = parse_conn_string(conn_string)
    username = values[0]
    password = values[1]  # There is an option to pass a pre-hashed password into create_auth_info
    server = values[2]

    logging.basicConfig(level=logging.INFO)

    app = QApplication(sys.argv)

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
    core.capture_device = config_capture
    proxy_cfg = core.create_proxy_config()
    proxy_cfg.identity_address = proxy_cfg.normalize_sip_uri("sip:" + username + "@" + server)
    proxy_cfg.server_addr = "sip:" + server
    proxy_cfg.register_enabled = True

    auth_info = linphone.Core.create_auth_info(core, username, None, password, None, None, server)
    # References to linphone_auth_destroy() in api to securely delete auth_info?

    core.add_proxy_config(proxy_cfg)
    core.add_auth_info(auth_info)

    make_call(core, 1001, server)

    # Below this is timeout code.  Will sys.exit after some time.
    # Inherited from sample code, remove later.
    # Tried to remove this whole block and the call didn't work anymore.
    # I think everything is non blocking so we have to force the call to stay open.
    iterate_timer = QTimer()
    iterate_timer.timeout.connect(core.iterate)
    stop_timer = QTimer()
    stop_timer.timeout.connect(app.quit)
    iterate_timer.start(20)
    stop_timer.start(50000)

    exitcode = app.exec_()
    sys.exit(exitcode)


def parse_conn_string(conn_string):
    decoded = base64.b64decode(conn_string)
    mark1 = decoded.find(';')
    mark2 = decoded.rfind(';')
    username = decoded[:mark1]
    password = decoded[mark1 + 1:mark2]
    server = decoded[mark2 + 1:]
    return [username, password, server]


def make_conn_string(username, password, server):
    # For now, conn_string will be sourced from conn.conf
    # Eventually, it will be passed in through the GUI
    # If the b64 encoded conn_strings get too long, we can try compressing them
    conn_string = username + ';' + password + ";" + server
    return base64.b64encode(conn_string)


def make_call(core, number, server):
    params = core.create_call_params(None)
    params.record_file = './recording.snd'  # I have no idea what format it will dump into
    # Start recording with linphone.Call.start_recording()
    params.audio_enabled = True
    params.video_enabled = False

    url = 'sip:' + str(number) + '@' + server

    core.invite_with_params(url, params)


main()
