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
            f = open(file, 'w')
            f.close()

        self.read(self.file)
        self.check()

        with open(self.file, 'w') as config_file:
            self.write(config_file)

    def check(self):
        """
        Checks the config file and ensure all sections exist
        If not, add the sections and initialize to "None"
        """
        connection = ['user', 'password', 'server', 'role']
        settings = ['mic', 'speakers', 'recording_location']
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
#config = Config("conn.conf")
