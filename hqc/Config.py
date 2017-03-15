import ConfigParser
import logging.config
import os

#  Load logging configuration from file
logging.config.fileConfig('../logging.conf')
#  Reference logger
debug_logger = logging.getLogger('debugLog')


#  Inherits methods such as get() from SafeConfigParser
class Config(ConfigParser.SafeConfigParser):
    """Handles creation and updating of configuration settings."""
    def __init__(self, file):
        """
        Initializes config file at location given or with file already at location given.
        :param file: File path to either create new config file or of already existing config file to use.
        """
        ConfigParser.SafeConfigParser.__init__(self)
        self.file = file
        if not os.path.isfile(self.file):
            logging.warning("Creating config")
            # Touch the file
            with open(file, 'a'):
                os.utime(file, None)

        self.read(self.file)
        self.check()

        with open(self.file, 'w') as config_file:
            self.write(config_file)

    def check(self):
        """
        Checks the config file and ensure all sections exist
        If not, add the sections and initialize to "None"
        """

        connection = ['user', 'password', 'server', 'role', 'call_no', 'username']
        # User: username to SIP register to the server with.  This will likely be a number but will always be set up
        #       on the SIP server
        # Password: password associated with the SIP account trying to be registered
        # Server: IP or domain name of the SIP server.  Currently expects the SIP server to be on port 5060
        # Role: Role to register on the server with.  Check constants.py for mappings
        #       Note: This should be set when the role button is clicked and used in the chat objects
        # Call_No: Number to call once registered on the SIP server.  This should be a conference number set up on
        #          the SIP server
        # Username: Preferred name to be displayed in the application.  This affects display and some usage in chat
        #           objects

        settings = ['mic', 'speakers', 'recording_location']
        # Mic: Selected from a dropdown menu of recording devices populated from hqc.Phone function
        # Speakers: Selected from a dropdown menu of output devices populated form hqc.Phone function
        # Recording_location: Path to storage of sessions and recording files

        sections = {'ConnectionDetails': connection, 'Settings': settings}

        for section in sections:
            if not self.has_section(section):
                self.add_section(section)
            for option in sections[section]:
                if not self.has_option(section, option):
                    self.set(section, option, "None")

    def update_setting(self, section, option, value):
        """
        Add or update settings to config file.
        :param section: Section of setting to update/add, will be added if does not exist
        :param option: Desired setting to update/add
        :param value: Value to set setting to
        :return: None
        """
        self.read(self.file)
        #  Add a section if one does not exist
        if not self.has_section(section):
            self.add_section(section)
        #  Add/update the desired setting
        self.set(section, option, value)
        #  Write the settings back to disk
        with open(self.file, "w") as config_file:
            self.write(config_file)

# WARNING: DO NOT Initialize Config on import. Create a config object with custom parameters.
# config = Config("conn.conf")
