from pydub import AudioSegment
from pydub.utils import make_chunks
from pyaudio import PyAudio
import pyaudio
import wave

#  TODO: I know this file looks bad. I will clean it up and make a proper Python module.
#  This file should contain audio/recording related functionality.


#  TODO: add file location and support for other files(get file extension)
#  Splits an mp3 file into sections based on time
def split_audio(filename, secs):
    #  Need conditionals to handle other file types
    test_sound = AudioSegment.from_mp3(filename)
    chunk_list = make_chunks(test_sound, secs*1000)
    for i, chunk in enumerate(chunk_list):

        chunk_name = "{}{}".format(filename, i) + ".mp3"
        chunk.export(chunk_name, format="mp3")

#  TODO: parameterize and test outputting different settings
#  Records audio for 5 seconds to disk
def record_audio(filename):
    #  Sample sizing and format
    FORMAT = pyaudio.paInt16
    # Number of channels
    CHANNELS = 2
    #  Sampling rate. 44.1 KHz is what's used for CD's
    RATE = 44100
    #
    CHUNK = 1024
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = filename

    #  Create PyAudio object
    audio = pyaudio.PyAudio()

    # Open audio stream with given parameters
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    print "recording..."
    frames = []
    #  Add small audio chunks to a list
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    print "finished recording"

    #  Stop Recording
    stream.stop_stream()
    #  Close handle
    stream.close()
    #  Close PyAudio session
    audio.terminate()
    #  File handle for output file
    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    #  Close file handle
    waveFile.close()
