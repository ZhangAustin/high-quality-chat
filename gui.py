import kivy
from kivy.app import App
from kivy.uix.gridlayout import GridLayout

kivy.require('1.9.1')


class HQCApp(App):
    def build(self):
        return MainScreen()

    def callback(instance):
        print 'Button <%s> pressed' % instance.text


class MainScreen(GridLayout):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.cols = 3
        #
        # #Contains the "Exit" button and "I'm an artist"
        # pane0 = BoxLayout(orientation='vertical')
        # pane0.add_widget(Button(text="Quit", size=(200,100)))
        # pane0.add_widget(Button(text="I'm an artist", size=(300,300)))
        # self.add_widget(pane0)
        #
        # # Contains the "I'm a producer" button
        # pane1 = BoxLayout(orientation='vertical')
        # pane1.add_widget(Label(text=""))
        # pane1.add_widget(Button(text="I'm a producer", size=(300,300)))
        # self.add_widget(pane1)
        #
        # # Contains the settings button and I'm an interested party
        # pane2 = BoxLayout(orientation='vertical')
        # pane2.add_widget(Button(text="Settings", size=(200,100)))
        # pane2.add_widget(Button(text="I'm an interested party", size=(300,300)))
        # self.add_widget(pane2)

    def callback(instance, object):
        print 'Button <%s> pressed' % object.text


class SettingsScreen(GridLayout):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.cols = 3

        # Display these in a dropdown, kivy.uix.dropdown
        # There should be a callback later to set_output_device and set_input_device probably
        # output_devices = hqc.enum_output_devices()
        # input_devices = hqc.enum_input_devices()

    def callback(instance, object):
        print 'Button <%s> pressed' % object.text


class ConnectionScreen(GridLayout):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.cols = 3

    def callback(instance, object):
        print 'Button <%s> pressed' % object.text

if __name__ == '__main__':
    HQCApp().run()
