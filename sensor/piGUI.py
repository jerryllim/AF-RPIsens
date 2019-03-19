import os
os.environ['KIVY_GL_BACKEND'] = 'gl'
import re
import cv2
import sys
import time
import socket
import ipaddress
import piMain
from enum import Enum
from kivy.app import App
from pyzbar import pyzbar
from kivy.metrics import dp
from kivy.clock import Clock
from datetime import datetime
from kivy.factory import Factory
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.dropdown import DropDown
from settings_json import settings_main, settings_machine1, settings_machine2, settings_machine3
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.graphics.texture import Texture
from kivy.graphics import Color, Rectangle
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, NoTransition
from kivy.uix.settings import SettingOptions, SettingString
from kivy.properties import NumericProperty, StringProperty, ListProperty


class State(Enum):
    SELECT = 'select_page'
    ADJUSTMENT = 'adjustment_page'
    RUN = 'run_page'


class Colour(Enum):
    GREEN = (46.0/255, 139.0/255, 87.0/255, 1)  # Sea Green
    BLUE = (65.0/255, 105.0/255, 180.0/255, 1)  # Steel Blue
    RED = (138.0/255, 34.0/255, 34.0/255, 1)  # Fire Brick
    PURPLE = (102.0/255, 51.0/255, 153.0/255, 1)  # Rebecca Purple
    ORANGE = (255.0/255, 140.0/255, 0/255, 1)  # Dark Orange


class JobClass(Widget):
    # TODO output in job class or machine class
    output = NumericProperty(0)

    def __init__(self, job_info, wastage=None):
        Widget.__init__(self)
        self.job_info = job_info
        if wastage is None:
            wastage = {'waste1': (0, 'kg'), 'waste2': (0, 'kg')}
        self.wastage = wastage
        self.adjustments = {'B1': 0, 'B2': 0, 'B3': 0, 'B4': 0, 'B5': 0}
        self.qc = None

    def get_jo_no(self):
        return "{jo_no}{jo_line:03d}".format(**self.job_info)

    def get_sfu(self):
        # TODO format sfu dict
        sfu_dict = self.job_info.copy()
        sfu_dict.update(self.wastage)
        sfu_dict['output'] = self.output
        return sfu_dict

    def all_info(self):
        save_info = self.job_info.copy()
        save_info.update(self.wastage)
        save_info['output'] = self.output
        save_info.update(self.adjustments)
        save_info['qc'] = self.qc
        return save_info

    def get_jono(self):
        return self.job_info['jo_no']

    def set_qc(self, emp_id, c_time, grade):
        self.qc = (emp_id, c_time, grade)


