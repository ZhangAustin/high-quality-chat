import kivy
from kivy.app import App
from kivy.uix.label import Label

kivy.require('1.9.1')


class HQCApp(App):
    def build(self):
        return Label(text='High Quality Chat')


if __name__ == '__main__':
    HQCApp().run()
