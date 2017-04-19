# This file is effectively a list of ENUMS

# Payload message types
CHAT = 1
FILE = 2
ROLE_VERIFICATION = 3
# START --- Contains no payload --- #
SYNC_TESTSYNCMSG = 4
SYNC_MIC_ON = 5
SYNC_MIC_OFF = 6
SYNC_SPEAKER_ON = 7
SYNC_SPEAKER_OFF = 8
SYNC_UNUSED1 = 9
SYNC_UNUSED2 = 10
# END --- Contains no payload --- #
# START --- Contains timestamp payload --- #
SYNC_START_RECORDING = 11
SYNC_STOP_RECORDING = 12
# END --- Contains timestamp payload --- #
# START --- Contains filename payload --- #
SYNC_REQUEST_FILE = 13
# Artist sends "SENDFILE" to notify producer of new recording
SYNC_SEND_FILE = 14
# END --- Contains file name payload --- #

# Contains username, filename, length
SYNC_FILE_AVAILABLE = 15

# IMPORTANT: Keep to date with sync messages that want to be used
SYNC = [SYNC_TESTSYNCMSG,
        SYNC_TESTSYNCMSG,
        SYNC_MIC_ON,
        SYNC_MIC_OFF,
        SYNC_SPEAKER_ON,
        SYNC_SPEAKER_OFF,
        SYNC_START_RECORDING,
        SYNC_STOP_RECORDING,
        SYNC_REQUEST_FILE,
        SYNC_SEND_FILE,
        SYNC_FILE_AVAILABLE]

# User roles
ARTIST = "ARTIST"
PRODUCER = "PRODUCER"
LISTENER = "LISTENER"

# Default connection values
IP = '127.0.0.1'
PORT = 9000
USERNAME = 'user'

# String formattings
DATETIME_SESSION = 'SESSION_%Y%m%d_%H%M%S'
DATETIME_LQ = 'LQ_%H%M%S.wav'
DATETIME_HQ = 'HQ_%H%M%S.wav'

# Server reverse lookup
SYNC_CODE_WORDS = {
        1: "CHAT",
        2: "FILE",
        3: "ROLE_VERIFICATION",
        4: "SYNC_TESTSYNCMSG",
        11: "SYNC_START_RECORDING",
        12: "SYNC_STOP_RECORDING",
        13: "SYNC_REQUEST_FILE",
        14: "SYNC_SEND_FILE",
        15: "SYNC_FILE_AVAILABLE"

}
