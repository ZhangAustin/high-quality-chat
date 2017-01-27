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

Python 2.7, precompiled binaries coming later.

liblinphone
* [Windows] pip install linphone
* [OS X] pip install [linphone-3.10.2_379_g85ffd1e-cp27-none-macosx_10_7_x86_64.whl](https://www.linphone.org/snapshots/linphone-python/macosx/linphone-3.10.2_379_g85ffd1e-cp27-none-macosx_10_7_x86_64.whl)

PyQt4
* [Windows] pip install [PyQt4-\*.whl](http://stackoverflow.com/questions/22640640/how-to-install-pyqt4-on-windows-using-pip#22651895)
* [OS X] ##TODO##

Kivy
* [Windows] https://kivy.org/docs/installation/installation-windows.html
* [OS X] ##TODO##

PyDub and PyAudio
* Requires ffmpeg or libav (We are using ffmpeg)
  * [Windows] Install [ffmpeg](https://ffmpeg.zeranoe.com/builds/) and add it to path
* [Windows] pip install pyaudio
* [Windows] pip install pydub
