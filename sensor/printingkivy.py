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
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import NumericProperty, StringProperty


class JobClass:
    def __init__(self, info_dict, ink_key, employee='ABC123', wastage=(0, 'kg')):
        # TODO remove employee placeholder
        self.info_dict = info_dict
        self.wastage = wastage
        self.employees = []
        self.employees.append(employee)
        self.qc = None
        self.ink_key = ink_key
        self.adjustments = {'size': 0, 'ink': 0, 'plate': 0}


class SelectPage(Screen):
    cam = None
    camera_event = None

    def scan_barcode(self):
        self.cam = cv2.VideoCapture(0)
        self.camera_event = Clock.schedule_interval(self.check_camera, 1.0/60)
        # Timeout
        Clock.schedule_once(self.stop_checking, 10)

    def check_camera(self, _dt):
        ret, frame = self.cam.read()

        if ret:
            barcodes = pyzbar.decode(frame)

            if barcodes:
                barcode = barcodes[0]
                barcode_data = barcode.data.decode("utf-8")
                self.ids.job_entry.text = barcode_data
                self.stop_checking(0)

            self.show_image(frame)

    def stop_checking(self, dt):
        if dt != 0:
            self.ids.job_entry.text = ''

        self.camera_event.cancel()
        self.cam.release()

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
        current_job = App.get_running_app().current_job
        self.ids['jo_no'].text = 'JO No.: {}'.format(current_job.info_dict['JO No.'])

        if self.adjustment_tabbedpanel is not None:
            self.ids['box_layout'].remove_widget(self.adjustment_tabbedpanel)

        self.adjustment_tabbedpanel = Factory.AdjustmentTabbedPanel()
        self.ids['box_layout'].add_widget(self.adjustment_tabbedpanel)

    def proceed_next(self):
        current_job = App.get_running_app().current_job

        current_job.adjustments['size'] = self.adjustment_tabbedpanel.ids['adjustment_tab'].size_togglebox.current_value
        current_job.adjustments['ink'] = self.int_text_input(self.adjustment_tabbedpanel.ids['adjustment_tab'].ink_text.text)
        current_job.adjustments['plate'] = self.int_text_input(self.adjustment_tabbedpanel.ids['adjustment_tab'].plate_text.text)
        self.parent.transition.direction = 'left'
        self.parent.current = 'run_page'

        # TODO to remove
        print(current_job.adjustments)

    @staticmethod
    def int_text_input(value):
        return int(value) if value else 0


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
        self.size_togglebox = YesNoToggleBox(group_name='size')
        self.ids['adjustment_grid'].add_widget(self.size_togglebox)
        self.size_togglebox.set_selection(current_job.adjustments['size'])

        # Ink
        self.ids['adjustment_grid'].add_widget(AdjustmentLabel(text='Ink: '))
        self.ink_text = AdjustmentTextInput()
        self.ink_text.bind(focus=self.set_text_input_target)
        self.ink_text.bind(text=self.check_text)
        self.ink_text.hint_text = '0'
        self.ink_text.hint_text_color = (0, 0, 0, 1)
        self.ids['adjustment_grid'].add_widget(self.ink_text)
        self.ink_text.text = '{}'.format(current_job.adjustments['ink'])

        # Plate
        self.ids['adjustment_grid'].add_widget(AdjustmentLabel(text='Plate: '))
        self.plate_text = AdjustmentTextInput()
        self.plate_text.bind(focus=self.set_text_input_target)
        self.plate_text.bind(text=self.check_text)
        self.plate_text.hint_text = '0'
        self.plate_text.hint_text_color = (0, 0, 0, 1)
        self.ids['adjustment_grid'].add_widget(self.plate_text)
        self.plate_text.text = '{}'.format(current_job.adjustments['plate'])

    def set_text_input_target(self, text_input, focus):
        if focus:
            self.ids['numpad'].set_target(text_input)

    def check_text(self, text_input, value):
        if value.lstrip("0") == '':
            text_input.text = ''


