import os
os.environ['KIVY_GL_BACKEND'] = 'gl'
import re
import cv2
import time
import json
from kivy.app import App
from pyzbar import pyzbar
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.graphics.texture import Texture
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.properties import NumericProperty
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.screenmanager import ScreenManager, Screen


class JobClass:
    def __init__(self, info_dict, ink_key, employee='ABC123', wastage=0):
        # TODO remove employee placeholder
        self.info_dict = info_dict
        self.wastage = wastage
        self.employees = []
        self.employees.append(employee)
        self.qc = None
        self.ink_key = ink_key
        self.adjustments = {'size': 0, 'ink': 0, 'plate': 0}


class SelectPage(Screen):

    def scan_barcode(self):
        cam = cv2.VideoCapture(0)
        timeout = time.time() + 10

        # image_event = Clock.schedule_interval(self.show_image, 1.0 / 30)

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

        self.show_image(frame)
        cam.release()

    def show_image(self, frame):
        frame2 = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
        buf1 = cv2.flip(frame2, 0)
        buf = buf1.tostring()
        image_texture = Texture.create(
            size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
        image_texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        self.ids['camera_viewer'].texture = image_texture

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

            App.get_running_app().current_job = JobClass(job_dict, item_ink_key_dict)
            self.parent.get_screen('adjustment_page').generate_tabs()
            self.parent.get_screen('run_page').generate_screen()
            self.parent.transition.direction = 'left'
            self.parent.current = 'adjustment_page'

        except FileNotFoundError:
            popup_boxlayout = BoxLayout(orientation='vertical')
            popup_boxlayout.add_widget(Label(text='JO number ("{}") was not found, please try again.'.
                                             format(job_num)))
            dismiss_button = Button(text='Dismiss', size_hint=(1, None))
            popup_boxlayout.add_widget(dismiss_button)
            popup = Popup(title='No job found', content=popup_boxlayout, auto_dismiss=False, size_hint=(0.5, 0.5))
            dismiss_button.bind(on_press=popup.dismiss)
            popup.open()


class AdjustmentPage(Screen):
    adjustment_tabbedpanel = None

    def generate_tabs(self):
        if self.adjustment_tabbedpanel is not None:
            self.ids['box_layout'].clear_widgets(self.adjustment_tabbedpanel)

        self.adjustment_tabbedpanel = AdjustmentTabbedPanel()
        self.ids['box_layout'].add_widget(self.adjustment_tabbedpanel)


class AdjustmentTabbedPanel(TabbedPanel):
    pass


class AdjustmentTab(BoxLayout):
    size_togglebox = None
    ink_text = None
    plate_text = None

    def __init__(self, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        Clock.schedule_once(self.setup_adjustment_grid, 0)

    def setup_adjustment_grid(self, _dt):
        current_job = App.get_running_app().current_job

        # Size
        self.ids['adjustment_grid'].add_widget(AdjustmentLabel(text='Size: '))
        self.size_togglebox = YesNoToggleBox('size', self.set_size_change)
        self.ids['adjustment_grid'].add_widget(self.size_togglebox)
        self.size_togglebox.set_selection(current_job.adjustments['size'])

        # Ink
        self.ids['adjustment_grid'].add_widget(AdjustmentLabel(text='Ink: '))
        self.ink_text = AdjustmentTextInput()
        self.ink_text.bind(focus=self.set_text_input_target)
        self.ids['adjustment_grid'].add_widget(self.ink_text)
        self.ink_text.text = '{}'.format(current_job.adjustments['ink'])

        # Plate
        self.ids['adjustment_grid'].add_widget(AdjustmentLabel(text='Plate: '))
        self.plate_text = AdjustmentTextInput()
        self.plate_text.bind(focus=self.set_text_input_target)
        self.ids['adjustment_grid'].add_widget(self.plate_text)
        self.plate_text.text = '{}'.format(current_job.adjustments['plate'])

    def set_text_input_target(self, text_input, focus):
        if focus:
            self.ids['numpad'].set_target(text_input)
        else:
            current_job = App.get_running_app().current_job
            if text_input == self.ink_text:
                current_job.adjustments['ink'] = int(text_input.text)
            elif text_input == self.plate_text:
                current_job.adjustments['plate'] = int(text_input.text)

            print(current_job.adjustments)

    def set_size_change(self):
        current_job = App.get_running_app().current_job

        if self.size_togglebox is not None:
            current_job.adjustments['size'] = self.size_togglebox.current_value


class RunPage(Screen):
    wastagePopup = None

    def generate_screen(self):
        self.clear_widgets()
        self.add_widget(Factory.RunPageLayout())


class RunPageLayout(BoxLayout):
    counter = NumericProperty(0)

    def __init__(self, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        current_job = App.get_running_app().current_job
        self.job_dict = current_job.info_dict

        self.ids['jo_no'].text = 'JO No.: {}'.format(self.job_dict['JO No.'])
        self.ids['to_do'].text = 'To do: {}'.format(self.job_dict['To do'])
        self.ids['code'].text = 'Code: {}'.format(self.job_dict['Code'])
        self.ids['desc'].text = 'Description: {}'.format(self.job_dict['Desc'])
        if current_job.qc is None:
            self.ids['qc'].text = 'QC check: Not complete'
        else:
            self.ids['qc'].text = 'QC check: {}'.format(current_job.qc)


class NumPadGrid(GridLayout):
    target = None

    def __init__(self, **kwargs):
        GridLayout.__init__(self, **kwargs)
        self.buttons = []
        for i in range(1, 10):
            button = NumPadButton(text='{}'.format(i))
            button.bind(on_press=self.button_pressed)
            self.add_widget(button)
            self.buttons.append(button)

        button = NumPadButton(text=u'\u2713', color=(0, 1, 0, 1))
        button.bind(on_press=self.button_pressed)
        self.add_widget(button)
        self.buttons.append(button)

        button = NumPadButton(text='0')
        button.bind(on_press=self.button_pressed)
        self.add_widget(button)
        self.buttons.append(button)

        button = NumPadButton(text=u'\u232b', color=(1, 0, 0, 1))
        button.bind(on_press=self.button_pressed)
        self.add_widget(button)
        self.buttons.append(button)

    def set_target(self, target):
        self.target = target

    def button_pressed(self, instance):
        if isinstance(self.target, TextInput):
            if instance.text == u'\u232b':
                self.target.do_backspace()
            elif instance.text == u'\u2713':
                self.target = None
            else:
                self.target.insert_text(instance.text)


class NumPadButton(Button):
    pass


class AdjustmentLabel(Label):
    pass


class AdjustmentTextInput(TextInput):
    pass


class ToggleBox(BoxLayout):
    current_value = None

    def __init__(self, group_name, button_names, on_change_method=None, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        self.group_name = group_name
        self.buttons = []
        self.parent_method = on_change_method

        self.create_buttons(button_names)

        self.set_selection(0)

    def create_buttons(self, button_names):
        for name in button_names:
            button = ToggleButton(group=self.group_name, allow_no_selection=False, text=name)
            button.bind(on_press=self.set_value)
            self.buttons.append(button)
            self.add_widget(button)

    def set_value(self, button):
        self.current_value = button.text
        if self.parent_method is not None:
            self.parent_method()

    def set_selection(self, index):
        self.buttons[index].state = 'down'
        other_buttons = (button for button in self.buttons if button is not self.buttons[index])
        for button in other_buttons:
            button.state = 'normal'

        self.set_value(self.buttons[index])


class YesNoToggleBox(ToggleBox):
    def __init__(self, group_name, on_change_method=None, **kwargs):
        ToggleBox.__init__(self, group_name, ['Yes', 'No'], on_change_method, **kwargs)

    def create_buttons(self, button_names):
        for name in button_names:
            button = ToggleButton(group=self.group_name, allow_no_selection=False, text=name)
            button.bind(on_press=self.set_value)
            self.buttons = [button] + self.buttons
            self.add_widget(button)

    def set_value(self, button):
        self.current_value = self.buttons.index(button)

        if self.parent_method is not None:
            self.parent_method()



class PrintingGUIApp(App):
    screen_manager = ScreenManager()
    current_job = None
    user = None

    def build(self):
        Window.bind(on_keyboard=self.on_keyboard)
        Factory.register('AdjustmentTabbedPanel', cls=AdjustmentTabbedPanel)
        Factory.register('RunPageLayout', cls=RunPageLayout)

        self.screen_manager.add_widget(SelectPage(name='select_page'))
        self.screen_manager.add_widget(AdjustmentPage(name='adjustment_page'))
        self.screen_manager.add_widget(RunPage(name='run_page'))
        return self.screen_manager

    def on_keyboard(self, _window, _key, _scan_code, code_point, _modifier):
        if code_point == 'Q':
            self.stop()


if __name__ == '__main__':
    printApp = PrintingGUIApp()
    printApp.run()
