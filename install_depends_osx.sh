curl https://www.linphone.org/snapshots/linphone-python/macosx/linphone-3.10.2_379_g85ffd1e-cp27-none-macosx_10_7_x86_64.whl > linphone.whl
pip install linphone.whl
rm linphone.whl

brew install sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer
pip install -I Cython==0.23
USE_OSX_FRAMEWORKS=0 pip install kivy
pip install pygame

brew install ffmpeg portaudio
pip install pyaudio pydub