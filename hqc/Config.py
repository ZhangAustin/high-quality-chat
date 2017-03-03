import ConfigParser
from logging.config import fileConfig
import logging
import os

#  Load logging configuration from file
logging.config.fileConfig('../logging.conf')
#  Reference logger
debug_logger = logging.getLogger('debugLog')


class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instance


#  Inherits methods such as get() from SafeConfigParser
class Config(ConfigParser.SafeConfigParser):
    __metaclass__ = Singleton

    def __init__(self, file):
        ConfigParser.SafeConfigParser.__init__(self)
        self.file = file
        if not os.path.isfile(self.file):
            logging.warning("Creating config")
            #  Open a new file for reading and writing
            f = open(file, 'w+')
            f.close()

        self.read(file)
        if self.has_section('Connection Details'):
            connection_details = 'Config contains '
            for item in self.items('ConnectionDetails'):
                connection_details += "{} ".format(item)
            debug_logger.debug(connection_details)

        #  Add configuration sections if they do not exist
        if not self.has_section('ConnectionDetails'):
            self.add_section('ConnectionDetails')

        if not self.has_section('Settings'):
            self.add_section('Settings')

        if not self.has_option('ConnectionDetails', 'user'):
            self.set('ConnectionDetails', 'user', 'None')

        # Risky stuff, best to remove in production
        if not self.has_option('ConnectionDetails', 'password'):
            self.set('ConnectionDetails', 'password', 'None')

        if not self.has_option('ConnectionDetails', 'server'):
            self.set('ConnectionDetails', 'server', 'None')

        if not self.has_option('Settings', 'mic'):
            self.set('Settings', 'mic', 'None')

        if not self.has_option('Settings', 'speakers'):
            self.set('Settings', 'speakers', 'None')

        with open(self.file, 'w') as config_file:
            self.write(config_file)

    #  Add or update settings to config file
    def update_setting(self, section, option, value):
        self.read(self.file)
        #  Add a section if one dose not exist
        if not self.has_section(section):
            self.add_section(section)
        #  Add/update the desired setting
        self.set(section, option, value)
        #  Write the settings back to disk
        with open(self.file, "w") as config_file:
            self.write(config_file)


#  Initialize Config on import. Reference this config for usage
config = Config("conn.conf")