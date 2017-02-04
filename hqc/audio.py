from pyaudio import PyAudio
from pydub import AudioSegment
from pydub.utils import make_chunks

import os
import pyaudio
import sys
import wave

#  This file contains audio functionality for the project.


#  Splits an audio file into a list of audio segments.
#  Supports .mp3 and .wav files
def split_audio_file(file_path, secs):
    #  Get absolute file path
    #  file_path = os.path.abspath(filename)
    #  Extract filename and extension
    filename, file_extension = os.path.splitext(file_path)
    if file_extension == ".mp3":
        audio_segment = AudioSegment.from_mp3(file_path)
    elif file_extension == ".wav":
        audio_segment = AudioSegment.from_wav(file_path)
    else:
        print("Unsupported audio file")
        sys.exit(-1)
    #  Make a list of audio chunks
    chunk_list = make_chunks(audio_segment, secs*1000)
    # name = filename.split(".")
    # for i, chunk in enumerate(chunk_list):
    #     chunk_name = "{}{}".format(name[0], i) + ".wav"
    #     chunk.export(chunk_name, format="wav")
    #  Return the list of audio segments
    return chunk_list


#  Saves a list of audio chunks to the specified path
def save_audio_chunks(chunk_list, base_name, file_extension, file_path):
    for i, chunk in enumerate(chunk_list):
        chunk_name = "{}_{}".format(base_name, i) + str(file_extension)
        #  TODO: check for unsupported file types
        save_path = str(file_path) + str(chunk_name)
        print(save_path)
        #  indexing removes "." at beginning of file extension
        chunk.export(save_path, format=file_extension[1:])


#  TODO: parametrize and test outputting different settings
#  Records audio for 5 seconds to disk
def record_audio(filename, secs):
    #  Sample sizing and format
    FORMAT = pyaudio.paInt16
    # Number of channels
    CHANNELS = 2
    #  Sampling rate. 44.1 KHz is what's used for CD's
    RATE = 44100
    #
    CHUNK = 1024
    RECORD_SECONDS = secs
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

#  segment_list = split_audio_file("hqc/test/test.mp3", 20)
#  save_audio_chunks(segment_list, "hello", ".mp3", (os.getcwd() + "/hqc/"))