class RunPage(Screen):
    runPage = None
    wastagePopup = None

    def generate_screen(self):
        self.clear_widgets()
        self.runPage = Factory.RunPageLayout()
        self.add_widget(self.runPage)

    def maintenance_scan(self):
        maintenance_popup = EmployeeScanPage()
        maintenance_popup.title_label.text = 'Technician No.: '
        maintenance_popup.parent_method = self.start_maintenance
        maintenance_popup.open()

    def wastage_popup(self, finish=False):
        self.wastagePopup = WastagePopUp()
        if finish:
            button = Button(text='Confirm')
            button.bind(on_release=self.stop_job)
            self.wastagePopup.ids['button_box'].add_widget(button)

        self.wastagePopup.open()

    def stop_job(self, _instance):
        self.wastagePopup.save_dismiss()
        # TODO add code to save job class
        self.parent.transition.direction = 'right'
        self.parent.current = 'select_page'

    def start_maintenance(self, employee_num):
        sm = App.get_running_app().screen_manager
        sm.get_screen('maintenance_page').setup_maintenance(employee_num)
        self.parent.transition.direction = 'up'
        sm.current = 'maintenance_page'

    def qc_check(self):
        qc_popup = EmployeeScanPage()
        qc_popup.title_label.text = 'QC No.: '
        qc_popup.parent_method = self.update_qc
        qc_popup.open()

    def update_qc(self, employee_num):
        self.runPage.qc_label.text = 'QC Check: {} at {}'.format(employee_num, time.strftime('%x %H:%M'))


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
            self.qc_label.text = 'QC check: Not complete'
        else:
            self.qc_label.text = 'QC check: {}'.format(current_job.qc)


class MaintenancePage(Screen):
    maintenance_layout = None

    def setup_maintenance(self, employee_num):
        self.clear_widgets()
        self.maintenance_layout = Factory.MaintenancePageLayout(employee_num)
        self.add_widget(self.maintenance_layout)

    def complete(self):
        screen_manager = App.get_running_app().screen_manager
        self.parent.transition.direction = 'down'
        screen_manager.current = screen_manager.previous()


class MaintenancePageLayout(BoxLayout):
    def __init__(self, employee_num, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        self.technician_label.text = 'Technician no.: {}'.format(employee_num)
        self.date_label.text = 'Start date: {}'.format(time.strftime('%x'))
        self.time_label.text = 'Start time: {}'.format(time.strftime('%H:%M'))


class WastagePopUp(Popup):
    def __init__(self, **kwargs):
        Popup.__init__(self, **kwargs)
        self.ids['numpad'].set_target(self.add_label)
        self.current_job = App.get_running_app().current_job

        self.numpad.enter_button.text = u'\u2795'
        self.numpad.set_enter_function(self.add_wastage)

        if self.current_job.wastage[0] != 0:
            self.unit_spinner.text = self.current_job.wastage[1]
            self.unit_spinner.disabled = True
            self.current_label.text = '{}'.format(self.current_job.wastage[0])
        else:
            self.unit_spinner.text = 'kg'
            self.unit_spinner.values = ('kg', 'pcs')
            self.current_label.text = '0'

    def add_wastage(self):
        new_sum = int(self.current_label.text) + self.int_text_input(self.add_label.text)
        self.current_label.text = '{}'.format(new_sum)
        self.add_label.text = ''

    def save_dismiss(self):
        self.current_job.wastage = (int(self.current_label.text), self.unit_spinner.text)
        self.dismiss()

    @staticmethod
    def int_text_input(value):
        return int(value) if value else 0


class EmployeeScanPage(Popup):
    cam = None
    camera_event = None
    parent_method = None

    def scan_barcode(self):
        self.cam = cv2.VideoCapture(0)
        self.camera_event = Clock.schedule_interval(self.check_camera, 1.0/60)
        # Timeout
        Clock.schedule_once(self.stop_checking, 10)

    def check_camera(self, _dt):
        ret, frame = self.cam.read()

        if ret:
            barcodes = pyzbar.decode(frame)

            if barcodes:
                barcode = barcodes[0]
                barcode_data = barcode.data.decode("utf-8")
                self.employee_num.text = barcode_data
                self.stop_checking(0)

            self.show_image(frame)

    def stop_checking(self, _dt):
        self.camera_event.cancel()
        self.cam.release()

    def show_image(self, frame):
        frame2 = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
        buf1 = cv2.flip(frame2, 0)
        buf = buf1.tostring()
        image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
        image_texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        self.ids['camera_viewer'].texture = image_texture

    def confirm(self):
        if self.parent_method is not None:
            self.parent_method(self.employee_num.text)
        self.dismiss()


class InkKeyTab(ScrollView):
    def __init__(self, **kwargs):
        ScrollView.__init__(self, **kwargs)
        self.clear_widgets()
        ink_key_dict = App.get_running_app().current_job.ink_key
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
                            size_hint=(1, None), halign='center', markup=True)
            button.bind(on_press=self.edit_ink_key)
            self.buttons.append(button)
            self.ids['ink_zones'].add_widget(button)

    def edit_ink_key(self, instance):
        def dismiss_popup(_button):
            if value_textinput.text:
                self.ink_dict[key] = int(value_textinput.text)

            edit_popup.dismiss()
            self.load_widgets()

        text = instance.text
        key, value = text.split('\n', 2)
        content_boxlayout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        value_textinput = TextInput()
        value_textinput.bind(focus=lambda inst, _focus: numpad.set_target(inst))
        content_boxlayout.add_widget(value_textinput)
        numpad = NumPadGrid()
        numpad.size_hint = (1, 4)
        numpad.set_target(value_textinput)
        content_boxlayout.add_widget(numpad)
        dismiss_button = Button(text='Dismiss')
        content_boxlayout.add_widget(dismiss_button)
        edit_popup = Popup(title='Edit ink key {}'.format(key), content=content_boxlayout, auto_dismiss=False, size_hint=(0.5, 0.7))
        dismiss_button.bind(on_press=dismiss_popup)
        edit_popup.open()