class MachineClass:
    permanent = 0

    def __init__(self, index, controller, config):
        self.index = index
        self.controller = controller
        self.config = {}
        self.update_config(config)
        self.state = State.SELECT
        self.current_job = None
        self.emp_main = {}
        self.emp_main_names = {}
        self.emp_asst = {}
        self.emp_asst_names = {}
        self.maintenance = (None, None)
        # TODO set permanent

    def update_config(self, config):
        self.config.update(dict(config.items('General{}'.format(self.index))))
        self.config.update(dict(config.items('Adjustments{}'.format(self.index))))

    def generate_sfu(self):
        # TODO set sfu format
        sfu = self.current_job.get_sfu()
        pass

    def get_emp(self):
        if not self.emp_main:
            return None

        return min(self.emp_main, key=self.emp_main.get)

    def remove_emp(self, emp_id):
        start = self.emp_main.pop(emp_id, None)
        if start is None:
            start = self.emp_asst.pop(emp_id, None)
            self.emp_asst_names.pop(emp_id, None)
        else:
            self.emp_main_names.pop(emp_id, None)
        end = datetime.now().strftime('%Y-%m-%d %H:%M')

        self.controller.add_employee(self.index, "{0}_{1}".format(emp_id, start.strftime('%Y-%m-%d %H:%M')), end=end)

    def add_emp(self, emp_id, asst=False):
        start = datetime.now()
        if not asst:
            if len(self.emp_main) < 3:
                self.emp_main[emp_id] = start
                self.emp_main_names[emp_id] = self.controller.get_emp_name(emp_id)
                self.controller.add_employee(self.index, "{0}_{1}".format(emp_id, start.strftime('%Y-%m-%d %H:%M')))
                return True
            else:
                return False

        self.emp_asst[emp_id] = start
        self.emp_asst_names[emp_id] = self.controller.get_employee_name(emp_id)
        self.controller.add_employee(self.index, "{0}_{1}".format(emp_id, start.strftime('%Y-%m-%d %H:%M')))
        return True

    def has_emp(self, emp_id):
        if (emp_id in self.emp_main) or (emp_id in self.emp_asst):
            return True

        return False

    def emp_available(self):
        if self.emp_main:
            return True
        return False

    def get_jo_no(self):
        if self.current_job:
            return self.current_job.get_jo_no()
        return ''

    def get_jono(self):
        if self.current_job:
            return self.current_job.get_jono()
        return ''

    def get_job_info(self):
        if self.current_job:
            return self.current_job.job_info
        return {}

    def set_state(self, state):
        self.state = state

    def get_page(self):
        if any(self.maintenance):
            return 'maintenance_page'
        else:
            return self.state.value

    def add_qc(self, emp_id, c_time, _pass):
        grade = 'Pass' if _pass else 'Fail'
        self.current_job.set_qc(emp_id, c_time, grade)
        self.controller.add_qc(self.index, "{0}_{1}_{2}_{3}".format(emp_id, self.current_job.get_jo_no(), c_time, int(_pass)))

    def get_qc(self):
        if self.current_job:
            return self.current_job.qc
        return None

    def publish_job(self):
        # TODO This is called at stop job
        print(self.current_job.get_sfu())

    def self_info(self):
        save_info = {'permanent': self.permanent, 'state': self.state.name, 'emp_main': self.emp_main,
                     'emp_asst':self.emp_asst,'maintenance': self.maintenance}
        if self.current_job:
            save_info['job'] = self.current_job.all_info
        return save_info

    def get_current_job(self):
        return self.current_job

    def update_output(self):
        self.permanent += 1
        if self.current_job:
            self.current_job.output += 1

    def start_maintenance(self, emp_id):
        start = datetime.now()
        self.maintenance = (emp_id, start)
        self.controller.add_maintenance(self.index, "{0}_{1}".format(emp_id, start.strftime('%Y-%m-%d %H:%M')))

    def get_maintenance(self):
        return self.maintenance

    def finished_maintenance(self, emp_id, start):
        self.maintenance = (None, None)
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        self.controller.add_maintenance(self.index, "{0}_{1}".format(emp_id, start.strftime('%Y-%m-%d %H:%M')), now)


class SelectPage(Screen):
    cam = None
    camera_event = None
    timeout = None
    machine = None
    colour = ListProperty([0, 0, 0, 1])

    def on_pre_enter(self, *args):
        if self.machine is not App.get_running_app().get_current_machine():
            self.machine = App.get_running_app().get_current_machine()

        self.machine.set_state(State.SELECT)
        self.colour = Colour[self.machine.config['bg_colour']].value

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
        try:
            if not barcode:
                raise ValueError('Please scan barcode')

            if not self.machine.emp_available():
                raise ValueError("Please log in.")

            controller = App.get_running_app().controller
            job_dict = controller.get_job_info(barcode)
            if not job_dict:
                raise ValueError("JO number ({}) was not found, please try again.")

            self.ids.job_entry.text = ''
            self.machine.current_job = JobClass(job_dict)
            self.parent.transition = SlideTransition()
            self.parent.transition.direction = 'left'
            self.parent.current = 'adjustment_page'

        except ValueError as err_msg:
            popup_boxlayout = BoxLayout(orientation='vertical')
            popup_boxlayout.add_widget(Label(text=str(err_msg)))
            popup = Popup(title='Error', content=popup_boxlayout, size_hint=(0.5, 0.5))
            popup.open()


