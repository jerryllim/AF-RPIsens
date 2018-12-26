import cv2
import time
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
        # TODO ammend condition
        if self.ids.job_entry.text == '.':
            popup_boxlayout = BoxLayout(orientation='vertical')
            popup_boxlayout.add_widget(Label(text='JO number ("{}") was not found, please try again.'.
                                             format(self.ids.job_entry.text)))
            dismiss_button = Button(text='Dismiss', size_hint=(1, None))
            popup_boxlayout.add_widget(dismiss_button)
            popup = Popup(title='No job found', content=popup_boxlayout, auto_dismiss=False)
            dismiss_button.bind(on_press=popup.dismiss)
            popup.open()

        else:
            temp_dict = {'JO No.': self.ids.job_entry.text}
            self.parent.get_screen('run_page').generate_screen(temp_dict)
            self.parent.current = 'run_page'


class CameraViewer(Image):
    def __init__(self, cam, **kwargs):
        Image.__init__(self, **kwargs)
        self.cam = cam

    def update(self):
        print("update called")
        ret, frame = self.cam.read()

        if ret:
            buf1 = cv2.flip(frame, 0)
            buf = buf1.tostring()
            image_texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            # display image from the texture
            self.texture = image_texture


class RunPage(Screen):
    def clear_screen(self):
        self.clear_widgets()

    def generate_screen(self, job_dict):
        self.clear_screen()
        self.add_widget(Factory.RunPageLayout(job_dict))


class RunPageLayout(ScrollView):
    def __init__(self, job_dict, **kwargs):
        ScrollView.__init__(self, **kwargs)
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
        pos = self.pos[1] + 75
        # self.parent.parent.parent.parent.scroll_y = pos/1160
        print(self.parent.parent.parent.parent.scroll_y)


class PrintingGUIApp(App):
    def build(self):
        Factory.register('RunPageLayout', cls=RunPageLayout)
        screen_manager = ScreenManager()
        screen_manager.add_widget(SelectPage(name='select_page'))
        screen_manager.add_widget(RunPage(name='run_page'))
        return screen_manager


if __name__ == '__main__':
    printingApp = PrintingGUIApp()
    printingApp.run()
