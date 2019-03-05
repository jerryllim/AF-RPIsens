import csv
import sqlite3
import pymysql
import datetime
from PySide2 import QtCore, QtWidgets, QtGui, QtSql


class TabPis(QtWidgets.QWidget):
    sensor_list = ['S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S07', 'S08', 'S09', 'S10', 'S11', 'S12', 'S13', 'S14',
                   'S15', 'E01', 'E02', 'E03', 'E04', 'E05']

    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        # Connect to save
        self.conn = sqlite3.connect('serverTest.sqlite')
        self.conn.row_factory = self.dict_factory
        self.cursor = self.conn.cursor()

        # Tree View for the networks
        self.pis_model = QtGui.QStandardItemModel(0, 3, self)
        self.pis_treeview = QtWidgets.QTreeView(self)
        self.pis_treeview.setModel(self.pis_model)
        self.pis_treeview.setAlternatingRowColors(True)
        self.pis_treeview.setRootIsDecorated(False)
        self.pis_treeview.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.pis_treeview.setSortingEnabled(True)
        self.pis_treeview.activated.connect(self.set_fields)
        header = self.pis_treeview.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        for i in range(3):
            self.pis_treeview.resizeColumnToContents(i)

        # Button box for New, Edit, Delete
        button_box = QtWidgets.QVBoxLayout()
        new_btn = QtWidgets.QPushButton('New', self)
        new_btn.clicked.connect(self.new_item)
        button_box.addWidget(new_btn)
        edit_btn = QtWidgets.QPushButton('Edit', self)
        edit_btn.clicked.connect(self.edit_item)
        button_box.addWidget(edit_btn)
        del_btn = QtWidgets.QPushButton('Delete', self)
        del_btn.clicked.connect(self.delete_item)
        button_box.addWidget(del_btn)
        button_box.addStretch()

        # Last box
        vbox_layout = QtWidgets.QVBoxLayout()

        # Top form layout for Nick, IP & Mac
        self.main_lineedits = {}
        form_layout = QtWidgets.QFormLayout()
        nick_edit = QtWidgets.QLineEdit()
        rx = QtCore.QRegExp('([A-Za-z0-9_]){1,15}')
        validator = QtGui.QRegExpValidator(rx)
        nick_edit.setValidator(validator)
        self.main_lineedits['nick'] = nick_edit
        form_layout.addRow('Nickname:', nick_edit)
        ip_edit = QtWidgets.QLineEdit()
        ip_rx = QtCore.QRegExp('((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}')
        ip_validator = QtGui.QRegExpValidator(ip_rx)
        ip_edit.setValidator(ip_validator)
        self.main_lineedits['ip'] = ip_edit
        form_layout.addRow('IP:', ip_edit)
        mac_edit = QtWidgets.QLineEdit()
        mac_edit.setValidator(validator)
        self.main_lineedits['mac'] = mac_edit
        form_layout.addRow('Mac:', mac_edit)

        # Details scroll area with GridLayout
        details = QtWidgets.QScrollArea()
        details.setWidgetResizable(True)
        detail_widget = QtWidgets.QWidget()
        detail_grid = QtWidgets.QGridLayout(detail_widget)
        detail_grid.setColumnStretch(1, 1)
        detail_grid.setColumnStretch(2, 1)

        # TODO set this to be dynamic temp list
        machines = ['-', 'Exia', 'Kyrios', 'Dynames', 'Virtue', 'Nadleeh']
        columns = ['-', 'output', 'col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9', 'col10']
        self.machine_comboboxes = {}
        self.col_comboboxes = {}
        for row, id_ in enumerate(self.sensor_list):
            label = QtWidgets.QLabel(id_)
            machine_combo = QtWidgets.QComboBox()
            machine_combo.addItems(machines)
            self.machine_comboboxes[id_] = machine_combo
            col_combo = QtWidgets.QComboBox()
            col_combo.insertItems(0, columns)
            self.col_comboboxes[id_] = col_combo
            detail_grid.addWidget(label, row, 0)
            detail_grid.addWidget(machine_combo, row, 1)
            detail_grid.addWidget(col_combo, row, 2)

        # Button box for the details
        detail_btn_box = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton('Save', self)
        save_btn.clicked.connect(self.save_item)
        clear_btn = QtWidgets.QPushButton('Clear', self)
        clear_btn.clicked.connect(self.clear_all)
        detail_btn_box.addStretch()
        detail_btn_box.addWidget(save_btn)
        detail_btn_box.addWidget(clear_btn)

        vbox_layout.addLayout(form_layout)
        details.setWidget(detail_widget)
        vbox_layout.addWidget(details)
        vbox_layout.addLayout(detail_btn_box)

        self.hbox_layout = QtWidgets.QHBoxLayout()
        self.hbox_layout.addWidget(self.pis_treeview)
        self.hbox_layout.addLayout(button_box)
        self.hbox_layout.addLayout(vbox_layout)

        self.populate_network_view()

        self.setLayout(self.hbox_layout)

        self.set_all_enabled(False, False)
        self.show()

    def populate_network_view(self):
        self.pis_model.clear()
        self.pis_model.setHorizontalHeaderLabels(['Nickname', 'IP Address', 'Mac'])

        self.cursor.execute("SELECT nickname, ip, mac FROM pis;")

        for row in self.cursor:
            nick_item = QtGui.QStandardItem(row['nickname'])
            ip_item = QtGui.QStandardItem(row['ip'])
            mac_item = QtGui.QStandardItem(row['mac'])
            index = self.pis_model.rowCount()
            self.pis_model.setItem(index, 0, nick_item)
            self.pis_model.setItem(index, 1, ip_item)
            self.pis_model.setItem(index, 2, mac_item)

    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def set_fields(self, index):
        row = index.row()

        for col, id_ in enumerate(['nick', 'ip', 'mac']):
            item = self.pis_model.item(row, col)
            self.main_lineedits[id_].setText(item.text())

        self.set_all_enabled(False, False)

        ip = self.pis_model.item(row, 1).text()
        self.cursor.execute("SELECT * FROM pis WHERE ip = ? LIMIT 1", (ip,))
        ip_dict = self.cursor.fetchone()
        for key in self.sensor_list:
            if ip_dict.get('machine{}'.format(key)):
                self.machine_comboboxes[key].setCurrentText(ip_dict['machine{}'.format(key)])
            else:
                self.machine_comboboxes[key].setCurrentText('-')

            if ip_dict.get('colnum{}'.format(key)):
                self.col_comboboxes[key].setCurrentText(ip_dict['colnum{}'.format(key)])
            else:
                self.col_comboboxes[key].setCurrentText('-')

    def new_item(self):
        self.clear_all(edits=True)

        self.main_lineedits['nick'].setFocus()
        self.set_all_enabled(True, True)

    def edit_item(self):
        if len(self.main_lineedits['nick'].text()) > 0 and not self.main_lineedits['nick'].isEnabled():
            self.set_all_enabled(True, False)

    def delete_item(self):
        index = self.pis_treeview.selectedIndexes()[0]
        row = index.row()
        ip = self.pis_model.item(row, 1).text()

        try:
            self.cursor.execute("DELETE FROM pis WHERE ip = ? LIMIT 1", (ip, ))
            self.conn.commit()
        except sqlite3.Error as error:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText(str(error))
            msgbox.exec_()
        finally:
            self.populate_network_view()

    def save_item(self):
        ip = self.main_lineedits['ip'].text()
        nick = self.main_lineedits['nick'].text()
        mac = self.main_lineedits['mac'].text()

        try:
            if not self.main_lineedits['ip'].isEnabled():
                query = "UPDATE pis SET nickname = ?, mac = ? WHERE ip = ?"
            else:
                query = "INSERT INTO pis (nickname, mac, ip) VALUES (?, ?, ?)"

            self.cursor.execute(query, (nick, mac, ip))

            for key in self.sensor_list:
                machine = self.machine_comboboxes.get(key).currentText()
                colnum = self.col_comboboxes.get(key).currentText()

                self.cursor.execute("UPDATE pis SET machine{0} = ?, colnum{0} = ? WHERE ip = ?".format(key), (machine, colnum, ip))

                # TODO to continue
            self.conn.commit()
            self.new_item()
            self.populate_network_view()

        except sqlite3.Error as error:
            self.conn.rollback()
            print(error)  # TODO log error
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText(str(error))
            msgbox.exec_()

    def set_all_enabled(self, enable, ip):
        for key, edit in self.main_lineedits.items():
            if key == 'ip':
                edit.setEnabled(ip)
            else:
                edit.setEnabled(enable)

        for combo in self.machine_comboboxes.values():
            combo.setEnabled(enable)

        for combo in self.col_comboboxes.values():
            combo.setEnabled(enable)

    def clear_all(self, edits=False):
        if edits:
            for edit in self.main_lineedits.values():
                edit.clear()
                edit.setText('')

        for combo in self.machine_comboboxes.values():
            combo.setCurrentIndex(0)

        for combo in self.col_comboboxes.values():
            combo.setCurrentIndex(0)


