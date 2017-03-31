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
SYNC_SESSIONNAME = 13
SYNC_HAVEFILE = 14  # Artist should send this once it finalizes HQ recordings
SYNC_REQUESTFILE = 15  # Producer should send this once it hits the 'request file' button'

SYNC = range(4, 16)

# User roles
ARTIST = "ARTIST"
PRODUCER = "PRODUCER"
LISTENER = "LISTENER"

# Default connection values
IP = '127.0.0.1'
PORT = 9000
USERNAME = 'user'
