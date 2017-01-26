from pydub import AudioSegment
from pydub.utils import make_chunks
test_sound = AudioSegment.from_mp3("test.mp3")

chunk_list = make_chunks(test_sound, 10000)
for i, chunk in enumerate(chunk_list):
    chunk_name = "test{}".format(i) + ".mp3"
    print "chunk {}".format(i)
    chunk.export(chunk_name, format="mp3")