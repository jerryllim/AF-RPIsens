import os
os.environ['KIVY_GL_BACKEND'] = 'gl'
import re
import cv2
import sys
import time
import json
import socket
import ipaddress
import printingMain
from kivy.app import App
from pyzbar import pyzbar
from kivy.metrics import dp
from kivy.clock import Clock
from collections import Counter
from kivy.factory import Factory
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.core.window import Window
from settings_json import settings_json
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.graphics.texture import Texture
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.settings import SettingOptions, SettingString
from kivy.properties import NumericProperty, StringProperty


class JobClass(Widget):
    output = NumericProperty(0)

    def __init__(self, info_dict, ink_key, employees, wastage=None):
        Widget.__init__(self)
        self.info_dict = info_dict
        # TODO get default unit
        if wastage is None:
            wastage = {'waste1': (0, 'kg'), 'waste2': (0, 'kg')}
        self.wastage = wastage
        self.employees = employees
        self.qc = []
        self.ink_key = ink_key
        self.adjustments = {'E01': 0, 'E02': 0, 'E03': 0}

    # def get_employee(self):
    #     return self.employees[1]

    def get_adjustments(self):
        return self.adjustments

    def get_current_job(self):
        return "{jo_no}{jo_line:03d}".format(**self.info_dict)

    def get_sfu(self):
        # TODO reformat the return information
        return self.info_dict

    def get_item_code(self):
        return self.info_dict.get('code', '')

    def get_ink_key(self):
        ink_key_copy = self.ink_key.copy()
        ink_key_copy.pop('update', False)
        item_ink_key = {self.get_item_code(): ink_key_copy}
        return item_ink_key

    def ink_key_updated(self):
        return self.ink_key.get('update', False)


class SelectPage(Screen):
    cam = None
    camera_event = None
    timeout = None

    def scan_barcode(self):
        self.cam = cv2.VideoCapture(0)
        self.camera_event = Clock.schedule_interval(self.check_camera, 1.0/60)
        # Timeout
        self.timeout = Clock.schedule_once(self.stop_checking, 10)

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

        self.timeout.cancel()
        self.camera_event.cancel()
        self.cam.release()

    def show_image(self, frame):
        frame2 = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
        buf1 = cv2.flip(frame2, 0)
        buf = buf1.tostring()
        image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
        image_texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        self.ids['camera_viewer'].texture = image_texture

    def start_job(self):
        barcode = self.ids.job_entry.text
        # TODO clear job_entry text
        try:
            controller: printingMain.RaspberryPiController = App.get_running_app().controller

            job_dict = controller.get_job_info(barcode)
            if not job_dict:
                popup_boxlayout = BoxLayout(orientation='vertical')
                popup_boxlayout.add_widget(Label(text='JO number ("{}") was not found, please try again.'.
                                                 format(barcode)))
                dismiss_button = Button(text='Dismiss', size_hint=(1, None))
                popup_boxlayout.add_widget(dismiss_button)
                popup = Popup(title='No job found', content=popup_boxlayout, auto_dismiss=False, size_hint=(0.5, 0.5))
                dismiss_button.bind(on_press=popup.dismiss)
                popup.open()
                return

            item_code = job_dict.get('code')
            item_ink_key_dict = controller.get_ink_key(item_code)

            employees = App.get_running_app().action_bar.employees.copy()
            if len(employees) < len(App.get_running_app().action_bar.employee_buttons):
                raise ValueError('Please log in')

            App.get_running_app().current_job = JobClass(job_dict, item_ink_key_dict, employees)
            self.parent.get_screen('adjustment_page').generate_tabs()
            self.parent.get_screen('run_page').generate_screen()
            self.parent.transition.direction = 'left'
            self.parent.current = 'adjustment_page'
        except ValueError:
            popup_boxlayout = BoxLayout(orientation='vertical')
            popup_boxlayout.add_widget(Label(text='Please log in'.
                                             format(barcode)))
            popup = Popup(title='No employee logged in', content=popup_boxlayout, size_hint=(0.5, 0.5))
            popup.open()


