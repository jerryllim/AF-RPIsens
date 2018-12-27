import os
os.environ['KIVY_GL_BACKEND'] = 'gl'
import re
import cv2
import time
import json
from kivy.app import App
from pyzbar import pyzbar
from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemanddock')
Config.set('kivy', 'keyboard_layout', 'numeric_keypad.json')
from kivy.factory import Factory
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.graphics.texture import Texture
from kivy.uix.scrollview import ScrollView
from kivy.properties import NumericProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Color, Rectangle


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

            try:
                fileName = job_dict.get('Code', '').replace('/', '_')
                with open('{}.json'.format(fileName)) as inkfile:
                    item_ink_key_dict = json.load(inkfile)

            except FileNotFoundError:
                item_ink_key_dict = {}

            self.parent.get_screen('run_page').generate_screen(job_dict, item_ink_key_dict)
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

    def generate_screen(self, job_dict, item_ink_key_dict):
        self.clear_screen()
        self.add_widget(Factory.RunPageLayout(job_dict, item_ink_key_dict))

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
        # TODO save info to output for SFU
        # TODO save ink key info


class RunPageLayout(BoxLayout):
    counter_number = NumericProperty(0)

    def __init__(self, job_dict, item_ink_key_dict, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        self.ids['test_button'].state = 'down'

        self.job_dict = job_dict
        self.ids['jo_no'].text = 'JO No.: {}'.format(self.job_dict['JO No.'])
        self.ids['to_do'].text = 'To do: {}'.format(self.job_dict['To do'])
        self.ids['item_code'].text = 'Code: {}'.format(self.job_dict['Code'])
        description = 'Description: {}'.format(self.job_dict['Desc'])
        label_length = 40
        self.ids['item_desc'].text = description[0:label_length]
        self.ids['item_desc2'].text = description[label_length:]
        self.ids['ink_key_tab'].generate_ink_key(item_ink_key_dict)


class AdjustmentTab(ScrollView):
    pass


class InkKeyTab(ScrollView):
    def generate_ink_key(self, ink_key_dict):
        self.clear_widgets()
        self.add_widget(Factory.InkKeyBoxLayout(ink_key_dict))


class InkKeyBoxLayout(BoxLayout):
    def __init__(self, ink_key_dict, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        self.ink_key_dict = ink_key_dict
        self.ids['impression'].text = '{}'.format(self.ink_key_dict.get('impression', ''))
        keys = list(self.ink_key_dict.keys())
        try:
            keys.remove('impression')
        except ValueError:
            pass
        for key in keys:
            layout = InkZoneLayout(key, self.ink_key_dict.get(key, ''))
            self.add_widget(layout)


class InkZoneLayout(BoxLayout):
    def __init__(self, plate, ink_dict, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        self.ink_dict = ink_dict
        self.buttons = []
        self.ids['plate_code'].text = plate
        self.load_widgets()

    def load_widgets(self):
        self.buttons.clear()
        self.ids['ink_zones'].clear_widgets()

        zones = sorted(self.ink_dict.keys(), key=alphanum_key)
        for zone in zones:
            button = Button(text="{}\n[b][size=20sp]{}[/size][/b]".format(zone, self.ink_dict.get(zone, '')),
                            size_hint=(None, 1), halign='center', markup=True)
            button.bind(on_press=self.edit_ink_key)
            self.buttons.append(button)
            self.ids['ink_zones'].add_widget(button)

    def edit_ink_key(self, instance):
        def dismiss_popup(_button):
            if value_textinput.text:
                self.ink_dict[key] = int(value_textinput.text)
            else:
                self.ink_dict[key] = 0

            edit_popup.dismiss()
            self.load_widgets()

        text = instance.text
        key, value = text.split('\n', 2)
        content_boxlayout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        value_textinput = TextInput()
        content_boxlayout.add_widget(value_textinput)
        dismiss_button = Button(text='Dismiss')
        content_boxlayout.add_widget(dismiss_button)
        edit_popup = Popup(title='Edit ink key {}'.format(key), content=content_boxlayout, auto_dismiss=False, size_hint=(0.5, 0.5))
        dismiss_button.bind(on_press=dismiss_popup)
        edit_popup.open()


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
        Factory.register('InkKeyBoxLayout', cls=InkKeyBoxLayout)
        self.screen_manager.add_widget(SelectPage(name='select_page'))
        self.screen_manager.add_widget(RunPage(name='run_page'))
        return self.screen_manager

    def on_keyboard(self, _window, _key, _scan_code, code_point, _modifier):
        if code_point == 'Q':
            self.stop()


def try_int(s):
    try:
        return int(s)
    except ValueError:
        return s


def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [try_int(c) for c in re.split('([0-9]+)', s)]


if __name__ == '__main__':
    printingApp = PrintingGUIApp()
    printingApp.run()
