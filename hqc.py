# This is sample code retrieved from
# http://pythonhosted.org/linphone/getting_started.html#running-some-code
# It sets up and tears down a linphone.Core object

# WINDOWS DEPENDENCIES
# pip install linphone
# Select the proper PyQt version
#   cpXX = python version X.X
#   win32 vs win_amd64 = architecture of Python (not OS or CPU)
# pip install PyQt4-*.whl

import ConfigParser
import logging
import sys

import linphone
from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QApplication


def main():
    confparse = ConfigParser.SafeConfigParser()
    confparse.read('conn.conf')
    # Currently, config contains username, password, and server address
    username = confparse.get('ConnectionDetails', 'user')
    password = confparse.get('ConnectionDetails', 'password')
    server = confparse.get('ConnectionDetails', 'server')

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
    proxy_cfg = core.create_proxy_config()
    proxy_cfg.identity_address = proxy_cfg.normalize_sip_uri("sip:" + username + "@" + server)
    proxy_cfg.server_addr = "sip:" + server
    proxy_cfg.register_enabled = True

    auth_info = linphone.Core.create_auth_info(core, username, None, password, None, None, server)
    # auth_info.username = username
    # auth_info.password = password
    # auth_info.domain = server

    core.add_proxy_config(proxy_cfg)
    core.add_auth_info(auth_info)

    iterate_timer = QTimer()
    iterate_timer.timeout.connect(core.iterate)
    stop_timer = QTimer()
    stop_timer.timeout.connect(app.quit)
    iterate_timer.start(20)
    stop_timer.start(5000)

    exitcode = app.exec_()
    sys.exit(exitcode)


main()