class AdjustmentPage(Screen):
    adjustment_tabbedpanel = None

    def generate_tabs(self):
        current_job = App.get_running_app().current_job
        self.ids['jo_no'].text = 'JO No.: {}'.format(current_job.info_dict['jo_no'])

        if self.adjustment_tabbedpanel is not None:
            self.ids['box_layout'].remove_widget(self.adjustment_tabbedpanel)

        self.adjustment_tabbedpanel = Factory.AdjustmentTabbedPanel()
        self.ids['box_layout'].add_widget(self.adjustment_tabbedpanel)

    def proceed_next(self):
        current_job = App.get_running_app().current_job

        current_job.adjustments['E01'] = self.adjustment_tabbedpanel.ids['adjustment_tab'].size_togglebox.current_value
        current_job.adjustments['E02'] = self.int_text_input(self.adjustment_tabbedpanel.ids['adjustment_tab'].ink_text.
                                                             text)
        current_job.adjustments['E03'] = self.int_text_input(self.adjustment_tabbedpanel.ids['adjustment_tab'].
                                                             plate_text.text)

        if current_job.ink_key_updated():
            App.get_running_app().controller.replace_ink_key_tables(current_job.get_ink_key())

        self.parent.transition.direction = 'left'
        self.parent.current = 'run_page'

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
        # Size
        self.ids['adjustment_grid'].add_widget(AdjustmentLabel(text='Size: '))
        self.size_togglebox = YesNoToggleBox(group_name='size')
        self.ids['adjustment_grid'].add_widget(self.size_togglebox)
        self.size_togglebox.set_selection(0)

        # Ink
        self.ids['adjustment_grid'].add_widget(AdjustmentLabel(text='Ink: '))
        self.ink_text = AdjustmentTextInput()
        self.ink_text.bind(focus=self.set_text_input_target)
        self.ink_text.bind(text=self.check_text)
        self.ink_text.hint_text = '0'
        self.ink_text.hint_text_color = (0, 0, 0, 1)
        self.ids['adjustment_grid'].add_widget(self.ink_text)
        self.ink_text.text = '{}'.format(0)

        # Plate
        self.ids['adjustment_grid'].add_widget(AdjustmentLabel(text='Plate: '))
        self.plate_text = AdjustmentTextInput()
        self.plate_text.bind(focus=self.set_text_input_target)
        self.plate_text.bind(text=self.check_text)
        self.plate_text.hint_text = '0'
        self.plate_text.hint_text_color = (0, 0, 0, 1)
        self.ids['adjustment_grid'].add_widget(self.plate_text)
        self.plate_text.text = '{}'.format(0)

    def set_text_input_target(self, text_input, focus):
        if focus:
            self.ids['numpad'].set_target(text_input)

    @staticmethod
    def check_text(text_input, value):
        if value.lstrip("0") == '':
            text_input.text = ''


class RunPage(Screen):
    runPage = None
    wastagePopup = None

    def generate_screen(self):
        self.clear_widgets()
        self.runPage = Factory.RunPageLayout()
        self.add_widget(self.runPage)
        App.get_running_app().current_job.bind(output=self.runPage.setter('counter'))

    def maintenance_scan(self):
        maintenance_popup = EmployeeScanPage()
        maintenance_popup.title_label.text = 'Technician No.: '
        maintenance_popup.parent_method = self.start_maintenance
        maintenance_popup.open()

    def wastage_popup(self, key, finish=False):
        self.wastagePopup = WastagePopUp(key, self.runPage.update_waste)
        if finish:
            button = Button(text='Confirm')
            button.bind(on_release=self.stop_job)
            self.wastagePopup.ids['button_box'].add_widget(button)

        self.wastagePopup.open()

    def stop_job(self, _instance):
        self.wastagePopup.save_dismiss()
        # TODO publish job
        App.get_running_app().publish_job()
        self.parent.transition.direction = 'right'
        self.parent.current = 'select_page'

    def start_maintenance(self, employee_num, _alternate):
        sm = App.get_running_app().screen_manager
        sm.get_screen('maintenance_page').setup_maintenance(employee_num)
        self.parent.transition.direction = 'up'
        sm.current = 'maintenance_page'
        # TODO update dictionary for Maintenance

    def qc_check(self):
        qc_popup = EmployeeScanPage(qc=self.update_qc)
        qc_popup.title_label.text = 'QC No.: '
        qc_popup.parent_method = self.update_qc
        qc_popup.open()

    def update_qc(self, employee_num, fail=False):
        c_time = time.strftime('%x %H:%M')
        grade = 'Fail' if fail else 'Pass'
        App.get_running_app().current_job.qc.append((employee_num, c_time, grade))
        # TODO update dictionary for QC
        self.runPage.qc_label.text = 'QC Check: {} at {}, {}'.format(employee_num, c_time, grade)


