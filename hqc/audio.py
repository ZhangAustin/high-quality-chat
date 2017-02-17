import Queue
import os
import sys
import time
import wave
from threading import Thread

import pyaudio
from pydub import AudioSegment
from pydub.utils import make_chunks


class Recorder:
    _recording = False
    _frames = Queue.Queue()
    _p = ''
    _stream = ''
    _output = ''
    _audio_writer = ''
    _audio_recorder = ''
    _exit = False

    def __init__(self, filename, width=2, channels=2, rate=48000):
        self._p = pyaudio.PyAudio()
        self._stream = self._p.open(format=self._p.get_format_from_width(width),
                                    channels=channels,
                                    rate=rate,
                                    input=True,
                                    stream_callback=self._callback)

        self._output = wave.open(filename, 'wb')
        self._output.setnchannels(channels)
        self._output.setsampwidth(width)
        self._output.setframerate(rate)

        self._audio_writer = Thread(target=self._write_queue_to_file)
        self._audio_writer.daemon = True
        self._audio_writer.start()

    def start(self):
        self._recording = True
        self._audio_recorder = Thread(target=self._async_record)
        self._audio_recorder.start()

    def stop(self):
        self._recording = False
        self._frames.join()
        self._exit = True

    def _async_record(self):
        """
        Starts recording from stream asynchronously
        """
        self._stream.start_stream()

        while self._stream.is_active():
            time.sleep(0.1)

        self._stream.stop_stream()
        self._stream.close()

        self._p.terminate()

    def _callback(self, in_data, frame_count, time_info, status):
        """
        Callback function for continuous_record
        Checks global var recording
           If true, put frames into the queue - another thread will pop from the queue and write to disk
           If false, shut down the recorder (we don't want silence or sudden time shifts in one recording file)
        """
        if self._recording:
            self._frames.put(in_data)
            callback_flag = pyaudio.paContinue
        else:
            callback_flag = pyaudio.paComplete

        return in_data, callback_flag

    def _write_queue_to_file(self):
        """
        Write data from a queue to a file object
        """
        while not self._exit:
            data = self._frames.get()
            self._output.writeframes(b''.join(data))
            self._frames.task_done()


def split_audio_file(self, file_path, secs):
    print "USING DEPRECIATED FUNCTION audio.split_audio_file"
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
    print "USING DEPRECIATED FUNCTION audio.save_audio_chunks"
    for i, chunk in enumerate(chunk_list):
        chunk_name = "{}_{}".format(base_name, i) + str(file_extension)
        #  TODO: check for unsupported file types
        save_path = str(file_path) + str(chunk_name)
        #  indexing removes "." at beginning of file extension
        chunk.export(save_path, format=file_extension[1:])


#  TODO: parametrize and test outputting different settings
#  Records audio for 5 seconds to disk
def record_audio(filename, secs):
    print "USING DEPRECIATED FUNCTION audio.record_audio"
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

if __name__ == '__main__':
    recorder = Recorder('async.mp3')
    print "Starting recording async.mp3"
    recorder.start()
    print "Recording 3 seconds"
    time.sleep(3)
    print "Stopping recording async.mp3"
    recorder.stop()

    print "Waiting 3 seconds"
    time.sleep(3)

    recorder2 = Recorder('async2.mp3')
    print "Starting recording async2.mp3"
    recorder2.start()
    print "Recording 5 seconds"
    time.sleep(5)
    print "Stopping recording async2.mp3"
    recorder2.stop()

    # record_audio("test.mp3", 5)
    # segment_list = split_audio_file("test.mp3", 2.5)
    # save_audio_chunks(segment_list, "hello", ".mp3", (os.getcwd() + "/"))
