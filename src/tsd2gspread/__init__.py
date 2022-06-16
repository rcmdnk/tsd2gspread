#!/usr/bin/env python3
import os
from datetime import datetime, timedelta, timezone

__version__ = '0.1.11'


class Tsd2Gspread():
    def __init__(self, config_file=None, **kw):
        self.log = None
        self.data = None
        self.service_account = None
        self.sheet_name = None
        self.create = None
        self.sheet_url = None
        self.sheet_key = None
        self.worksheet_name = None
        self.columns = None
        self.share = None
        self.perm_type = 'user'
        self.role = 'owner'
        self.add_datetime = 1
        self.timedelta = 0
        self.timeformat = '%Y-%m-%d %H:%M:%S'
        self.value_input_option = 'USER_ENTERED'

        self.config_file = config_file
        self.get_config()
        for k, v in kw.items():
            if v is not None:
                setattr(self, k, v)

        self.gc = None

    def get_data_wrapper(self, force=True):
        if self.data is not None and not force:
            return self.data
        self.data = self.get_data()
        return self.data

    def get_data(self):
        return []

    def print_data(self):
        print(self.get_data_wrapper())

    def get_config(self):
        if not self.config_file:
            return
        with open(self.config_file) as f:
            for line in f.readlines():
                key_value = line.rstrip().split('#')[0].split('=')
                if len(key_value) != 2:
                    continue
                setattr(self, key_value[0].lower(),
                        ' '.join(key_value[1:]).strip(' "\''))

    def get_service_account(self):
        if self.gc:
            return self.gc
        import gspread
        if self.service_account:
            self.gc = gspread.service_account(
                os.path.expanduser(self.service_account))
        else:
            self.gc = gspread.service_account()
        return self.gc

    def set_columns(self, worksheet):
        if not self.columns:
            return
        columns = self.columns.split(',')
        if self.add_datetime:
            columns = ['Datetime'] + columns
        worksheet.resize(2, len(columns))
        worksheet.freeze(rows=1)
        cell_list = worksheet.range(1, 1, 1, len(columns))
        for i, cell in enumerate(cell_list):
            cell.value = columns[i]
        worksheet.update_cells(cell_list)

    def get_sheet_by_name(self):
        gc = self.get_service_account()
        names = [x['name'] for x in gc.list_spreadsheet_files()]
        if self.sheet_name in names:
            return gc.open(self.sheet_name)

        if self.create:
            sheet = gc.create(self.sheet_name)
            if self.worksheet_name:
                worksheet = sheet.worksheets()[0]
                worksheet.update_title(self.worksheet_name)
                self.set_columns(worksheet)
            return sheet
        raise RuntimeError(f'Sheets named {self.sheet_name} was not found.\n'
                           'Please prepare the sheets or use `--create 1`')

    def get_sheet(self):
        if self.sheet_name:
            return self.get_sheet_by_name()
        gc = self.get_service_account()
        if self.sheet_url:
            return gc.open_by_url(self.sheet_url)
        if self.sheet_key:
            return gc.open_by_key(self.sheet_key)
        raise RuntimeError('Set sheet_name, sheet_url or sheet_key')

    def get_worksheet(self):
        sh = self.get_sheet()
        if self.share:
            permissions = sh.list_permissions()
            for p in permissions:
                if p['emailAddress'] == self.share \
                        and p['type'] == self.perm_type \
                        and p['role'] == self.role:
                    break
            else:
                self.get_service_account().insert_permission(sh.id, self.share,
                                                             self.perm_type,
                                                             self.role)
        titles = [x.title for x in sh.worksheets()]
        if self.worksheet_name in titles:
            return sh.worksheet(self.worksheet_name)
        worksheet = sh.add_worksheet(self.worksheet_name, 1, 1)
        self.set_columns(worksheet)
        return worksheet

    def get_tsd(self, data=None, force=True):
        if data is None:
            data = self.get_data_wrapper(force)
        if not data:
            print('failed to get data')
            return False
        if type(data) not in [list, tuple, set]:
            data = [data]
        data = list(data)
        if self.add_datetime:
            now = datetime.now(
                timezone(timedelta(hours=int(self.timedelta)))
            ).strftime('%Y-%m-%d %H:%M:%S')
            data = [now] + data
        return data

    def write(self, data=None, force=True):
        tsd_data = self.get_tsd(data, force)
        if not tsd_data:
            return False
        worksheet = self.get_worksheet()
        worksheet.append_row(tsd_data, value_input_option=self.value_input_option)
        if self.log:
            with open(self.log, 'w') as f:
                f.write(self.log_text(data, force=False))
        return True

    def log_text(self, data=None, force=True):
        data = self.get_tsd(data, force)
        return ','.join([str(x) for x in data])


def get(**kw):
    return Tsd2Gspread(**kw)
