![alt text](https://github.com/b6938236/high-quality-chat/blob/master/img/orionlogo.png "Orion Logo")
# high-quality-chat
Capstone Project for Georgia Tech

Implements liblinphone to create a SIP endpoint that does some pretty specific things.

It is meant to combine the low bandwidth of a voice codec for collaboration on projects that require "studio quality" outputs.  The "studio quality" is 320kpbs MP3, though this could easily be altered with little issue.

It should work with all SIP servers, though it was built and tested with FreePBX/Asterisk.

### Features

* User status synchronization (recording, mic disabled, speakers disabled)
* Records locally the entirety of the session in voice quality
* Allows 'artists' to record locally parts or all of the session in studio quality
* Allows 'artists' to send these studio quality recordings at the end of the session
* Allows 'producers' to segment audio (studio and voice quality) into arbitrary chunks in real time
* Allows playback of these chunks in voice quality
* Allows for an arbitrary number of users, limited only by SIP server settings and accounts.

### Dependencies

[Python 2.7](https://www.python.org/downloads/)

Precompiled binaries coming later.

linphone
* [Windows] `pip install linphone`
* [OS X] `pip install `
    * Download  [linphone.whl](https://www.linphone.org/snapshots/linphone-python/macosx/linphone-3.10.2_379_g85ffd1e-cp27-none-macosx_10_7_x86_64.whl)
    * `pip install linphone.whl`
    * We could not get a newer version to install on 10.10.

Kivy
* [Windows] https://kivy.org/docs/installation/installation-windows.html
* [OS X] https://kivy.org/docs/installation/installation-osx.html#using-homebrew-with-pip

PyDub and PyAudio
* Requires ffmpeg or libav (we are using ffmpeg)
* Windows
	* Install [ffmpeg](https://ffmpeg.zeranoe.com/builds/) and add it to path
	* `pip install pyaudio pydub`
* OSX
	* `brew install ffmpeg`
	* `brew install portaudio`
	* `pip install pyaudio`
  * `pip install pydub`
  
### Project Configuration

After cloning the application, any desired configurations should be filled out in `hqc/conn.conf`:
- [ConnectionDetails]
    - user: username for the voice chat server
    - password: password for the voice chat server
    - server: voice chat server IP address
    - call_no: voice conference call number
- [AudioSettings]
    - mic: preferred audio recording device
    - speakers: preferred playback device 
    - recording_location: This field should be a directory path where audio files from the recording sessions are saved.
- [ChatSettings]
    - ip_address: IP address of chat server
    - port: port address of chat server
    - username: desired username for the chat
    - role: role of user during session (set upon joining a session)
- [HQRecordingSettings]
    - width: TODO
    - channels: number of audio channels for high quality recording
    - rate: bit rate for high quality recording
- [LQRecordingSettings]
    - codec - desired audio compression

### Running the Application
Clone the Application
* Make sure [git](https://git-scm.com/) is properly installed and included in your path
* `git clone https://github.com/b6938236/high-quality-chat.git`
* Install dependencies from section above

Running the Chat Server
* Follow instructions up until the `server` section on the [chat README](https://github.com/b6938236/high-quality-chat/blob/master/hqc/chat/README.md)

Starting the Graphical Client
* Naviagte to project folder `cd high-quality-chat`
* And then run hqc/gui.py with `python gui.py`