class AdjustmentPage(Screen):
    machine = None
    fields = {}
    size_togglebox = None
    ink_text = None
    plate_text = None
    colour = ListProperty([0, 0, 0, 1])

    def on_pre_enter(self, *args):
        if self.machine is not App.get_running_app().get_current_machine():
            self.machine = App.get_running_app().get_current_machine()
            self.generate_tabs()

        self.machine.set_state(State.ADJUSTMENT)
        self.colour = Colour[self.machine.config['bg_colour']].value

    def generate_tabs(self):
        # TODO save all info on change
        self.ids['jo_no'].text = 'JO No.: {}'.format(self.machine.get_jono())
        self.ids['adjustment_grid'].clear_widgets()
        for idx in range(1, 6):
            if int(self.machine.config['b{}_enable'.format(idx)]):
                self.ids['adjustment_grid'].add_widget(AdjustmentLabel(text='{}'.format(self.machine.config['b{}_name'.format(idx)])))
                field = AdjustmentTextInput()
                field.bind(focus=self.set_text_input_target)
                field.bind(text=self.check_text)
                field.hint_text = '0'
                field.hint_text_color = (0, 0, 0, 1)
                field.text = '{}'.format(0)
                self.fields['B{}'.format(idx)] = field
                self.ids['adjustment_grid'].add_widget(field)

    def proceed_next(self):
        # TODO store B1 to B5
        self.parent.transition = SlideTransition()
        self.parent.transition.direction = 'left'
        self.parent.current = 'run_page'

    def set_text_input_target(self, text_input, focus):
        if focus:
            self.ids['numpad'].set_target(text_input)

    @staticmethod
    def check_text(text_input, value):
        if value.lstrip("0") == '':
            text_input.text = ''


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


class EmployeePage(Screen):
    machine = None
    employee_layout = None
    emp_popup = None
    colour = ListProperty([0, 0, 0, 1])

    def on_pre_enter(self, *args):
        if self.machine is not App.get_running_app().get_current_machine():
            self.machine = App.get_running_app().get_current_machine()

        self.load_emp_list()
        self.colour = Colour[self.machine.config['bg_colour']].value

    def load_emp_list(self):
        self.emp_main_view.data = list({'text': '{0} - {1}'.format(id_, name)} for id_, name in
                                       self.machine.emp_main_names.items())
        self.emp_asst_view.data = list({'text': '{0} - {1}'.format(id_, name)} for id_, name in
                                       self.machine.emp_asst_names.items())

    def log_in_out(self):
        self.emp_popup = EmployeeScanPage(caller=self, login=True, auto_dismiss=False)
        self.emp_popup.open()

    def emp_login(self, emp_id, alternate=False):
        if self.machine.add_emp(emp_id, asst=alternate):
            self.emp_popup.dismiss()
            self.load_emp_list()
        else:
            popup_boxlayout = BoxLayout(orientation='vertical')
            popup_boxlayout.add_widget(Label(text=str('Maximum 3 main operators!')))
            popup = Popup(title='Error', content=popup_boxlayout, size_hint=(0.5, 0.5))
            popup.open()

    def emp_logout(self, emp_id, _alternate=False):
        self.machine.remove_emp(emp_id)
        self.emp_popup.dismiss()
        self.load_emp_list()

    def has_emp(self, emp_id):
        return self.machine.has_emp(emp_id)

    def get_parent_method(self, has_emp):
        if has_emp:
            return self.emp_logout
        else:
            return self.emp_login


class EmployeeScanPage(Popup):
    cam = None
    camera_event = None
    parent_method = None
    timeout = None

    def __init__(self, **kwargs):
        qc = kwargs.pop('qc', False)
        self.caller = kwargs.pop('caller', None)
        self.login = kwargs.pop('login', False)
        Popup.__init__(self, **kwargs)
        if qc:
            self.confirm_button.text = 'Fail'
            self.alternate_button.text = 'Pass'
        elif self.login:
            self.button_box.remove_widget(self.confirm_button)
            self.button_box.remove_widget(self.alternate_button)
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
                if self.login:
                    self.login_buttons(barcode_data)

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
        if self.employee_num.text == '':
            popup = Popup(title='No id found', content=Label(text='Please scan your employee number.'), size_hint=(0.5, 0.5))
            popup.open()
            return

        if callable(self.parent_method):
            self.parent_method(self.employee_num.text, alternate)

    def login_buttons(self, emp_id):
        logged_in = self.caller.has_emp(emp_id)
        self.parent_method = self.caller.get_parent_method(logged_in)

        if logged_in:
            self.confirm_button.text = 'Log out'
            self.button_box.add_widget(self.confirm_button)
        else:
            self.confirm_button.text = 'Main'
            self.alternate_button.text = 'Assistant'
            self.button_box.add_widget(self.confirm_button)
            self.button_box.add_widget(self.alternate_button)


