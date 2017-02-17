import Queue
import os
import sys
import time
import wave
from threading import Thread

import pyaudio
from pydub import AudioSegment
from pydub.utils import make_chunks


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
        #  indexing removes "." at beginning of file extension
        chunk.export(save_path, format=file_extension[1:])


#  TODO: parametrize and test outputting different settings
#  Records audio for 5 seconds to disk
def record_audio(filename, secs):
    file_base_name, file_extension = os.path.splitext(filename)

    #  Sample sizing and format
    FORMAT = pyaudio.paInt16
    # Number of channels
    CHANNELS = 2
    #  Sampling rate. 44.1 KHz is what's used for CD's
    RATE = 44100
    # Number of samples in each frame
    CHUNK = 1024
    RECORD_SECONDS = secs
    WAVE_OUTPUT_FILENAME = file_base_name + ".wav"

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
    wave_file = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wave_file.setnchannels(CHANNELS)
    wave_file.setsampwidth(audio.get_sample_size(FORMAT))
    wave_file.setframerate(RATE)
    wave_file.writeframes(b''.join(frames))
    #  Close file handle
    wave_file.close()
    print("converting wav to mp3")
    if file_extension == ".mp3":
        audio_file = AudioSegment.from_wav(WAVE_OUTPUT_FILENAME)
        file_handle = audio_file.export(filename, format="mp3")


def init_audio_output(filename, width, channels, rate):
    """
    Initializes the Pyaudio stream and destination file
    :param filename: name to write the audio stream to
    :param width: int for use in get_format_from_width (either 1=8 bit, 2=16 bit, 3=24 bit, or 4=32bit)
    :param channels: number of channels for recording
    :param rate: sample rate at which to record
    :return: the pyaudio object, the pyaudio stream, and the file object
    """
    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(width),
                    channels=channels,
                    rate=rate,
                    input=True,
                    stream_callback=callback)

    output = wave.open(filename, 'wb')
    output.setnchannels(channels)
    output.setsampwidth(width)
    output.setframerate(rate)

    return p, stream, output


def async_record(p, stream):
    """
    Starts recording from stream asynchronously
    :param p: a pyaudio object
    :param stream: a pyaudio stream object
    """
    stream.start_stream()

    while stream.is_active():
        time.sleep(0.1)

    stream.stop_stream()
    stream.close()

    p.terminate()


def callback(in_data, frame_count, time_info, status):
    """
    Callback function for continuous_record
    Checks global var recording
       If true, put frames into the queue - another thread will pop from the queue and write to disk
       If false, shut down the recorder (we don't want silence or sudden time shifts in one recording file)
    """
    global recording, frames
    if recording:
        frames.put(in_data)
        callback_flag = pyaudio.paContinue
    else:
        callback_flag = pyaudio.paComplete

    return in_data, callback_flag


def write_queue_to_file(filename):
    """
    Write data from a queue to a file object
    :param filename: initialized file object to write to
    """
    global frames
    while True:
        data = frames.get()
        filename.writeframes(b''.join(data))
        frames.task_done()


if __name__ == '__main__':
    frames = Queue.Queue()
    recording = True
    p, stream, output = init_audio_output('asyc.mp3', 2, 2, 48000)

    t = Thread(target=write_queue_to_file, args=(output,))
    t.daemon = True
    print "starting daemon"
    t.start()

    print "starting recording"
    Thread(target=async_record, args=(p, stream))
    print "waiting 5 seconds"
    time.sleep(5)  # Record for 5 seconds
    print "killing recording"
    recording = False  # Emulate 'stop recording' button
    print "waiting for queue to empty"
    frames.join()  # Block until everything has been written to file

    # record_audio("test.mp3", 5)
    # segment_list = split_audio_file("test.mp3", 2.5)
    # save_audio_chunks(segment_list, "hello", ".mp3", (os.getcwd() + "/"))
