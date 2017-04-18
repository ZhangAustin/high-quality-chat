import ConfigParser
import base64
import os


# TODO: fix lossy encoding in "ConnectionDetails"
#  Inherits methods such as get() from SafeConfigParser
class Config(ConfigParser.SafeConfigParser):
    """Handles creation and updating of configuration settings."""

    #  CONFIG FILE SPECIFICATIONS
    connection = ['user', 'password', 'server', 'call_no']
    audio_settings = ['mic', 'speakers', 'recording_location']
    chat_settings = ['ip_address', 'port', 'username', 'role']
    hq_recording_settings = ['width', 'channels', 'rate']  # Use these values to replace hardcoded in audio
    # HQ_recording_settings have no corresponding GUI element, users will have to change manually
    lq_recording_settings = ['codec']  # Use this when we finally implement dropdown

    sections = {'ConnectionDetails': connection,
                'AudioSettings': audio_settings,
                'ChatSettings': chat_settings,
                'HQRecordingSettings': hq_recording_settings,
                'LQRecordingSettings': lq_recording_settings}

    def __init__(self, file):
        """
        Initializes config file at location given or with file already at location given.
        :param file: File path to either create new config file or of already existing config file to use.
        """
        ConfigParser.SafeConfigParser.__init__(self)
        self.file = file
        if not os.path.isfile(self.file):
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
        for section in self.sections:
            if not self.has_section(section):
                self.add_section(section)
            for option in self.sections[section]:
                if not self.has_option(section, option):
                    self.set(section, option, "None")

        self.create_recording_location()

    def create_recording_location(self):
        """
        If not present, create the folder specified in recording_location
        :return: 
        """
        if not os.path.exists(self.get('AudioSettings', 'recording_location')):
            os.makedirs(self.get('AudioSettings', 'recording_location'))

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

        if option == 'recording_location':
            self.create_recording_location()

    def get_file_name(self, session_name, file_name):
        """
        Given a session name and file name, provide a fully qualified path to where it should be saved
        :param session_name: name of the current session 'SESSION_DATETIME"
        :param file_name: name of the file '[HQ|LQ]_DATETIME'
        :return: A fully qualified path
        """
        path = self.get('AudioSettings', 'recording_location')
        if path != "None":
            return os.path.join(path, session_name, file_name)  # If it is set up, record here
        else:
            return os.path.join(os.getcwd(), 'tmp_recordings', session_name,
                                file_name)  # If it is not set up, record to cwd/tmp

    def parse_conn_string(self, conn_string):
        """
        Decode the connection string and return its elements
        :param conn_string: Base64 encoded connection string
        :return: List containing decoded username, password, and server
        """
        decoded = base64.b64decode(conn_string)
        mark1 = decoded.find(';')
        mark3 = decoded.rfind(';')
        mark2 = decoded.find(';', mark1 + 1, mark3 - 1)
        username = decoded[:mark1]
        password = decoded[mark1 + 1:mark2]
        server = decoded[mark2 + 1:mark3]
        call_no = decoded[mark3 + 1:]
        # Old: return [username, password, server, call_no]
        # TODO: This has been updated, please fix in other places
        return {'user': username, 'password': password, 'server': server, 'call_no': call_no}

    def make_conn_string(self, username, password, server, call_no):
        """
        Given a username, password, and server address, base64 encode them together
        :param username: username (or phone number) to register to the SIP server
        :param password: password associated with the username
        :param server: IP or hostname of the SIP server
        :return: a base 64 encoded string containing all parameters
        """
        conn_string = username + ';' + password + ";" + server + ';' + call_no
        return base64.b64encode(conn_string)

    def get_section(self, section):
        """
        Returns a connection object, no more unordered tuple nonsense
        :param section: Name of the section, as defined in self.sections
        :return: A dict of the names and values in section
        """
        if section not in self.sections:
            print "Bad section defined"
            return

        obj = {}
        for item in self.sections[section]:
            obj[item] = self.get(section, item)
        return obj


if __name__ == '__main__':
    config = Config('conn.conf')
    a = config.get_section('ConnectionDetails')
    print config.get_section('AudioSettings')
    print config.get_section('ChatSettings')
    b = config.make_conn_string(a['user'], a['password'], a['server'], a['call_no'])
    print b
    print config.parse_conn_string(b)
