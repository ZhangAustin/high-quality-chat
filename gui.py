import kivy
kivy.require('1.0.7')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition


class HQC(App):
    def build(self):
        self.load_kv("HQC.kv")
        return RootScreen()
class MainScreen(Screen):
    pass
class RootScreen(ScreenManager):
    pass
class SessionScreen(Screen):
    pass
class SessionJoiningScreen(Screen):
    pass

if __name__ == '__main__':
    HQC().run()
