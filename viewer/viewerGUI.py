import os
import csv
import logging
import datetime
import statistics
import configparser
from sys import exit
import viewerDatabase
from PySide2 import QtCore, QtWidgets, QtGui
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler


class MachinesTab(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.configuration_parent = parent
        self.database_manager = self.parent().database_manager

        # Add Top box for insert
        self.insert_fields = {}
        self.hheaders = self.database_manager.get_machines_headers()
        insert_box = QtWidgets.QGridLayout()
        for col, head in enumerate(self.hheaders):
            label = QtWidgets.QLabel(head, self)
            edit = QtWidgets.QLineEdit(self)
            edit.setValidator(QtGui.QIntValidator())
            self.insert_fields[head] = edit
            insert_box.addWidget(label, 0, col)
            insert_box.setAlignment(label, QtCore.Qt.AlignCenter)
            insert_box.addWidget(edit, 1, col)
        self.insert_fields[self.hheaders[0]].setValidator(None)

        # Tree View & Models for Machines
        self.machine_model = QtGui.QStandardItemModel(0, 3, self)
        self.machine_table = QtWidgets.QTableView(self)
        self.machine_table.setModel(self.machine_model)
        self.machine_table.setAlternatingRowColors(True)
        self.machine_table.setSortingEnabled(True)
        self.machine_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.machine_table.doubleClicked.connect(self.set_value)

        self.populate_machines()

        # Add, Delete, Save button on right
        btn_box = QtWidgets.QVBoxLayout()
        add_btn = QtWidgets.QPushButton('Add', self)
        add_btn.clicked.connect(self.add_row)
        btn_box.addWidget(add_btn)
        del_btn = QtWidgets.QPushButton('Delete', self)
        del_btn.clicked.connect(self.delete_rows)
        btn_box.addWidget(del_btn)
        btn_box.addStretch()

        vbox_layout = QtWidgets.QVBoxLayout()
        vbox_layout.addLayout(insert_box)
        hbox_layout = QtWidgets.QHBoxLayout()
        hbox_layout.addWidget(self.machine_table)
        hbox_layout.addLayout(btn_box)
        vbox_layout.addLayout(hbox_layout)
        self.setLayout(vbox_layout)
        self.show()

    def populate_machines(self):
        self.machine_model.clear()
        # Set horizontal headers
        self.machine_model.setHorizontalHeaderLabels(self.hheaders)

        # Insert machines
        machines_list = self.database_manager.get_machines()

        for id_, row in enumerate(machines_list):
            idx = id_
            for col, value in enumerate(row):
                if value:
                    item = QtGui.QStandardItem()
                    item.setData(value, QtCore.Qt.EditRole)
                    if col == 0:
                        pass
                    self.machine_model.setItem(idx, col, item)

    def add_row(self):
        row = self.machine_model.rowCount()
        if self.insert_fields[self.hheaders[0]].text():
            for col, key in enumerate(self.hheaders):
                value = self.insert_fields[key].text()
                if value:
                    item = QtGui.QStandardItem()
                    item.setData(value, QtCore.Qt.EditRole)
                    self.machine_model.setItem(row, col, item)
                self.insert_fields[key].clear()

    def delete_rows(self):
        rows = set()
        for idx in self.machine_table.selectedIndexes():
            rows.add(idx.row())
        if not rows:
            return

        row = min(rows)
        count = len(rows)
        choice = QtWidgets.QMessageBox.question(self, 'Delete', 'Delete {} rows?'.format(count),
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            self.machine_model.removeRows(row, count)

    def save_table(self):
        machines_list = []

        for row in range(self.machine_model.rowCount()):
            machine_name = self.machine_model.item(row, 0).data(QtCore.Qt.EditRole)
            if not machine_name:
                continue
            items = [machine_name]
            for col in range(1, self.machine_model.columnCount()):
                item = self.machine_model.item(row, col)
                if item:
                    try:
                        text = int(item.data(QtCore.Qt.EditRole))
                    except ValueError:
                        text = None
                else:
                    text = None
                items.append(text)

            machines_list.append(items)

        self.database_manager.reinsert_machines(machines_list)
        self.populate_machines()

    def get_machines_model(self):
        return self.machine_model

    def set_value(self):
        idx = self.machine_table.selectedIndexes()[0]
        col = self.hheaders[idx.column()]
        if col == 'machine':
            return
        machine = self.machine_model.item(idx.row(), 0).data(QtCore.Qt.EditRole)
        item = self.machine_model.item(idx.row(), idx.column())
        if item:
            current = item.data(QtCore.Qt.EditRole)
        else:
            current = 0

        value, result = TargetInputDialog.get_value(self, machine, col, current)
        if result:
            item = self.machine_model.itemFromIndex(idx)
            item.setData(value, QtCore.Qt.EditRole)


class TargetInputDialog(QtWidgets.QDialog):
    def __init__(self, parent, title, label, value):
        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowTitle('Set target for {}'.format(title))
        self.label = QtWidgets.QLabel('{}: '.format(label), self)
        self.spin_box = QtWidgets.QSpinBox(self)
        self.spin_box.setMinimum(-50000)
        self.spin_box.setMaximum(50000)
        self.spin_box.setValue(value)
        self.layout = QtWidgets.QVBoxLayout()
        self.results = (value, False)

        # Buttons
        ok_btn = QtWidgets.QPushButton('OK', self)
        ok_btn.clicked.connect(self.ok_clicked)
        cancel_btn = QtWidgets.QPushButton('Cancel', self)
        cancel_btn.clicked.connect(self.cancel_clicked)
        remove_btn = QtWidgets.QPushButton('Remove', self)
        remove_btn.clicked.connect(self.remove_clicked)
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addWidget(remove_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.spin_box)
        self.layout.addLayout(btn_layout)
        self.setLayout(self.layout)

    def ok_clicked(self):
        self.results = (self.spin_box.value(), True)
        self.accept()

    def cancel_clicked(self):
        self.results = (self.spin_box.value(), False)
        self.reject()

    def remove_clicked(self):
        self.results = (None, True)
        self.accept()

    @staticmethod
    def get_value(parent, title, label, value):
        dialog = TargetInputDialog(parent, title, label, value)
        dialog.exec_()

        return dialog.results


class PisTab(QtWidgets.QWidget):
    sensor_list = ['machine', 'mac', 'A1', 'A2', 'A3', 'A4', 'A5', 'B1', 'B2', 'B3', 'B4', 'B5']

    def __init__(self, parent, machines_model):
        QtWidgets.QWidget.__init__(self, parent)
        self.database_manager = self.parent().database_manager
        self.pis_dict = self.database_manager.get_pis()

        # Tree View for the Pis
        self.pis_model = QtGui.QStandardItemModel(0, 3, self)
        self.pis_treeview = QtWidgets.QTreeView(self)
        self.pis_treeview.setModel(self.pis_model)
        self.pis_treeview.setAlternatingRowColors(True)
        self.pis_treeview.setRootIsDecorated(False)
        self.pis_treeview.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.pis_treeview.setSortingEnabled(True)
        self.populate_pis()
        header = self.pis_treeview.header()
        # header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeToContents)

        hbox_layout = QtWidgets.QHBoxLayout()
        hbox_layout.addWidget(self.pis_treeview)
        self.setLayout(hbox_layout)

        self.show()

    def populate_pis(self):
        self.pis_model.clear()
        self.pis_model.setHorizontalHeaderLabels(['Nickname', 'IP Address', 'Port', 'Machine1', 'Machine2', 'Machine3',
                                                  'lu to', 'lu from', 'lu jobs'])

        for ip in self.pis_dict.keys():
            nick_item = QtGui.QStandardItem(self.pis_dict[ip].get('nick'))
            ip_item = QtGui.QStandardItem(ip)
            port_item = QtGui.QStandardItem(self.pis_dict[ip].get('port'))
            machine1_item = QtGui.QStandardItem(self.pis_dict[ip].get('machine1'))
            machine2_item = QtGui.QStandardItem(self.pis_dict[ip].get('machine2'))
            machine3_item = QtGui.QStandardItem(self.pis_dict[ip].get('machine3'))
            last_updates = self.database_manager.get_last_updates(ip)
            index = self.pis_model.rowCount()
            self.pis_model.setItem(index, 0, nick_item)
            self.pis_model.setItem(index, 1, ip_item)
            self.pis_model.setItem(index, 2, port_item)
            self.pis_model.setItem(index, 3, machine1_item)
            self.pis_model.setItem(index, 4, machine2_item)
            self.pis_model.setItem(index, 5, machine3_item)

            if last_updates:
                for idx, ludt in enumerate(last_updates[:3]):
                    if ludt:
                        item = QtGui.QStandardItem(ludt.strftime("%d/%m/%y %H:%M"))
                    else:
                        item = QtGui.QStandardItem('-')

                    self.pis_model.setItem(index, (6 + idx), item)

    def machine_in_use(self, machine):
        for ip in self.pis_dict.keys():
            for i in range(1, 4):
                if self.pis_dict[ip].get('machine{}'.format(i)) == machine:
                    return ip

        return False

    def set_fields(self, index):
        row = index.row()

        self.set_all_enabled(False, False)

        ip = self.pis_model.item(row, 1).text()
        self.main_lineedits['ip'].setText(ip)
        self.main_lineedits['nick'].setText(self.pis_dict[ip]['nick'])
        self.main_lineedits['port'].setText(self.pis_dict[ip]['port'])

        for key in self.machine_tabs:
            self.machine_tabs[key].set_fields(key, self.pis_dict[ip])

    def new_item(self):
        self.clear_all(edits=True)
        self.main_lineedits['nick'].setFocus()
        self.set_all_enabled(True, True)

    def edit_item(self):
        if len(self.main_lineedits['ip'].text()) > 0 and not self.main_lineedits['nick'].isEnabled():
            self.set_all_enabled(True, False)

    def delete_item(self):
        index = self.pis_treeview.selectedIndexes()[0]
        row = index.row()
        nick = self.pis_model.item(row, 0).text()
        ip = self.pis_model.item(row, 1).text()

        choice = QtWidgets.QMessageBox.question(self, 'Delete', 'Delete {0} ({1})?'.format(nick, ip))
        if choice == QtWidgets.QMessageBox.Yes:
            self.pis_dict.pop(ip, None)
            self.populate_pis()

    def set_item(self):
        ip = self.main_lineedits['ip'].text()
        self.pis_dict[ip] = {}
        for key in ['nick', 'port']:
            self.pis_dict[ip][key] = self.main_lineedits[key].text()

        for idx in self.machine_tabs.keys():
            self.pis_dict[ip].update(self.machine_tabs[idx].get_values(idx))

        self.populate_pis()
        self.clear_all(True)
        self.set_all_enabled(False, False)

    def save_items(self):
        pis_row = []

        for ip, values in self.pis_dict.items():
            pi_row = [ip, int(values['port']), values['nick']]

            for i in range(1, 4):
                for key in self.sensor_list:
                    pi_row.append(values['{0}{1}'.format(key, i)])

            pis_row.append(pi_row)

        self.database_manager.saved_all_pis(pis_row)

    def set_all_enabled(self, enable, ip):
        for key, edit in self.main_lineedits.items():
            if key == 'ip':
                edit.setEnabled(ip)
            else:
                edit.setEnabled(enable)

        for tab in self.machine_tabs.values():
            tab.enable_combos(enable)

    def clear_all(self, edits=False):
        if edits:
            for edit in self.main_lineedits.values():
                edit.clear()
                edit.setText('')

        for tab in self.machine_tabs.values():
            tab.clear_fields()


class EmployeesTab(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.database_manager = self.parent().database_manager

        # Tree View
        self.emp_model = QtGui.QStandardItemModel(0, 3, self)
        self.emp_treeview = QtWidgets.QTreeView(self)
        self.emp_treeview.setModel(self.emp_model)
        self.emp_treeview.setAlternatingRowColors(True)
        self.emp_treeview.setRootIsDecorated(False)
        self.emp_treeview.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.emp_treeview.setSortingEnabled(True)
        self.emp_treeview.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        header = self.emp_treeview.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        for i in range(3):
            self.emp_treeview.resizeColumnToContents(i)
        self.populate_employees()

        vbox_layout = QtWidgets.QVBoxLayout()
        vbox_layout.addWidget(self.emp_treeview)

        self.setLayout(vbox_layout)
        self.show()

    def populate_employees(self):
        self.emp_model.clear()
        self.emp_model.setHorizontalHeaderLabels(['ID', 'Name', 'last modified'])

        for row in self.database_manager.get_emps():
            id_item = QtGui.QStandardItem(row[0])
            name_item = QtGui.QStandardItem(row[1])
            date_item = QtGui.QStandardItem(str(row[2]))
            index = self.emp_model.rowCount()
            self.emp_model.setItem(index, 0, id_item)
            self.emp_model.setItem(index, 1, name_item)
            self.emp_model.setItem(index, 2, date_item)


class MiscTab(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.database_manager = self.parent().database_manager
        self.config = configparser.ConfigParser()
        path = os.path.expanduser('~/Documents/JAM/JAMviewer/jam.ini')
        self.config.read(path)

        # Database group
        self.db_edits = {}
        db_box = QtWidgets.QGroupBox('Database', self)
        db_layout = QtWidgets.QGridLayout()
        db_layout.setColumnMinimumWidth(0, 100)
        db_box.setLayout(db_layout)
        host_label = QtWidgets.QLabel('TCP/IP Server: ', db_box)
        host_edit = QtWidgets.QLineEdit(db_box)
        self.db_edits['host'] = host_edit
        host_edit.setText(self.config.get('Database', 'host'))
        port_label = QtWidgets.QLabel('Port: ', db_box)
        port_edit = QtWidgets.QLineEdit(db_box)
        self.db_edits['port'] = port_edit
        port_edit.setText(self.config.get('Database', 'port'))
        port_edit.setMaximumWidth(100)
        db_layout.addWidget(host_label, 0, 0, QtCore.Qt.AlignRight)
        db_layout.addWidget(host_edit, 0, 1)
        db_layout.addWidget(port_label, 0, 2, QtCore.Qt.AlignRight)
        db_layout.addWidget(port_edit, 0, 3)
        user_label = QtWidgets.QLabel('User: ', db_box)
        user_edit = QtWidgets.QLineEdit(db_box)
        self.db_edits['user'] = user_edit
        user_edit.setText(self.config.get('Database', 'user'))
        db_layout.addWidget(user_label, 1, 0, QtCore.Qt.AlignRight)
        db_layout.addWidget(user_edit, 1 ,1)
        pass_label = QtWidgets.QLabel('Password: ', db_box)
        pass_edit = QtWidgets.QLineEdit(db_box)
        self.db_edits['password'] = pass_edit
        pass_edit.setText(self.config.get('Database', 'password'))
        db_layout.addWidget(pass_label, 2, 0, QtCore.Qt.AlignRight)
        db_layout.addWidget(pass_edit, 2, 1)
        db_label = QtWidgets.QLabel('Database: ', db_box)
        db_edit = QtWidgets.QLineEdit(db_box)
        self.db_edits['db'] = db_edit
        db_edit.setText(self.config.get('Database', 'db'))
        db_layout.addWidget(db_label, 3, 0, QtCore.Qt.AlignRight)
        db_layout.addWidget(db_edit, 3, 1)
        db_test_btn = QtWidgets.QPushButton('Test', db_box)
        db_test_btn.clicked.connect(self.test_db)
        db_layout.addWidget(db_test_btn, 3, 3)

        # Log group
        # TODO add log group - log level & file name

        vbox_layout = QtWidgets.QVBoxLayout()
        vbox_layout.addWidget(db_box)
        vbox_layout.addStretch()

        widget = QtWidgets.QWidget(self)
        widget.setLayout(vbox_layout)
        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidget(widget)
        scroll_area.setWidgetResizable(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(scroll_area)
        self.setLayout(layout)
        self.show()

    def set_delete_spin_min(self, value):
        self.data_fields['delete'].setMinimum(value)

    def shift_check_state(self, state, idx):
        state = bool(state)
        self.shift_starts[idx].setEnabled(state)
        self.shift_ends[idx].setEnabled(state)

    def test_db(self):
        success = self.database_manager.test_db_connection(self.db_edits['host'].text(), self.db_edits['port'].text(),
                                                           self.db_edits['user'].text(),
                                                           self.db_edits['password'].text(), self.db_edits['db'].text())
        msgbox = QtWidgets.QMessageBox()
        msgbox.setMinimumWidth(500)
        if success:
            msgbox.setText('Connection Successful')
        else:
            msgbox.setText('Connection Failed')
        msgbox.exec_()

    def import_from(self):
        path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select file to import', '', 'CSV(*.csv)')
        if path[0] != '':
            self.import_fields['import'].setText(path[0])

    def export_to(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, 'Set export location', '')
        if path != '':
            self.import_fields['export'].setText(path)

    def save_misc(self):
        for key in self.db_edits.keys():
            self.config.set('Database', key, self.db_edits[key].text())

        path = os.path.expanduser('~/Documents/JAM/JAMviewer/jam.ini')
        with open(path, 'w') as configfile:
            self.config.write(configfile)


class ConfigurationWidget(QtWidgets.QWidget):
    def __init__(self, parent, database_manager):
        QtWidgets.QWidget.__init__(self, parent)
        config = configparser.ConfigParser()
        path = os.path.expanduser('~/Documents/JAM/JAMviewer/jam.ini')
        config.read(path)
        self.database_manager = database_manager

        self.setWindowTitle('Configurations')
        self.setMinimumWidth(800)

        self.tab_widget = QtWidgets.QTabWidget()
        self.machines_tab = MachinesTab(self)
        machines = self.machines_tab.get_machines_model()
        self.pis_tab = PisTab(self, machines)
        self.emp_tab = EmployeesTab(self)
        self.misc_tab = MiscTab(self)
        self.tab_widget.addTab(self.machines_tab, 'Machines')
        self.tab_widget.addTab(self.pis_tab, 'Pis')
        self.tab_widget.addTab(self.emp_tab, 'Employees')
        self.tab_widget.addTab(self.misc_tab, 'Miscellaneous')

        btn_box = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton('Save', self)
        save_btn.setAutoDefault(False)
        save_btn.clicked.connect(self.save_all)
        cancel_btn = QtWidgets.QPushButton('Cancel', self)
        cancel_btn.setAutoDefault(False)
        cancel_btn.clicked.connect(self.cancel_changes)
        btn_box.addStretch()
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(save_btn)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tab_widget)
        layout.addLayout(btn_box)
        self.setLayout(layout)
        # self.show()

    def save_all(self):
        self.machines_tab.save_table()
        self.misc_tab.save_misc()
        self.parent().accept()
        self.parent().parent().settings.update()
        self.parent().parent().database_manager.update()

    def cancel_changes(self):
        self.parent().done(0)


class DisplayTable(QtWidgets.QWidget):
    scheduler_jobs = {}

    def __init__(self, parent, database_manager):
        QtWidgets.QWidget.__init__(self, parent)
        config = configparser.ConfigParser()
        path = os.path.expanduser('~/Documents/JAM/JAMviewer/jam.ini')
        config.read(path)
        self.database_manager = database_manager
        self.scheduler = BackgroundScheduler()
        jam_dur = config.getint('Network', 'interval')
        self.schedule_jam(interval=jam_dur)

        self.table_model = QtGui.QStandardItemModel(3, 10)

        self.table_view = QtWidgets.QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table_view.setAlternatingRowColors(True)
        v_header = self.table_view.verticalHeader()
        v_header.hide()

        hbox = QtWidgets.QHBoxLayout()
        date_label = QtWidgets.QLabel('Date: ')
        self.date_spin = QtWidgets.QDateEdit()
        self.date_spin.setDate(QtCore.QDate.currentDate())
        start_label = QtWidgets.QLabel('Start: ')
        self.start_spin = QtWidgets.QTimeEdit(QtCore.QTime(7, 0))
        self.start_spin.setDisplayFormat('HH:mm')
        hour_label = QtWidgets.QLabel('Hours: ')
        self.hour_spin = QtWidgets.QSpinBox()
        self.hour_spin.setMinimum(1)
        self.hour_spin.setMaximum(24)
        self.hour_spin.setValue(12)
        populate_btn = QtWidgets.QPushButton('Refresh')
        populate_btn.clicked.connect(self.populate_table)
        hbox.addWidget(date_label)
        hbox.addWidget(self.date_spin)
        hbox.addWidget(start_label)
        hbox.addWidget(self.start_spin)
        hbox.addWidget(hour_label)
        hbox.addWidget(self.hour_spin)
        hbox.addWidget(populate_btn)

        box_layout = QtWidgets.QVBoxLayout()
        box_layout.addLayout(hbox)
        box_layout.addWidget(self.table_view)
        self.setLayout(box_layout)
        self.show()
        self.populate_table()
        self.scheduler.start()

    def populate_table(self):
        self.table_model.clear()

        table_hheaders = ['Machine', 'Sum']
        date = self.date_spin.date().toPython()
        start_time = self.start_spin.time().toPython()
        start = datetime.datetime.combine(date, start_time)
        end = start + datetime.timedelta(hours=int(self.hour_spin.text()))
        if start.hour >= end.hour:
            for i in range(start.hour, 24):
                table_hheaders.append('{:02d}'.format(i))
            for i in range(end.hour):
                table_hheaders.append('{:02d}'.format(i))
        else:
            for i in range(start.hour, end.hour):
                table_hheaders.append('{:02d}'.format(i))
        self.table_model.setHorizontalHeaderLabels(table_hheaders)

        output_list = []
        table_vheaders = self.database_manager.get_machine_names()
        for row, machine in enumerate(table_vheaders):
            output_list.append([0] * len(table_hheaders))
            self.table_model.setItem(row, 0, QtGui.QStandardItem(machine))

        outputs = self.database_manager.get_hourly_output(start.isoformat(timespec='minutes'),
                                                          end.isoformat(timespec='minutes'))
        for row in outputs:
            col = table_hheaders.index('{:02d}'.format(row[2]))
            try:
                idx = table_vheaders.index(row[0])
            except ValueError:
                table_vheaders.append(row[0])
                idx = table_vheaders.index(row[0])
                self.table_model.setItem(idx, 0, QtGui.QStandardItem(row[0]))
                output_list.append([0] * len(table_hheaders))
            output_list[idx][col] = row[3]

        targets_dict = self.database_manager.get_machine_targets('output')

        for idx, row in enumerate(output_list):
            target = targets_dict.get(table_vheaders[idx], None)
            for col, value in enumerate(row):
                if col < 2:
                    continue
                item = QtGui.QStandardItem(str(value))
                if target and value <= target:
                    font = QtGui.QFont()
                    font.setBold(True)
                    item.setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                    item.setFont(font)
                self.table_model.setItem(idx, col, item)
            self.table_model.setItem(idx, 1, QtGui.QStandardItem(str(sum(row))))

    def schedule_jam(self, interval=5):
        cron_trigger = CronTrigger(second='30', minute='1-59/{}'.format(interval))
        job_id = 'REFRESH'
        if self.scheduler_jobs.get(job_id):
            self.scheduler_jobs[job_id].remove()
        self.scheduler_jobs[job_id] = self.scheduler.add_job(self.update_table, cron_trigger, id=job_id,
                                                             misfire_grace_time=30, max_instances=3)

    def update_table(self):
        now = datetime.datetime.now()
        self.date_spin.setDate(QtCore.QDate.currentDate())
        if now.hour > 19:
            self.start_spin.setTime(QtCore.QTime(19, 0))
        else:
            self.start_spin.setTime(QtCore.QTime(7, 0))
        self.hour_spin.setValue(12)

        # Repopulate table
        self.populate_table()


class SFUDisplayTable(QtWidgets.QWidget):
    scheduler_jobs = {}

    def __init__(self, parent, database_manager):
        QtWidgets.QWidget.__init__(self, parent)
        config = configparser.ConfigParser()
        path = os.path.expanduser('~/Documents/JAM/JAMviewer/jam.ini')
        config.read(path)
        self.database_manager = database_manager

        self.sfu_model = QtGui.QStandardItemModel(3, 10)

        self.sfu_treeview = QtWidgets.QTreeView(self)
        self.sfu_treeview.setModel(self.sfu_model)
        self.sfu_treeview.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.sfu_treeview.setAlternatingRowColors(True)
        self.sfu_treeview.setRootIsDecorated(False)
        self.sfu_treeview.setSortingEnabled(True)
        header = self.sfu_treeview.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        hbox = QtWidgets.QHBoxLayout()
        date_label = QtWidgets.QLabel('Date: ')
        self.date_spin = QtWidgets.QDateEdit()
        self.date_spin.setDate(QtCore.QDate.currentDate())
        start_label = QtWidgets.QLabel('Start time: ')
        self.start_spin = QtWidgets.QTimeEdit(QtCore.QTime(7, 0))
        self.start_spin.setDisplayFormat('HH:mm')
        hour_label = QtWidgets.QLabel('End time: ')
        self.end_spin = QtWidgets.QTimeEdit(QtCore.QTime(19, 0))
        self.end_spin.setDisplayFormat('HH:mm')
        refresh_btn = QtWidgets.QPushButton('Refresh')
        refresh_btn.clicked.connect(self.populate_table)
        hbox.addWidget(date_label)
        hbox.addWidget(self.date_spin)
        hbox.addWidget(start_label)
        hbox.addWidget(self.start_spin)
        hbox.addWidget(hour_label)
        hbox.addWidget(self.end_spin)
        hbox.addWidget(refresh_btn)

        box_layout = QtWidgets.QVBoxLayout()
        box_layout.addLayout(hbox)
        box_layout.addWidget(self.sfu_treeview)
        self.setLayout(box_layout)
        self.show()
        self.populate_table()

    def populate_table(self):
        self.sfu_model.clear()
        self.sfu_model.setHorizontalHeaderLabels(self.database_manager.get_sfu_headers())

        date = self.date_spin.date().toPython()
        start = self.start_spin.time().toPython()
        end = self.end_spin.time().toPython()

        sfus = self.database_manager.get_sfus(date=date, time_fr=start.strftime('%H:%M'),
                                              time_to=end.strftime('%H:%M'))

        for row in sfus:
            index = self.sfu_model.rowCount()
            for col, value in enumerate(row):
                item = QtGui.QStandardItem(str(value))
                self.sfu_model.setItem(index, col, item)


class MUDisplayTable(QtWidgets.QWidget):
    scheduler_jobs = {}

    def __init__(self, parent, database_manager):
        QtWidgets.QWidget.__init__(self, parent)
        config = configparser.ConfigParser()
        path = os.path.expanduser('~/Documents/JAM/JAMserver/jam.ini')
        config.read(path)
        self.database_manager = database_manager

        self.table_model = QtGui.QStandardItemModel(3, 10)

        self.table_view = QtWidgets.QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table_view.setAlternatingRowColors(True)
        v_header = self.table_view.verticalHeader()
        v_header.hide()

        hbox = QtWidgets.QHBoxLayout()
        start_label = QtWidgets.QLabel('Start: ')
        start_datetime = QtCore.QDateTime.currentDateTime()
        start_datetime.setTime(QtCore.QTime(7, 0))
        self.start_spin = QtWidgets.QDateTimeEdit(start_datetime)
        self.start_spin.setDisplayFormat('dd-MM-yy HH:mm')
        self.start_spin.dateChanged.connect(self.change_end_date)
        end_label = QtWidgets.QLabel('End: ')
        end_datetime = QtCore.QDateTime.currentDateTime()
        end_datetime.setTime(QtCore.QTime(19, 0))
        self.end_spin = QtWidgets.QDateTimeEdit(end_datetime)
        self.end_spin.setDisplayFormat('dd-MM-yy HH:mm')
        populate_btn = QtWidgets.QPushButton('Refresh')
        populate_btn.clicked.connect(self.populate_table)
        hbox.addWidget(start_label)
        hbox.addWidget(self.start_spin)
        hbox.addWidget(end_label)
        hbox.addWidget(self.end_spin)
        hbox.addWidget(populate_btn)

        box_layout = QtWidgets.QVBoxLayout()
        box_layout.addLayout(hbox)
        box_layout.addWidget(self.table_view)
        self.setLayout(box_layout)
        self.show()
        self.populate_table()

    def change_end_date(self, date):
        self.end_spin.setDate(date)

    def populate_table(self):
        self.table_model.clear()

        table_hheaders = ['Machine', 'Avg']
        start = self.start_spin.dateTime().toPython()
        end = self.end_spin.dateTime().toPython()
        time_list = [start.hour] + [(start.replace(minute=0) + datetime.timedelta(hours=i+1)).hour
                                    for i in range(int((end - start).total_seconds()/3600))]
        if end.hour != time_list[-1]:
            time_list = time_list + [end.hour]

        for i in time_list:
            table_hheaders.append("{:02d}".format(i))

        self.table_model.setHorizontalHeaderLabels(table_hheaders)

        minutes_list = []
        outputs_list = []
        table_vheaders = self.database_manager.get_machine_names()
        for row, machine in enumerate(table_vheaders):
            minutes_list.append([0] * len(table_hheaders))
            outputs_list.append([0] * len(table_hheaders))
            self.table_model.setItem(row, 0, QtGui.QStandardItem(machine))

        outputs = self.database_manager.find_mu_in_hour(start.isoformat(timespec='minutes'),
                                                        end.isoformat(timespec='minutes'))

        for row in outputs:
            col = table_hheaders.index('{}'.format(row[2]))
            idx = table_vheaders.index(row[0])
            minutes_list[idx][col] = row[3]
            outputs_list[idx][col] = row[1]

        # targets_dict = self.database_manager.get_machine_targets('output')

        for idx, row in enumerate(minutes_list):
            # target = targets_dict.get(table_vheaders[idx], None)
            for col, value in enumerate(row):
                if col < 2:
                    continue
                # item = QtGui.QStandardItem("{} ({})".format(value, outputs_list[idx][col]))
                item = QtGui.QStandardItem(str(value))
                # if target and value <= target:
                #     font = QtGui.QFont()
                #     font.setBold(True)
                #     item.setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                #     item.setFont(font)
                self.table_model.setItem(idx, col, item)
            self.table_model.setItem(idx, 1, QtGui.QStandardItem(str(round(statistics.mean(row), 1))))


class MUDetailsDisplayTable(QtWidgets.QWidget):
    scheduler_jobs = {}

    def __init__(self, parent, database_manager):
        QtWidgets.QWidget.__init__(self, parent)
        config = configparser.ConfigParser()
        path = os.path.expanduser('~/Documents/JAM/JAMserver/jam.ini')
        config.read(path)
        self.database_manager = database_manager

        self.table_model = QtGui.QStandardItemModel(3, 10)

        self.table_view = QtWidgets.QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table_view.setAlternatingRowColors(True)
        v_header = self.table_view.verticalHeader()
        v_header.hide()
        h_header = self.table_view.horizontalHeader()
        h_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        hbox = QtWidgets.QHBoxLayout()
        start_label = QtWidgets.QLabel('Start: ')
        start_datetime = QtCore.QDateTime.currentDateTime()
        start_datetime.setTime(QtCore.QTime(7, 0))
        self.start_spin = QtWidgets.QDateTimeEdit(start_datetime)
        self.start_spin.setDisplayFormat('dd-MM-yy HH:mm')
        self.start_spin.dateChanged.connect(self.change_end_date)
        end_label = QtWidgets.QLabel('End: ')
        end_datetime = QtCore.QDateTime.currentDateTime()
        end_datetime.setTime(QtCore.QTime(19, 0))
        self.end_spin = QtWidgets.QDateTimeEdit(end_datetime)
        self.end_spin.setDisplayFormat('dd-MM-yy HH:mm')
        populate_btn = QtWidgets.QPushButton('Refresh')
        populate_btn.clicked.connect(self.populate_table)
        hbox.addWidget(start_label)
        hbox.addWidget(self.start_spin)
        hbox.addWidget(end_label)
        hbox.addWidget(self.end_spin)
        hbox.addWidget(populate_btn)

        box_layout = QtWidgets.QVBoxLayout()
        box_layout.addLayout(hbox)
        box_layout.addWidget(self.table_view)
        self.setLayout(box_layout)
        self.show()
        self.populate_table()

    def change_end_date(self, date):
        self.end_spin.setDate(date)

    def populate_table(self):
        self.table_model.clear()

        table_hheaders = ['Machine', 'Start', 'End', 'Duration', 'Output']
        self.table_model.setHorizontalHeaderLabels(table_hheaders)
        start = self.start_spin.dateTime().toPython()
        end = self.end_spin.dateTime().toPython()
        run_dict = self.database_manager.get_mu(start.isoformat(timespec='minutes'),
                                                end.isoformat(timespec='minutes'))

        row = 0
        for key, values in run_dict.items():
            self.table_model.setItem(row, 0, QtGui.QStandardItem(key))
            for starttime, endtime, duration, output in values:
                self.table_model.setItem(row, 1, QtGui.QStandardItem(starttime.strftime("%Y-%m-%d %H:%M")))
                self.table_model.setItem(row, 2, QtGui.QStandardItem(endtime.strftime("%Y-%m-%d %H:%M")))
                self.table_model.setItem(row, 3, QtGui.QStandardItem(str(duration)))
                self.table_model.setItem(row, 4, QtGui.QStandardItem(str(output)))
                row += 1


class JamMainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setWindowIcon(QtGui.QIcon('jam_icon.png'))
        # Logger setup
        self.logger = logging.getLogger('jamVIEWER')
        self.logger.setLevel(logging.DEBUG)
        path = os.path.expanduser('~/Documents/JAM/JAMviewer/jamVIEWER.log')
        file_handler = logging.FileHandler(path)
        file_handler.setLevel(logging.DEBUG)
        log_format = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s: %(module)s - %(message)s')
        file_handler.setFormatter(log_format)
        self.logger.addHandler(file_handler)
        self.logger.info('\n\nStarted logging')

        config = configparser.ConfigParser()
        path = os.path.expanduser('~/Documents/JAM/JAMviewer/jam.ini')
        config.read(path)
        success = viewerDatabase.DatabaseManager.test_db_connection(host=config.get('Database', 'host'),
                                                                    port=config.get('Database', 'port'),
                                                                    user=config.get('Database', 'user'),
                                                                    password=config.get('Database', 'password'),
                                                                    db=config.get('Database', 'db'))
        if not success:
            result = self.setup_database()
            if result:
                config = configparser.ConfigParser()
                path = os.path.expanduser('~/Documents/JAM/JAMviewer/jam.ini')
                config.read(path)
            else:
                exit()

        db_dict = {}
        for key in ['host', 'port', 'user', 'password', 'db']:
            db_dict[key] = config.get('Database', key)

        self.settings = viewerDatabase.Settings()
        self.database_manager = viewerDatabase.DatabaseManager(self.settings, **db_dict)
        # self.database_manager = viewerDatabase.DatabaseManager(self.settings, host=config.get('Database', 'host'),
        #                                                        port=config.get('Database', 'port'),
        #                                                        user=config.get('Database', 'user'),
        #                                                        password=config.get('Database', 'password'),
        #                                                        db=config.get('Database', 'db'))

        self.tab_widget = QtWidgets.QTabWidget()
        self.display_table = DisplayTable(self, self.database_manager)
        self.sfu_table = SFUDisplayTable(self, self.database_manager)
        self.mu_table = MUDisplayTable(self, self.database_manager)
        self.mu_det_table = MUDetailsDisplayTable(self, self.database_manager)
        self.tab_widget.addTab(self.display_table, 'Output Table')
        self.tab_widget.addTab(self.sfu_table, 'SFU Table')
        self.tab_widget.addTab(self.mu_table, 'MU Table')
        self.tab_widget.addTab(self.mu_det_table, 'MU Details Table')
        self.setCentralWidget(self.tab_widget)

        config_action = QtWidgets.QAction('&Configuration', self)
        config_action.setShortcut(QtGui.QKeySequence('Ctrl+,'))
        config_action.setStatusTip('Configurations Window')
        config_action.triggered.connect(self.launch_configuration)
        quit_action = QtWidgets.QAction('&Quit', self)
        quit_action.setShortcut(QtGui.QKeySequence('Ctrl+q'))
        quit_action.setStatusTip('Quit')
        quit_action.triggered.connect(exit)

        self.statusBar()

        main_menu = self.menuBar()
        file_menu = main_menu.addMenu(' &File')
        file_menu.addAction(config_action)
        file_menu.addAction(quit_action)

        self.logger.info('Completed JamMainWindow __init__')
        self.show()

    def launch_configuration(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('Configurations')
        dialog.setWindowIcon(QtGui.QIcon('jam_icon.png'))
        configurations = ConfigurationWidget(self, self.database_manager)
        configurations.show()
        dialog_layout = QtWidgets.QVBoxLayout()
        dialog_layout.addWidget(configurations)
        dialog.setLayout(dialog_layout)
        dialog.exec_()

    def setup_database(self):
        dialog = DatabaseSetup(self)
        dialog.setWindowIcon(QtGui.QIcon('jam_icon.png'))
        dialog.setWindowTitle('Setup Database')
        dialog.exec_()

        return dialog.result()


class DatabaseSetup(QtWidgets.QDialog):
    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        self.config = configparser.ConfigParser()
        path = os.path.expanduser('~/Documents/JAM/JAMviewer/jam.ini')
        self.config.read(path)

        # Database group
        self.db_edits = {}
        db_box = QtWidgets.QGroupBox('Database', self)
        db_layout = QtWidgets.QGridLayout()
        db_layout.setColumnMinimumWidth(0, 100)
        db_box.setLayout(db_layout)
        host_label = QtWidgets.QLabel('TCP/IP Server: ', db_box)
        host_edit = QtWidgets.QLineEdit(db_box)
        self.db_edits['host'] = host_edit
        host_edit.setText(self.config.get('Database', 'host'))
        port_label = QtWidgets.QLabel('Port: ', db_box)
        port_edit = QtWidgets.QLineEdit(db_box)
        self.db_edits['port'] = port_edit
        port_edit.setText(self.config.get('Database', 'port'))
        port_edit.setMaximumWidth(100)
        db_layout.addWidget(host_label, 0, 0, QtCore.Qt.AlignRight)
        db_layout.addWidget(host_edit, 0, 1)
        db_layout.addWidget(port_label, 0, 2, QtCore.Qt.AlignRight)
        db_layout.addWidget(port_edit, 0, 3)
        user_label = QtWidgets.QLabel('User: ', db_box)
        user_edit = QtWidgets.QLineEdit(db_box)
        self.db_edits['user'] = user_edit
        user_edit.setText(self.config.get('Database', 'user'))
        db_layout.addWidget(user_label, 1, 0, QtCore.Qt.AlignRight)
        db_layout.addWidget(user_edit, 1 ,1)
        pass_label = QtWidgets.QLabel('Password: ', db_box)
        pass_edit = QtWidgets.QLineEdit(db_box)
        self.db_edits['password'] = pass_edit
        pass_edit.setText(self.config.get('Database', 'password'))
        db_layout.addWidget(pass_label, 2, 0, QtCore.Qt.AlignRight)
        db_layout.addWidget(pass_edit, 2, 1)
        db_label = QtWidgets.QLabel('Database: ', db_box)
        db_edit = QtWidgets.QLineEdit(db_box)
        self.db_edits['db'] = db_edit
        db_edit.setText(self.config.get('Database', 'db'))
        db_layout.addWidget(db_label, 3, 0, QtCore.Qt.AlignRight)
        db_layout.addWidget(db_edit, 3, 1)
        db_test_btn = QtWidgets.QPushButton('Test and Save', db_box)
        db_test_btn.clicked.connect(self.test_db)
        db_layout.addWidget(db_test_btn, 3, 3)

        vbox_layout = QtWidgets.QVBoxLayout()
        vbox_layout.addWidget(db_box)
        self.setLayout(vbox_layout)

    def test_db(self):
        success = viewerDatabase.DatabaseManager.test_db_connection(self.db_edits['host'].text(), self.db_edits['port'].text(),
                                                                    self.db_edits['user'].text(),
                                                                    self.db_edits['password'].text(), self.db_edits['db'].text())
        msgbox = QtWidgets.QMessageBox()
        msgbox.setMinimumWidth(500)
        if success:
            msgbox.setText('Connection Successful')
        else:
            msgbox.setText('Connection Failed')
        msgbox.exec_()

        if success:
            for key in self.db_edits.keys():
                self.config.set('Database', key, self.db_edits[key].text())

            path = os.path.expanduser('~/Documents/JAM/JAMviewer/jam.ini')
            with open(path, 'w') as configfile:
                self.config.write(configfile)

            self.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = JamMainWindow(None)
    window.setWindowTitle('JAM')
    # window = ConfigurationWidget(None)
    app.exec_()
