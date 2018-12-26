import os
os.environ['KIVY_GL_BACKEND'] = 'gl'
import cv2
import time
import json
from kivy.app import App
from pyzbar import pyzbar
from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemanddock')
Config.set('kivy', 'keyboard_layout', 'numeric_keypad.json')
from kivy.factory import Factory
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.graphics.texture import Texture
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen


class SelectPage(Screen):

    def scan_barcode(self):
        cam = cv2.VideoCapture(0)
        timeout = time.time() + 10

        # image_event = Clock.schedule_interval(self.ids.camera_viewer.update, 1.0 / 30)

        while True:
            ret, frame = cam.read()

            if ret:
                barcodes = pyzbar.decode(frame)

                if barcodes:
                    barcode = barcodes[0]
                    barcode_data = barcode.data.decode("utf-8")
                    self.ids.job_entry.text = barcode_data
                    break

            if time.time() > timeout:
                self.ids.job_entry.text = ''
                break

        # image_event.cancel()
        if ret:
            frame2 = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
            buf1 = cv2.flip(frame2, 0)
            buf = buf1.tostring()
            image_texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
            image_texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
            self.ids['camera_viewer'].texture = image_texture

        cam.release()

    def start_job(self):
        job_num = self.ids.job_entry.text
        try:
            with open('{}.json'.format(job_num), 'r') as infile:
                job_dict = json.load(infile)

            self.parent.get_screen('run_page').generate_screen(job_dict)
            self.parent.transition.direction = 'left'
            self.parent.current = 'run_page'
        except FileNotFoundError:
            popup_boxlayout = BoxLayout(orientation='vertical')
            popup_boxlayout.add_widget(Label(text='JO number ("{}") was not found, please try again.'.
                                             format(job_num)))
            dismiss_button = Button(text='Dismiss', size_hint=(1, None))
            popup_boxlayout.add_widget(dismiss_button)
            popup = Popup(title='No job found', content=popup_boxlayout, auto_dismiss=False, size_hint=(0.5, 0.5))
            dismiss_button.bind(on_press=popup.dismiss)
            popup.open()


class RunPage(Screen):
    rejectPopup = None

    def clear_screen(self):
        self.clear_widgets()

    def generate_screen(self, job_dict):
        self.clear_screen()
        self.add_widget(Factory.RunPageLayout(job_dict))

    def reject_popup(self):
        popup_boxlayout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        reject_textinput = TextInput()
        popup_boxlayout.add_widget(reject_textinput)
        popup_boxlayout.add_widget(BoxLayout())
        dismiss_button = Button(text='Dismiss')
        popup_boxlayout.add_widget(dismiss_button)
        self.rejectPopup = Popup(title='Reject/Recycle', content=popup_boxlayout, auto_dismiss=False, size_hint=(0.5, 0.5))
        dismiss_button.bind(on_press=self.dismiss_reject_popup)
        self.rejectPopup.open()

    def dismiss_reject_popup(self, _button):
        self.rejectPopup.dismiss()
        self.parent.transition.direction = 'right'
        self.parent.current = 'select_page'


class RunPageLayout(BoxLayout):
    def __init__(self, job_dict, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        self.job_dict = job_dict
        self.ids.jo_no.text = self.job_dict['JO No.']


class AdjustmentTab(ScrollView):
    pass


class PageManager(ScreenManager):
    pass


class AdjustmentTextInput(TextInput):
    def __init__(self, **kwargs):
        TextInput.__init__(self, **kwargs)
        self.bind(focus=self.on_focus)

    def on_focus(self, _instance, _value):
        pos = self.pos[1] - 210
        self.parent.parent.parent.scroll_y = pos/300


class PrintingGUIApp(App):
    screen_manager = ScreenManager()

    def build(self):
        Window.bind(on_keyboard=self.on_keyboard)

        Factory.register('RunPageLayout', cls=RunPageLayout)
        self.screen_manager.add_widget(SelectPage(name='select_page'))
        self.screen_manager.add_widget(RunPage(name='run_page'))
        return self.screen_manager

    def on_keyboard(self, _window, _key, _scancode, codepoint, modifier):
        if codepoint == 'Q':
            self.stop()


if __name__ == '__main__':
    printingApp = PrintingGUIApp()
    printingApp.run()