class TabEmps(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        # Insertion fields
        insert_grid = QtWidgets.QGridLayout()
        self.insert_edits = {}
        id_label = QtWidgets.QLabel('ID: ')
        id_edit = QtWidgets.QLineEdit()
        rx = QtCore.QRegExp('([A-Za-z0-9]){1,6}')
        validator = QtGui.QRegExpValidator(rx)
        id_edit.setMaximumWidth(70)
        id_edit.setValidator(validator)
        self.insert_edits['id'] = id_edit
        name_label = QtWidgets.QLabel('Name: ')
        name_edit = QtWidgets.QLineEdit()
        name_edit.setMaxLength(20)
        self.insert_edits['name'] = name_edit
        insert_grid.addWidget(id_label, 0, 0)
        insert_grid.addWidget(id_edit, 0, 1)
        insert_grid.addWidget(name_label, 0, 2)
        insert_grid.addWidget(name_edit, 0, 3)

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

        self.populate_model()
        vbox_layout = QtWidgets.QVBoxLayout()
        vbox_layout.addLayout(insert_grid)
        vbox_layout.addWidget(self.emp_treeview)

        # Buttons
        buttons_box = QtWidgets.QVBoxLayout()
        add_btn = QtWidgets.QPushButton('Add', self)
        add_btn.clicked.connect(self.add_emp)
        buttons_box.addWidget(add_btn)
        del_btn = QtWidgets.QPushButton('Delete', self)
        del_btn.clicked.connect(self.delete_emp)
        buttons_box.addWidget(del_btn)
        import_btn = QtWidgets.QPushButton('Import', self)
        import_btn.clicked.connect(self.import_csv)
        buttons_box.addWidget(import_btn)
        buttons_box.addStretch()

        hbox_layout = QtWidgets.QHBoxLayout()
        hbox_layout.addLayout(vbox_layout)
        hbox_layout.addLayout(buttons_box)

        self.setLayout(hbox_layout)
        self.show()

    def populate_model(self):
        self.emp_model.clear()
        self.emp_model.setHorizontalHeaderLabels(['ID', 'Name', 'modified on'])
        # Connect to SQL
        db = pymysql.connect('localhost', 'user', 'pass', 'test')
        with db.cursor() as cursor:
            cursor.execute("SELECT emp_id, name, modified_on FROM emp_table;")

            for row in cursor:
                id_item = QtGui.QStandardItem(row[0])
                name_item = QtGui.QStandardItem(row[1])
                date_item = QtGui.QStandardItem(str(row[2]))
                index = self.emp_model.rowCount()
                self.emp_model.setItem(index, 0, id_item)
                self.emp_model.setItem(index, 1, name_item)
                self.emp_model.setItem(index, 2, date_item)

        db.close()

    def add_emp(self):
        if len(self.insert_edits['id'].text()) > 0:
            try:
                db = pymysql.connect('localhost', 'user', 'pass', 'test')
                id_ = self.insert_edits['id'].text()
                name = self.insert_edits['name'].text()

                with db.cursor() as cursor:
                    cursor.execute("INSERT INTO emp_table (emp_id, name) VALUES (%s, %s);", (id_, name))
                    db.commit()
                    self.insert_edits['id'].setText('')
                    self.insert_edits['name'].setText('')
            except pymysql.Error as error:
                db.rollback()
                print(error)  # TODO log error
                msgbox = QtWidgets.QMessageBox()
                msgbox.setText(str(error))
                msgbox.exec_()
            finally:
                self.populate_model()
                db.close()

    def delete_emp(self):
        rows = set()
        for idx in self.emp_treeview.selectedIndexes():
            rows.add(idx.row())

        try:
            db = pymysql.connect('localhost', 'user', 'pass', 'test')

            with db.cursor() as cursor:
                for row in rows:
                    emp_id = self.emp_model.item(row, 0).text()
                    cursor.execute("DELETE FROM emp_table WHERE emp_id = %s", (emp_id, ))

                db.commit()
        except pymysql.Error as error:
            db.rollback()
            print(error)  # TODO log error
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText(str(error))
            msgbox.exec_()
        finally:
            self.populate_model()
            db.close()

    def import_csv(self):
        path = QtWidgets.QFileDialog.getOpenFileName(self, 'Open CSV', None, 'CSV(*.csv)')
        if path[0] != '':
            with open(path[0], 'r') as csv_file:
                csv_reader = csv.reader(csv_file)
                db = pymysql.connect('localhost', 'user', 'pass', 'test')
                try:
                    with db.cursor() as cursor:
                        csv_list = list(csv_reader)
                        cursor.executemany("INSERT INTO emp_table (emp_id, name) VALUES (%s, %s);", csv_list)

                    db.commit()
                except pymysql.Error as error:
                    db.rollback()
                    print(error)  # TODO log error
                    msgbox = QtWidgets.QMessageBox()
                    msgbox.setText(str(error))
                    msgbox.exec_()
                finally:
                    db.close()
                    self.populate_model()


class TabWidget(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        self.setWindowTitle('JAM Server')
        self.setGeometry(60, 60, 800, 500)

        self.tabs = QtWidgets.QTabWidget()
        self.table_tab = DisplayTable()  # TODO to change
        self.pis_tab = TabPis()
        self.emp_tab = TabEmps()
        self.misc_tab = TabMisc()
        self.tabs.addTab(self.table_tab, 'Display table')
        self.tabs.addTab(self.pis_tab, 'Pis')
        self.tabs.addTab(self.emp_tab, 'Employees')
        self.tabs.addTab(self.misc_tab, 'Misc')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        self.show()


class TabMisc(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        # Request group
        req_box = QtWidgets.QGroupBox('Request')
        req_layout = QtWidgets.QGridLayout()
        req_layout.setColumnMinimumWidth(0, 100)
        dur_label = QtWidgets.QLabel('Duration: ')
        dur_spinbox = QtWidgets.QSpinBox()
        dur_spinbox.setMinimum(1)
        dur_spinbox.setMaximum(90)
        dur_label2 = QtWidgets.QLabel('minutes')
        req_layout.addWidget(dur_label, 0, 0, QtCore.Qt.AlignRight)
        req_layout.addWidget(dur_spinbox, 0, 1)
        req_layout.addWidget(dur_label2, 0, 2)
        req_btn = QtWidgets.QPushButton('Request now')
        req_layout.setAlignment(QtCore.Qt.AlignLeft)
        req_layout.addWidget(req_btn, 0, 3)
        req_box.setLayout(req_layout)

        db_box = QtWidgets.QGroupBox('Database')
        db_layout = QtWidgets.QGridLayout()
        db_layout.setColumnMinimumWidth(0, 100)
        db_box.setLayout(db_layout)
        host_label = QtWidgets.QLabel('TCP/IP Server: ')
        host_edit = QtWidgets.QLineEdit()
        port_label = QtWidgets.QLabel('Port: ')
        port_edit = QtWidgets.QLineEdit()
        port_edit.setMaximumWidth(100)
        db_layout.addWidget(host_label, 0, 0, QtCore.Qt.AlignRight)
        db_layout.addWidget(host_edit, 0, 1)
        db_layout.addWidget(port_label, 0, 2, QtCore.Qt.AlignRight)
        db_layout.addWidget(port_edit, 0, 3)
        user_label = QtWidgets.QLabel('User: ')
        user_edit = QtWidgets.QLineEdit()
        db_layout.addWidget(user_label, 1, 0, QtCore.Qt.AlignRight)
        db_layout.addWidget(user_edit, 1 ,1)
        pass_label = QtWidgets.QLabel('Password: ')
        pass_edit = QtWidgets.QLineEdit()
        db_layout.addWidget(pass_label, 2, 0, QtCore.Qt.AlignRight)
        db_layout.addWidget(pass_edit, 2, 1)
        db_label = QtWidgets.QLabel('Database: ')
        db_edit = QtWidgets.QLineEdit()
        db_layout.addWidget(db_label, 3, 0, QtCore.Qt.AlignRight)
        db_layout.addWidget(db_edit, 3, 1)
        db_test_btn = QtWidgets.QPushButton('Test')
        db_test_btn.clicked.connect(lambda: self.test_db_connection(host_edit.text(), port_edit.text(), user_edit.text(), pass_edit.text(), db_edit.text()))
        db_layout.addWidget(db_test_btn, 3, 3)

        vbox_layout = QtWidgets.QVBoxLayout()
        # vbox_layout.setAlignment(QtCore.Qt.AlignHCenter)
        vbox_layout.addWidget(req_box)
        vbox_layout.addWidget(db_box)
        vbox_layout.addStretch()
        self.setLayout(vbox_layout)
        self.show()

    @staticmethod
    def test_db_connection(host, port, user, password, db):
        msgbox = QtWidgets.QMessageBox()
        msgbox.setMinimumWidth(500)
        try:
            conn = pymysql.connect(host=host, user=user, password=password, database=db, port=port)
            if conn.open:
                msgbox.setText('Connection Successful')
                msgbox.exec_()
            else:
                raise pymysql.Error('conn.open = False')
            conn.close()
        except pymysql.Error as error:
            print(error)
            msgbox.setText('Connection Failed')
            msgbox.exec_()


class DisplayTable(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        self.table_model = QtGui.QStandardItemModel(3, 10)

        self.table_view = QtWidgets.QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setAlternatingRowColors(True)
        v_header = self.table_view.verticalHeader()
        v_header.hide()

        hbox = QtWidgets.QHBoxLayout()
        date_label = QtWidgets.QLabel('Date: ')
        self.date_spin = QtWidgets.QDateEdit()
        self.date_spin.setDate(QtCore.QDate.currentDate())
        start_label = QtWidgets.QLabel('Start: ')
        self.start_spin = QtWidgets.QTimeEdit(QtCore.QTime(7, 0))
        hour_label = QtWidgets.QLabel('Hours: ')
        self.hour_spin = QtWidgets.QSpinBox()
        self.hour_spin.setMinimum(1)
        self.hour_spin.setMaximum(24)
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

    def populate_table(self):
        self.table_model.clear()
        db = pymysql.connect('localhost', 'user', 'pass', 'test')

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
        print(table_hheaders)
        self.table_model.setHorizontalHeaderLabels(table_hheaders)

        output_list = []
        table_vheaders = []
        with db.cursor() as cursor:
            query = "SELECT DISTINCT machine FROM jam_current_table WHERE date_time >= %s AND date_time < %s"
            cursor.execute(query, (start.isoformat(timespec='minutes'), end.isoformat(timespec='minutes')))
            for row in cursor:
                table_vheaders.append(row[0])
        for row, machine in enumerate(table_vheaders):
            output_list.append([0] * len(table_hheaders))
            self.table_model.setItem(row, 0, QtGui.QStandardItem(machine))

        with db.cursor() as cursor:
            query = "SELECT machine, DATE(date_time), HOUR(date_time), SUM(output) FROM jam_current_table " \
                    "WHERE date_time >= %s AND date_time < %s GROUP BY machine, DATE(date_time), HOUR(date_time);"
            cursor.execute(query, (start.isoformat(timespec='minutes'), end.isoformat(timespec='minutes')))

            for row in cursor:
                col = table_hheaders.index('{:02d}'.format(row[2]))
                idx = table_vheaders.index(row[0])
                output_list[idx][col] = row[3]
                # table_model.setItem(idx, col, QtGui.QStandardItem(str(row[3])))

        for idx, row in enumerate(output_list):
            for col, value in enumerate(row):
                if col < 2:
                    continue
                item = QtGui.QStandardItem(str(value))
                if value <= 0:
                    font = QtGui.QFont()
                    font.setBold(True)
                    item.setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                    item.setFont(font)
                self.table_model.setItem(idx, col, item)
            self.table_model.setItem(idx, 1, QtGui.QStandardItem(str(sum(row))))
        # h_header = table_view.horizontalHeader()
        # h_header.hide()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    # app.setWindowTitle('JAM Server')
    # app.setGeometry(60, 60, 800, 500)
    # window = TabPis()
    window = TabWidget()
    app.exec_()