class MaintenancePage(Screen):
    maintenance_layout = None
    machine = None
    emp_id = None
    start = None
    colour = ListProperty([0, 0, 0, 1])

    def on_pre_enter(self, *args):
        if self.machine is not App.get_running_app().get_current_machine():
            self.machine = App.get_running_app().get_current_machine()

        self.emp_id, self.start = self.machine.get_maintenance()
        self.clear_widgets()
        self.maintenance_layout = Factory.MaintenancePageLayout(self.emp_id, self.start)
        self.add_widget(self.maintenance_layout)
        self.colour = Colour[self.machine.config['bg_colour']].value

    def complete(self):
        self.machine.finished_maintenance(self.emp_id, self.start)
        sm = App.get_running_app().screen_manager
        sm.transition = SlideTransition()
        sm.transition.direction = 'down'
        sm.current = self.machine.state.value


class MaintenancePageLayout(BoxLayout):
    def __init__(self, employee_num, start, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        self.technician_label.text = 'Technician no.: {}'.format(employee_num)
        self.date_label.text = 'Start date: {}'.format(start.strftime('%x'))
        self.time_label.text = 'Start time: {}'.format(start.strftime('%H:%M'))


class RunPage(Screen):
    machine = None
    run_layout = None
    wastagePopup = None
    emp_popup = None
    colour = ListProperty([0, 0, 0, 1])

    def on_pre_enter(self, *args):
        if self.machine is not App.get_running_app().get_current_machine():
            self.machine = App.get_running_app().get_current_machine()
            if self.run_layout is not None:
                self.remove_widget(self.run_layout)
            self.run_layout = Factory.RunPageLayout()
            self.add_widget(self.run_layout)

        self.run_layout.counter = self.machine.get_current_job().output
        self.machine.get_current_job().bind(output=self.run_layout.setter('counter'))
        self.machine.set_state(State.RUN)
        self.colour = Colour[self.machine.config['bg_colour']].value

    def wastage_popup(self, key, finish=False):
        self.wastagePopup = WastagePopUp(key, self.run_layout.update_waste)
        if finish:
            button = Button(text='Confirm')
            button.bind(on_release=self.stop_job)
            self.wastagePopup.ids['button_box'].add_widget(button)

        self.wastagePopup.open()

    def stop_job(self, _instance):
        self.wastagePopup.save_dismiss()
        self.machine.publish_job()
        self.parent.transition = SlideTransition()
        self.parent.transition.direction = 'right'
        self.parent.current = 'select_page'

    def qc_check(self):
        self.emp_popup = EmployeeScanPage(qc=True)
        self.emp_popup.parent_method = self.update_qc
        self.emp_popup.title_label.text = 'QC No: '
        self.emp_popup.open()

    def update_qc(self, emp_id, _pass=False):
        now = datetime.now()
        grade = 'Pass' if _pass else 'Fail'
        self.machine.add_qc(emp_id, now.strftime('%Y-%m-%d %H:%M'), _pass)
        self.run_layout.qc_label.text = 'QC Check: {} at {}, {}'.format(emp_id,
                                                                        now.strftime('%Y-%m-%d %H:%M'), grade)
        self.emp_popup.dismiss()


class RunPageLayout(BoxLayout):
    counter = NumericProperty(0)
    waste1 = NumericProperty(0)
    waste2 = NumericProperty(0)

    def __init__(self, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        self.machine = App.get_running_app().get_current_machine()
        self.job_info = self.machine.get_job_info()
        self.ids['jo_no'].text = 'JO No.: {}'.format(self.job_info['jo_no'])
        self.ids['to_do'].text = 'To do: {}'.format(self.job_info['to_do'])
        bal = self.job_info['to_do'] - self.job_info['ran']
        self.ids['bal'].text = 'Balance: {}'.format(bal)
        self.ids['code'].text = 'Code: {}'.format(self.job_info['code'])
        self.ids['desc'].text = 'Description: {}'.format(self.job_info['desc'])
        qc = self.machine.get_qc()
        if not qc:
            self.qc_label.text = 'QC check: Not complete'
        else:
            self.qc_label.text = 'QC check: {} at {}, {}'.format(qc[0], qc[1], qc[2])

    def update_waste(self, var, val):
        exec('self.{0} = {1}'.format(var, val))


class WastagePopUp(Popup):
    def __init__(self, key, update_func, **kwargs):
        Popup.__init__(self, **kwargs)
        self.title = key.capitalize()
        self.update_func = update_func
        self.ids['numpad'].set_target(self.add_label)
        self.current_job = App.get_running_app().get_current_machine().get_current_job()
        self.key = key
        self.wastage = self.current_job.wastage[self.key]
        self.numpad.enter_button.text = u'\u2795'
        self.numpad.set_enter_function(self.add_wastage)
        if self.wastage[0] != 0:
            self.unit_spinner.text = self.wastage[1]
            self.unit_spinner.disabled = True
            self.current_label.text = '{}'.format(self.wastage[0])
        else:
            units = App.get_running_app().config.get('General{}'.format(App.get_running_app().current_index),
                                                     '{}_units'.format(self.key))
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


class SimpleActionBar(BoxLayout):
    time = StringProperty()
    emp_popup = None

    def __init__(self, config, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        Clock.schedule_interval(self.update_time, 1)
        self.machine_dropdown = DropDown()
        self.machine_dropdown.bind(on_select=lambda instance, x: setattr(self.machine_button, 'text', x))
        self.set_machine_dropdown(config)

    def update_time(self, _dt):
        self.time = time.strftime('%x %H:%M')

    def set_machine_dropdown(self, config):
        self.machine_button.text = App.get_running_app().get_current_machine().config['machine_name']
        self.machine_dropdown.clear_widgets()
        blayout = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint=(None, None), width='150sp')
        for idx in range(1, 4):
            if int(config.get('Machine', 'machine{}_enable'.format(idx))):
                name = config.get('General{}'.format(idx), 'machine_name')
                colour = config.get('General{}'.format(idx), 'bg_colour')
                button = Button(text=name, size_hint_y=None, height=100, background_normal='',
                                background_color=Colour[colour].value)
                button.idx = idx
                button.bind(on_release=self.machine_selected)

                blayout.add_widget(button)
        blayout.height = len(blayout.children) * 110
        with blayout.canvas.before:
            Color(rgba=(0, 0, 0, 1))
            Rectangle(pos=blayout.pos, size=blayout.size)
        self.machine_dropdown.add_widget(blayout)

    def select_machine(self):
        self.machine_dropdown.open(self.machine_button)

    def machine_selected(self, button):
        self.machine_dropdown.select(button.text)
        if button.idx is not App.get_running_app().current_index:
            App.get_running_app().change_machine(button.idx)

    def select_employee(self):
        self.machine_button.disabled = not self.machine_button.disabled
        self.main_button.disabled = not self.main_button.disabled
        sm = App.get_running_app().screen_manager
        sm.transition = SlideTransition()
        if sm.current is not 'employee_page':
            sm.transition.direction = 'up'
            sm.current = 'employee_page'
        else:
            sm.transition.direction = 'down'
            sm.current = App.get_running_app().get_current_machine().get_page()

    def select_maintenance(self):
        self.emp_popup = EmployeeScanPage(caller=self, auto_dismiss=False)
        self.emp_popup.parent_method = self.start_maintenance
        self.emp_popup.open()

    def start_maintenance(self, emp_id, _alternate=False):
        machine = App.get_running_app().get_current_machine()
        machine.start_maintenance(emp_id)
        self.emp_popup.dismiss()
        sm = App.get_running_app().screen_manager
        if sm.current is not 'maintenance_page':
            sm.transition = SlideTransition()
            sm.transition.direction = 'up'
            sm.current = 'maintenance_page'


class DropDownLayout(BoxLayout):
    pass


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


class PiGUIApp(App):
    current_index = 1
    machines = {}
    screen_manager = ScreenManager()
    controller = None
    action_bar = None

    def build(self):
        # self.check_camera()
        self.config.set('Network', 'self_add', self.get_ip_add())
        self.controller = FakeClass(self)  # TODO set if testing
        # self.controller = piMain.PiController(self)

        for idx in range(1, 4):
            self.machines[idx] = MachineClass(idx, self.controller, self.config)

        self.use_kivy_settings = False

        Factory.register('RunPageLayout', cls=RunPageLayout)

        self.screen_manager.add_widget(SelectPage(name='select_page'))
        self.screen_manager.add_widget(AdjustmentPage(name='adjustment_page'))
        self.screen_manager.add_widget(RunPage(name='run_page'))
        self.screen_manager.add_widget(MaintenancePage(name='maintenance_page'))
        self.screen_manager.add_widget(EmployeePage(name='employee_page'))

        blayout = BoxLayout(orientation='vertical')
        self.action_bar = SimpleActionBar(self.config)
        blayout.add_widget(self.action_bar)
        blayout.add_widget(self.screen_manager)

        return blayout

    def build_config(self, config):
        config.setdefaults('Machine', {
            'machine1_enable': 1,
            'machine2_enable': 0,
            'machine3_enable': 0})

        ip_add = self.get_ip_add()
        config.setdefaults('Network', {
            'self_add': ip_add,
            'self_port': 8888,
            'server_add': '152.228.1.124',
            'server_port': 9999})
        config.setdefaults('General1', {
            'machine_name': 'Machine 1',
            'bg_colour': 'BLUE',
            'output_pin': 'A1',
            'waste1_units': 'kg',
            'waste2_units': 'kg'})
        config.setdefaults('Adjustments1', {
            'b1_enable': 0,
            'b1_name': 'B1',
            'b2_enable': 0,
            'b2_name': 'B2',
            'b3_enable': 0,
            'b3_name': 'B3',
            'b4_enable': 0,
            'b4_name': 'B4',
            'b5_enable': 0,
            'b5_name': 'B5'})
        config.setdefaults('General2', {
            'machine_name': 'Machine 2',
            'bg_colour': 'GREEN',
            'output_pin': 'A1',
            'waste1_units': 'kg',
            'waste2_units': 'kg'})
        config.setdefaults('Adjustments2', {
            'b1_enable': 0,
            'b1_name': 'B1',
            'b2_enable': 0,
            'b2_name': 'B2',
            'b3_enable': 0,
            'b3_name': 'B3',
            'b4_enable': 0,
            'b4_name': 'B4',
            'b5_enable': 0,
            'b5_name': 'B5'})
        config.setdefaults('General3', {
            'machine_name': 'Machine 3',
            'bg_colour': 'RED',
            'output_pin': 'A1',
            'waste1_units': 'kg',
            'waste2_units': 'kg'})
        config.setdefaults('Adjustments3', {
            'b1_enable': 0,
            'b1_name': 'B1',
            'b2_enable': 0,
            'b2_name': 'B2',
            'b3_enable': 0,
            'b3_name': 'B3',
            'b4_enable': 0,
            'b4_name': 'B4',
            'b5_enable': 0,
            'b5_name': 'B5'})

    def build_settings(self, settings):
        settings.register_type('scroll_options', SettingScrollableOptions)
        settings.register_type('ip_string', SettingIPString)
        settings.register_type('unit_string', SettingUnitsString)
        settings.register_type('self_ip', SettingSelfIP)
        settings.add_json_panel('Raspberry JAM', self.config, data=settings_main)
        settings.add_json_panel('Machine 1', self.config, data=settings_machine1)
        settings.add_json_panel('Machine 2', self.config, data=settings_machine2)
        settings.add_json_panel('Machine 3', self.config, data=settings_machine3)

    def get_current_machine(self):
        return self.machines[self.current_index]

    def change_machine(self, idx):
        self.current_index = idx
        self.screen_manager.transition = NoTransition()
        self.screen_manager.current = self.get_current_machine().get_page()
        self.screen_manager.current_screen.on_pre_enter()

    def update_output(self, idx):
        self.machines[idx].update_output()

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
        if section == 'Network':
            self.controller.update_ip_ports()
        elif section[:-1] == 'General' or section[:-1] == 'Adjustments':
            idx = int(section[-1:])
            self.machines[idx].update_config(config)
            self.action_bar.set_machine_dropdown(config)
        elif section == 'Machine':
            self.action_bar.set_machine_dropdown(config)


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

    def __init__(self, gui):
        self.database_manager = piMain.DatabaseManager()
        self.gui = gui

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

    def get_emp_name(self, emp_id):
        return self.database_manager.get_emp_name(emp_id)

    def request(self, req_msg):
        print(req_msg)

    def update_ip_ports(self):
        print(self.gui.config.get('Network', 'server_add'))
        print(self.gui.config.get('Network', 'server_port'))
        print(self.gui.config.get('Network', 'self_add'))
        print(self.gui.config.get('Network', 'self_port'))

    def add_maintenance(self, idx, emp_start, end=None):
        key = 'M{}'.format(idx)
        print(key, emp_start, end)

    def add_employee(self, idx, emp_start, end=None):
        key = 'E{}'.format(idx)
        print(key, emp_start, end)

    def add_qc(self, idx, string):
        key = 'Q{}'.format(idx)
        print(key, string)


if __name__ == '__main__':
    piApp = PiGUIApp()
    piApp.run()
