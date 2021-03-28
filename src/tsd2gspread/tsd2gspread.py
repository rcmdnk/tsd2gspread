#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone


class Tsd2Gspread():
    def __init__(self, config_file=None, **kw):
        self.credentials = None
        self.sheet_name = None
        self.create = None
        self.sheet_url = None
        self.sheet_key = None
        self.worksheet_name = None
        self.columns = None
        self.share = None
        self.perm_type = 'user'
        self.role = 'owner'
        self.timedelta = 0
        self.timeformat = '%Y-%m-%d %H:%M:%S'

        self.config_file = config_file
        self.get_config()
        for k, v in kw.items():
            if v is not None:
                setattr(self, k, v)

        self.gc = None

    def get_data(self):
        return []

    def print_data(self):
        print(self.get_data())

    def get_tsd(self):
        data = self.get_data()
        if not data:
            return None
        if isinstance(data) is not list:
            data = [data]
        now = datetime.now(
            timezone(timedelta(hours=self.timedelta))
        ).strftime(self.timeformat)
        data = [now] + data
        return data

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

    def get_credentials(self):
        if self.gc:
            return self.gc
        import gspread
        if self.credentials:
            self.gc = gspread.service_account(self.credentials)
        else:
            self.gc = gspread.service_account()
        return self.gc

    def get_sheet_by_name(self):
        gc = self.get_credentials()
        names = [x['name'] for x in gc.list_spreadsheet_files()]
        if self.sheet_name in names:
            return gc.open(self.sheet_name)

        if self.create:
            return gc.create(self.sheet_name)
        raise RuntimeError(f'Sheets named {self.sheet_name} was not found.\n'
                           'Please prepare the sheets or use `--create 1`')

    def get_sheet(self):
        if self.sheet_name:
            return self.get_sheet_by_name()
        gc = self.get_credentials()
        if self.sheet_url:
            return gc.open_by_url(self.sheet_url)
        if self.sheet_key:
            return gc.open_by_key(self.sheet_key)
        raise RuntimeError('Set sheet_name, sheet_url or sheet_key')

    def get_worksheet(self):
        sh = self.get_sheet()
        if self.share:
            self.get_credentials().insert_permission(sh.id, self.share,
                                                     self.perm_type,
                                                     self.role)
        titles = [x.title for x in sh.worksheets()]
        if self.worksheet_name in titles:
            return sh.worksheet(self.worksheet_name)
        if not self.columns:
            return sh.add_worksheet(self.worksheet_name, 1, 1)

        columns = self.columns.split(',')
        worksheet = sh.add_worksheet(self.worksheet_name, len(columns), 2)
        worksheet.freeze(rows=1)
        cell_list = worksheet.range(f'A1:A{len(columns)}')
        for i, cell in enumerate(cell_list):
            cell.value = columns[i]
        worksheet.update_cells(cell_list)

    def write(self):
        data = self.get_data()
        if isinstance(data) is not list:
            data = [data]
        if not data:
            print('failed to get data')
            return False

        now = datetime.now(
            timezone(timedelta(hours=self.timedelta))
        ).strftime('%Y-%m-%d %H:%M:%S')
        data = [now] + data
        worksheet = self.get_worksheet()
        worksheet.append_row(data)
        return True