class SimpleActionBar(BoxLayout):
    time = StringProperty()
    emp_popup = None

    def __init__(self, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        Clock.schedule_interval(self.update_time, 1)

    def update_time(self, _dt):
        self.time = time.strftime('%x %H:%M')

    def log_in(self):
        self.emp_popup = EmployeeScanPage()
        self.emp_popup.title_label.text = 'Employee No.: '
        self.emp_popup.parent_method = self.get_employee_num
        self.emp_popup.open()

    def get_employee_num(self, employee_num):
        self.employee_button.text = 'Employee No.: {}'.format(employee_num)


class NumPadGrid(GridLayout):
    target = None
    enter_function = None

    def __init__(self, **kwargs):
        GridLayout.__init__(self, **kwargs)
        self.buttons = []
        for i in range(1, 10):
            button = NumPadButton(text='{}'.format(i))
            button.bind(on_press=self.button_pressed)
            self.add_widget(button)
            self.buttons.append(button)

        self.enter_button = NumPadButton(text=u'\u2713', color=(0, 1, 0, 1))
        self.enter_button.bind(on_press=self.button_pressed)
        self.add_widget(self.enter_button)

        button = NumPadButton(text='0')
        button.bind(on_press=self.button_pressed)
        self.add_widget(button)
        self.buttons.append(button)

        self.backspace_button = NumPadButton(text=u'\u232b', color=(1, 0, 0, 1))
        self.backspace_button.bind(on_press=self.button_pressed)
        self.add_widget(self.backspace_button)

    def set_target(self, target):
        self.target = target

    def set_enter_function(self, function):
        self.enter_function = function

    def button_pressed(self, instance):
        if isinstance(self.target, TextInput):
            if instance is self.backspace_button:
                self.target.do_backspace()
            elif instance is self.enter_button:
                self.target = None
            else:
                self.target.insert_text(instance.text)

        elif isinstance(self.target, Label):
            if instance is self.backspace_button:
                self.target.text = self.target.text[:-1]
            elif instance is not self.enter_button:
                self.target.text = (self.target.text + instance.text).lstrip("0")
            elif self.enter_function is not None:
                self.enter_function()


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
            button.bind(on_release=self.set_value)
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
            button.bind(on_release=self.set_value)
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
        Factory.register('MaintenancePageLayout', cls=MaintenancePageLayout)

        self.screen_manager.add_widget(SelectPage(name='select_page'))
        self.screen_manager.add_widget(AdjustmentPage(name='adjustment_page'))
        self.screen_manager.add_widget(RunPage(name='run_page'))
        self.screen_manager.add_widget(MaintenancePage(name='maintenance_page'))

        blayout = BoxLayout(orientation='vertical')
        blayout.add_widget(SimpleActionBar())
        blayout.add_widget(self.screen_manager)
        return blayout

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
    printApp = PrintingGUIApp()
    printApp.run()