class RunPageLayout(BoxLayout):
    counter = NumericProperty(0)
    waste1 = NumericProperty(0)
    waste2 = NumericProperty(0)

    def __init__(self, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        current_job = App.get_running_app().current_job
        self.job_dict = current_job.info_dict
        self.ids['jo_no'].text = 'JO No.: {}'.format(self.job_dict['jo_no'])
        self.ids['to_do'].text = 'To do: {}'.format(self.job_dict['to_do'])
        self.ids['code'].text = 'Code: {}'.format(self.job_dict['code'])
        self.ids['desc'].text = 'Description: {}'.format(self.job_dict['desc'])
        if not current_job.qc:
            self.qc_label.text = 'QC check: Not complete'
        else:
            self.qc_label.text = 'QC check: {}'.format(current_job.qc[-1])

    def update_waste(self, var, val):
        exec('self.{0} = {1}'.format(var, val))


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
    def __init__(self, key, update_func, **kwargs):
        Popup.__init__(self, **kwargs)
        self.title = key.capitalize()
        self.update_func = update_func
        self.ids['numpad'].set_target(self.add_label)
        self.current_job = App.get_running_app().current_job
        self.key = key
        self.wastage = self.current_job.wastage[self.key]
        self.numpad.enter_button.text = u'\u2795'
        self.numpad.set_enter_function(self.add_wastage)
        if self.wastage[0] != 0:
            self.unit_spinner.text = self.wastage[1]
            self.unit_spinner.disabled = True
            self.current_label.text = '{}'.format(self.wastage[0])
        else:
            units = App.get_running_app().config.get('General', '{}_units'.format(self.key))
            units = units.split(',')
            self.unit_spinner.text = units[0]
            self.unit_spinner.values = units
            self.current_label.text = '0'

    def add_wastage(self):
        new_sum = int(self.current_label.text) + self.int_text_input(self.add_label.text)
        self.current_label.text = '{}'.format(new_sum)
        self.add_label.text = ''

    def save_dismiss(self):
        self.current_job.wastage[self.key] = (int(self.current_label.text), self.unit_spinner.text)
        self.update_func(self.key, self.current_job.wastage[self.key][0])
        self.dismiss()

    @staticmethod
    def int_text_input(value):
        return int(value) if value else 0


class EmployeeScanPage(Popup):
    cam = None
    camera_event = None
    parent_method = None
    timeout = None

    def __init__(self, **kwargs):
        self.qc = kwargs.pop('qc', False)
        self.login = kwargs.pop('login', False)
        Popup.__init__(self, **kwargs)
        if self.qc:
            self.confirm_button.text = 'Pass'
            self.alternate_button.text = 'Fail'
        elif self.login:
            self.alternate_button.text = 'Log out'
        else:
            self.button_box.remove_widget(self.alternate_button)

    def scan_barcode(self):
        self.cam = cv2.VideoCapture(0)
        self.camera_event = Clock.schedule_interval(self.check_camera, 1.0/60)
        # Timeout
        self.timeout = Clock.schedule_once(self.stop_checking, 10)

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

    def stop_checking(self, dt):
        if dt != 0:
            self.employee_num.text = ''

        self.timeout.cancel()
        self.camera_event.cancel()
        self.cam.release()

    def show_image(self, frame):
        frame2 = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
        buf1 = cv2.flip(frame2, 0)
        buf = buf1.tostring()
        image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
        image_texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        self.ids['camera_viewer'].texture = image_texture

    def confirm(self, alternate=False):
        if self.employee_num.text == '' and not (self.login and alternate):
            popup = Popup(title='No id found', content=Label(text='Please scan your employee number.'), size_hint=(0.5, 0.5))
            popup.open()
            return

        # TODO check that it is not empty
        if callable(self.parent_method):
            self.parent_method(self.employee_num.text, alternate)
        self.dismiss()


class InkKeyTab(ScrollView):
    def __init__(self, **kwargs):
        ScrollView.__init__(self, **kwargs)
        self.clear_widgets()
        ink_key_dict = App.get_running_app().current_job.ink_key
        self.add_widget(Factory.InkKeyBoxLayout(ink_key_dict))


class InkKeyBoxLayout(BoxLayout):
    def __init__(self, _ink_key_dict, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        self.ink_key_dict = App.get_running_app().current_job.ink_key.copy()
        if not self.ink_key_dict:
            self.clear_widgets()
            self.add_widget(Label(text='No ink key found.'))
            return
        self.impression_text.text = '{}'.format(self.ink_key_dict.pop('impression', ''))
        self.impression_text.bind(focus=self.edit_impression)
        keys = list(self.ink_key_dict.keys())

        for key in keys:
            layout = InkZoneLayout(key)
            self.add_widget(layout)

    def edit_impression(self, _instance, focus):
        def dismiss_popup(_button):
            if value_textinput.text:
                ink_key_dict = App.get_running_app().current_job.ink_key
                ink_key_dict['update'] = True
                ink_key_dict['impression'] = int(value_textinput.text)
                self.impression_text.text = '{}'.format(ink_key_dict['impression'])

            edit_popup.dismiss()

        if focus is True:
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
            edit_popup = Popup(title='Edit impression', content=content_boxlayout, auto_dismiss=False, size_hint=(0.5,
                                                                                                                  0.7))
            dismiss_button.bind(on_press=dismiss_popup)
            edit_popup.open()


class InkZoneLayout(BoxLayout):
    def __init__(self, plate, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        self.plate = plate
        self.buttons = []
        self.ids['plate_code'].text = 'Plate: {}'.format(plate)
        self.load_widgets()

    def load_widgets(self):
        self.buttons.clear()
        self.ids['ink_zones'].clear_widgets()
        ink_dict = App.get_running_app().current_job.ink_key.get(self.plate)

        zones = sorted(ink_dict.keys(), key=alphanum_key)
        for zone in zones:
            button = Button(text="{}\n[b][size=20sp]{}[/size][/b]".format(zone, ink_dict.get(zone, '')),
                            size_hint=(1, None), halign='center', markup=True)
            button.bind(on_press=self.edit_ink_key)
            self.buttons.append(button)
            self.ids['ink_zones'].add_widget(button)

    def edit_ink_key(self, instance):
        def dismiss_popup(_button):
            if value_textinput.text:
                App.get_running_app().current_job.ink_key['update'] = True
                App.get_running_app().current_job.ink_key[self.plate][key] = int(value_textinput.text)

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
        edit_popup = Popup(title='Edit ink key {}'.format(key), content=content_boxlayout, auto_dismiss=False,
                           size_hint=(0.5, 0.7))
        dismiss_button.bind(on_press=dismiss_popup)
        edit_popup.open()


class SimpleActionBar(BoxLayout):
    time = StringProperty()
    emp_popup = None
    employee_buttons = []
    employees = {}

    def __init__(self, **kwargs):
        num_operators = int(kwargs.pop('num_operators', 1))
        BoxLayout.__init__(self, **kwargs)
        Clock.schedule_interval(self.update_time, 1)

        for i in range(1, num_operators+1):
            button = EmployeeButton(i)
            self.employee_buttons.append(button)
            button.bind(on_release=self.log_in)
            self.add_widget(button, 3)

    def update_time(self, _dt):
        self.time = time.strftime('%x %H:%M')

    def log_in(self, button):
        self.emp_popup = EmployeeScanPage(login=True)
        index = button.number
        self.emp_popup.title_label.text = 'Employee {} No.: '.format(index)
        self.emp_popup.parent_method = lambda num, alternate: self.get_employee_num(button, num, alternate)
        self.emp_popup.open()

    def get_employee_num(self, button, employee_num, alternate):
        if alternate or employee_num == '':
            if self.employees.get(button.number) is not None:
                self.employees.pop(button.number)
            button.set_default_text()
        else:
            self.employees[button.number] = employee_num
            emp_name = App.get_running_app().controller.get_employee_name(employee_num)
            button.text = '{}'.format(emp_name)

    def get_employee(self):
        employee = None
        for num in sorted(self.employees.keys()):
            if self.employees.get(num, None):
                employee = self.employees.get(num, None)
                break

        return employee


class EmployeeButton(Button):

    def __init__(self, number, **kwargs):
        Button.__init__(self, **kwargs)
        self.number = number
        self.set_default_text()

    def set_default_text(self):
        self.text = 'Employee {}'.format(self.number)


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
            elif instance.text.isdigit():
                self.target.text = (self.target.text + instance.text).lstrip("0")
            elif self.enter_function is not None:
                self.enter_function()


class NumPadButton(Button):
    pass


class AdjustmentLabel(Label):
    pass


class AdjustmentTextInput(TextInput):
    pass


class SettingScrollableOptions(SettingOptions):

    def _create_popup(self, _instance):
        # create the popup
        content = BoxLayout(orientation='vertical', spacing='5dp', size_hint=(1, None))
        scroll_content = ScrollView()
        scroll_content.add_widget(content)
        popup_width = min(0.95 * Window.width, dp(500))
        self.popup = popup = Popup(
            content=scroll_content, title=self.title, size_hint=(None, 0.75),
            width=popup_width)
        content.height = len(self.options)/3 * dp(55) + dp(100)

        # add all the options
        content.add_widget(Widget(size_hint_y=None, height=1))
        grid_content = GridLayout(cols=3, spacing='5dp', size_hint=(1, None))
        grid_content.height = len(self.options)/3 * dp(55)
        content.add_widget(grid_content)
        uid = str(self.uid)
        for option in self.options:
            state = 'down' if option == self.value else 'normal'
            btn = ToggleButton(text=option, state=state, group=uid, size_hint_y=None, height=dp(50))
            btn.bind(on_release=self._set_option)
            grid_content.add_widget(btn)

        # finally, add a cancel button to return on the previous panel
        content.add_widget(Widget())
        btn = Button(text='Cancel', size_hint_y=None, height=dp(50))
        btn.bind(on_release=popup.dismiss)
        content.add_widget(btn)

        # and open the popup !
        popup.open()


class SettingIPString(SettingString):

    def _validate(self, instance):
        self._dismiss()

        try:
            address = ipaddress.ip_address(self.textinput.text)
            if isinstance(address, ipaddress.IPv4Address):
                self.value = self.textinput.text
        finally:
            return


class SettingUnitsString(SettingString):

    def _validate(self, instance):
        self._dismiss()

        if re.match("^([^,])([a-z,]*)([^,])$", self.textinput.text):
            self.value = self.textinput.text


class SettingSelfIP(SettingString):

    def _create_popup(self, _instance):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_add = s.getsockname()[0]
        s.close()

        self.value = ip_add


class YesNoToggleBox(BoxLayout):
    current_value = None

    def __init__(self, group_name, on_change_method=None, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        self.group_name = group_name
        self.buttons = []
        self.parent_method = on_change_method

        self.create_buttons(['Yes', 'No'])

        self.set_selection(0)

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

    def set_selection(self, index):
        self.buttons[index].state = 'down'
        other_buttons = (button for button in self.buttons if button is not self.buttons[index])
        for button in other_buttons:
            button.state = 'normal'

        self.set_value(self.buttons[index])


class PrintingGUIApp(App):
    screen_manager = ScreenManager()
    current_job = None
    user = None
    action_bar = None
    controller = None
    # database_manager = None

    def build(self):
        # self.check_camera()  # TODO uncomment

        self.config.set('Network', 'self_add', self.get_ip_add())
        self.controller = printingMain.RaspberryPiController(self)
        # self.controller = FakeClass()  # TODO set if testing

        self.use_kivy_settings = False
        num_operators = self.config.get('General', 'num_operators')

        Factory.register('AdjustmentTabbedPanel', cls=AdjustmentTabbedPanel)
        Factory.register('RunPageLayout', cls=RunPageLayout)
        Factory.register('MaintenancePageLayout', cls=MaintenancePageLayout)

        self.screen_manager.add_widget(SelectPage(name='select_page'))
        self.screen_manager.add_widget(AdjustmentPage(name='adjustment_page'))
        self.screen_manager.add_widget(RunPage(name='run_page'))
        self.screen_manager.add_widget(MaintenancePage(name='maintenance_page'))

        blayout = BoxLayout(orientation='vertical')
        self.action_bar = SimpleActionBar(num_operators=int(num_operators))
        blayout.add_widget(self.action_bar)
        blayout.add_widget(self.screen_manager)
        return blayout

    def build_config(self, config):
        config.setdefaults('General', {
            'num_operators': '1',
            'waste1_units': 'kg',
            'waste2_units': 'kg,pcs',
            'output_pin': 'Pin 21'})

        ip_add = self.get_ip_add()
        config.setdefaults('Network', {
            'self_add': ip_add,
            'ip_add': '152.228.1.124',
            'port': 56789})

    def build_settings(self, settings):
        settings.register_type('scroll_options', SettingScrollableOptions)
        settings.register_type('ip_string', SettingIPString)
        settings.register_type('unit_string', SettingUnitsString)
        settings.register_type('self_ip', SettingSelfIP)
        settings.add_json_panel('Raspberry JAM', self.config, data=settings_json)

    @staticmethod
    def get_ip_add():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_add = s.getsockname()[0]
        s.close()

        return ip_add

    @staticmethod
    def check_camera():
        cam = cv2.VideoCapture(0)

        if cam is None or not cam.isOpened():
            print('No camera found', file=sys.stderr)
            raise SystemExit

    def on_config_change(self, config, section, key, value):
        # TODO to change number of operators and self_add, server ip and port?
        pass

    def update_output(self):
        # TODO add checks for maintenance or ...
        if self.current_job is None:
            return
        self.current_job.output += 1

    def publish_job(self):
        i_key = self.controller.get_key(interval=1)
        adjustments = self.current_job.get_adjustments()

        with self.controller.counts_lock:
            if self.controller.counts.get(i_key) is None:
                self.controller.counts[i_key] = Counter()
            self.controller.counts[i_key].update(adjustments)

        sfu_data = self.current_job.get_sfu()
        req_msg = {'sfu': sfu_data}
        if self.current_job.ink_key_updated():
            req_msg['ink_key'] = self.current_job.get_ink_key()

        self.controller.request(req_msg)


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


class FakeClass:
    import threading
    counts_lock = threading.Lock()
    counts = {}
    database_manager = None

    def __init__(self):
        self.database_manager = printingMain.DatabaseManager()

    def get_key(self, interval=5):
        return interval

    def get_job_info(self, barcode):
        job_info = self.database_manager.get_job_info(barcode)
        # if job_info is None:
        #     reply_msg = self.request({"job_info": barcode})
        #     value = reply_msg.pop(barcode)
        #     job_info = {'jo_no': value[0], 'jo_line': value[1], 'code': value[2], 'desc': value[3], 'to_do': value[4],
        #                 'ran': value[5]}

        return job_info

    def get_ink_key(self, item):
        return self.database_manager.get_ink_key(item)

    def get_employee_name(self, emp_id):
        return self.database_manager.get_employee_name(emp_id)

    def replace_ink_key_tables(self, ink_key):
        self.database_manager.replace_ink_key_tables(ink_key)


if __name__ == '__main__':
    printApp = PrintingGUIApp()
    printApp.run()
