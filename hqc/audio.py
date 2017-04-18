import Queue
import os
import time
import wave
from datetime import datetime
from datetime import timedelta
from threading import Thread

import pyaudio
from pydub import AudioSegment
from pydub.playback import play

from Config import Config
from chat import constants


class Recorder:
    _recording = False
    _frames = Queue.Queue()
    _p = ''
    _stream = ''
    _output = ''
    _audio_writer = ''
    _audio_recorder = ''
    _exit = False
    _config = None

    def __init__(self, filename):
        """
        Creates the high quality recorder
        :param filename: Filename to record into
        """
        self._config = Config('conn.conf')
        audio_config = self._config.get_section('HQRecordingSettings')

        self._p = pyaudio.PyAudio()
        self._stream = self._p.open(format=self._p.get_format_from_width(int(audio_config['width'])),
                                    channels=int(audio_config['channels']),
                                    rate=int(audio_config['rate']),
                                    input=True,
                                    stream_callback=self._callback)

        self._output = wave.open(filename, 'wb')
        self._output.setnchannels(int(audio_config['channels']))
        self._output.setsampwidth(int(audio_config['width']))
        self._output.setframerate(int(audio_config['rate']))

        self._audio_writer = Thread(target=self._write_queue_to_file)
        self._audio_writer.daemon = True
        self._audio_writer.start()

    def start(self):
        """
        Start the recording process, which will include the disk writer
        :return: 
        """
        self._recording = True
        self._audio_recorder = Thread(target=self._async_record)
        self._audio_recorder.start()

    def stop(self):
        """
        Stop the recording process, which will flush buffers and spin down started threads
        :return: 
        """
        self._recording = False
        self._frames.join()
        self._exit = True

    def _async_record(self):
        """
        Starts recording from stream asynchronously
        """
        self._stream.start_stream()

        while self._stream.is_active():
            time.sleep(0.05)

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


def get_audio_from_filename(filename, length, lowquals):
    """
    Figures out what LQ 
    :param filename: The name of the file (direct from sync chat)
    :param length: The length of the file specified in filename (direct from sync chat)
    :param lowquals: An array of finalized low quality recordings
    :return: A file name and relative time index
    """
    time = datetime.strptime(filename, constants.DATETIME_HQ)  # Auto strips 'HQ_' and '.wav'
    for lowqual in lowquals:
        lq_time = datetime.strptime(lowqual, constants.DATETIME_LQ)
        if lq_time <= time:  # Check if the LQ recording started before the HQ recording
            # Check if the end of the LQ recording is after the end of the HQ recording
            time_end = time + timedelta(0, length)
            lq_length = get_length(lowqual)
            lq_time_end = lq_time + timedelta(0, lq_length)
            if lq_time_end > time_end:
                return lowqual
    print "Something went wrong, {} not found in LQ array".format(time)


def playback(filename, start, end=None, playback_time=None):
    """
    Plays back a wav file from the start point (in seconds) to the end point (in seconds)
    :param filename: filename to playback
    :param start: start time, in seconds.  No more than 3 places after decimal or loss of precision
    :param end: end time, in seconds.  Same as above
    :param playback_time: time to play back.  use instead of end
    """

    file_name, file_extension = os.path.splitext(filename)
    # This method will play back filetypes whose extension matches the coded
    # This includes wav and mp3 so we should be good
    audio = AudioSegment.from_file(filename, format=file_extension[1:])

    if end is None and playback_time is not None:
        # Play the track starting from start for playback_time seconds
        segment = audio[int(start):int(start + end)]
        play(segment)
    elif end is not None and playback_time is None:
        # Play the track starting from start and ending at end
        segment = audio[int(start):int(end)]
        play(segment)
    else:
        # Play the whole thing
        play(audio)


def get_length(filename):
    """
    Get the length of an audio file suitable for use in playback()
    :param filename: Location of audio file
    :return: length of file in seconds
    """
    file_name, file_extension = os.path.splitext(filename)
    audio = AudioSegment.from_file(filename, file_extension[1:])
    return float(len(audio)) / 1000


if __name__ == '__main__':
    recorder = Recorder('async.wav')
    print "Starting recording async.wav"
    recorder.start()
    print "Recording 3 seconds"
    time.sleep(3)
    print "Stopping recording async.wav"
    recorder.stop()

    print "Waiting 3 seconds"
    time.sleep(3)

    recorder2 = Recorder('async2.wav')
    print "Starting recording async2.wav"
    recorder2.start()
    print "Recording 5 seconds"
    time.sleep(5)
    print "Stopping recording async2.wav"
    recorder2.stop()