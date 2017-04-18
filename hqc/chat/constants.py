# This file is effectively a list of ENUMS

# Payload message types
CHAT = 1
FILE = 2
ROLE_VERIFICATION = 3
# START --- Contains no payload --- #
SYNC_TESTSYNCMSG = 4
SYNC_MICON = 5
SYNC_MICOFF = 6
SYNC_SPEAKERON = 7
SYNC_SPEAKEROFF = 8
SYNC_RECORDINGON = 9
SYNC_RECORDINGOFF = 10
# END --- Contains no payload --- #
# START --- Contains timestamp payload --- #
SYNC_RECORDINGSTART = 11
SYNC_RECORDINGSTOP = 12
# END --- Contains timestamp payload --- #
# START --- Contains filename payload --- #
SYNC_REQUESTFILE = 13
# Artist sends "SENDFILE" to notify producer of new recording
SYNC_SENDFILE = 14
# END --- Contains file name payload --- #

# Contains username, filename, length
SYNC_FILE_AVAILABLE = 15

# IMPORTANT: Keep to date with sync messages that want to be used
SYNC = [SYNC_TESTSYNCMSG,
        SYNC_TESTSYNCMSG,
        SYNC_MICON,
        SYNC_MICOFF,
        SYNC_SPEAKERON,
        SYNC_SPEAKEROFF,
SYNC_RECORDINGON,
SYNC_RECORDINGOFF,
SYNC_RECORDINGSTART,
SYNC_RECORDINGSTOP,
SYNC_REQUESTFILE,
SYNC_SENDFILE,
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
