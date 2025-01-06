#!/usr/bin/env python3
from __future__ import annotations

import importlib.metadata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import gspread

__version__ = importlib.metadata.version(__package__)


class Tsd2Gspread:
    """Time Series Data to Google Spread Sheet."""

    def __init__(self, config_file: str | None = None, **kw) -> None:  # type: ignore[no-untyped-def]
        self.log: str | None = None
        self.data: list[Any] | None = None
        self.service_account: str | None = None
        self.sheet_name: str | None = None
        self.create: int | None = None
        self.sheet_url: str | None = None
        self.sheet_key: str | None = None
        self.worksheet_name: str = "Tsd2Gspread"
        self.columns: str | None = None
        self.share: str | None = None
        self.perm_type: str = "user"
        self.role: str = "owner"
        self.add_datetime: int = 1
        self.timedelta: int = 0
        self.timeformat: str = "%Y-%m-%d %H:%M:%S"
        self.value_input_option: gspread.utils.ValueInputOption = (
            gspread.utils.ValueInputOption.user_entered
        )

        self.config_file = config_file
        self.get_config()
        for k, v in kw.items():
            if v is not None:
                setattr(self, k, v)

        self.gc: gspread.client.Client | None = None

        if self.value_input_option not in [
            gspread.utils.ValueInputOption.raw,
            gspread.utils.ValueInputOption.user_entered,
        ]:
            msg = "value_input_option must be 'RAW' or 'USER_ENTERED', not {self.value_input_option}"
            raise ValueError(msg)

    def get_data(self) -> list[Any]:
        return []

    def print_data(self) -> None:
        return

    def get_data_wrapper(self, force: bool = True) -> list[Any]:
        if self.data is not None and not force:
            return self.data
        self.data = self.get_data()
        return self.data

    def get_config(self) -> None:
        if not self.config_file:
            return
        with Path(self.config_file).open() as f:
            for line in f:
                key_value = line.rstrip().split("#")[0].split("=")
                if len(key_value) != 2:
                    continue
                setattr(
                    self,
                    key_value[0].lower(),
                    " ".join(key_value[1:]).strip(" \"'"),
                )

    def get_service_account(self) -> gspread.client.Client:
        if self.gc:
            return self.gc

        if self.service_account:
            self.gc = gspread.service_account(  # type: ignore[attr-defined]
                Path(self.service_account).expanduser(),
            )
        else:
            self.gc = gspread.service_account()  # type: ignore[attr-defined]
        return self.gc

    def set_columns(self, worksheet: gspread.worksheet.Worksheet) -> None:
        if not self.columns:
            return
        columns = self.columns.split(",")
        if self.add_datetime:
            columns = ["Datetime", *columns]
        worksheet.resize(2, len(columns))
        worksheet.freeze(rows=1)
        cell_list = worksheet.range(1, 1, 1, len(columns))
        for i, cell in enumerate(cell_list):
            cell.value = columns[i]
        worksheet.update_cells(cell_list)

    def get_sheet_by_name(
        self, sheet_name: str
    ) -> gspread.spreadsheet.Spreadsheet:
        gc = self.get_service_account()
        names = [x["name"] for x in gc.list_spreadsheet_files()]
        if self.sheet_name in names:
            return gc.open(sheet_name)

        if self.create:
            sheet = gc.create(sheet_name)
            if self.worksheet_name:
                worksheet = sheet.worksheets()[0]
                worksheet.update_title(self.worksheet_name)
                self.set_columns(worksheet)
            return sheet
        msg = (
            f"Sheets named {sheet_name} was not found.\n"
            "Please prepare the sheets or use `--create 1`"
        )
        raise RuntimeError(
            msg,
        )

    def get_sheet(self) -> gspread.spreadsheet.Spreadsheet:
        if self.sheet_name:
            return self.get_sheet_by_name(self.sheet_name)
        gc = self.get_service_account()
        if self.sheet_url:
            return gc.open_by_url(self.sheet_url)
        if self.sheet_key:
            return gc.open_by_key(self.sheet_key)
        msg = "Set sheet_name, sheet_url or sheet_key"
        raise RuntimeError(msg)

    def get_worksheet(self) -> gspread.worksheet.Worksheet:
        sh = self.get_sheet()
        if self.share:
            permissions = sh.list_permissions()
            for p in permissions:
                if (
                    p["emailAddress"] == self.share
                    and p["type"] == self.perm_type
                    and p["role"] == self.role
                ):
                    break
            else:
                self.get_service_account().insert_permission(
                    sh.id,
                    self.share,
                    self.perm_type,
                    self.role,
                )
        titles = [x.title for x in sh.worksheets()]
        if self.worksheet_name in titles:
            return sh.worksheet(self.worksheet_name)
        worksheet = sh.add_worksheet(self.worksheet_name, 1, 1)
        self.set_columns(worksheet)
        return worksheet

    def get_tsd(
        self, data: list[Any] | None = None, force: bool = True
    ) -> list[Any]:
        if data is None:
            data = self.get_data_wrapper(force)
        if not data:
            return []
        if type(data) not in [list, tuple, set]:
            data = [data]
        data = list(data)
        if self.add_datetime:
            now = datetime.now(
                timezone(timedelta(hours=int(self.timedelta))),
            ).strftime("%Y-%m-%d %H:%M:%S")
            data = [now, *data]
        return data

    def log_text(self, tsd_data: list[Any]) -> str:
        return ",".join([str(x) for x in tsd_data])

    def write(self, data: list[Any] | None = None, force: bool = True) -> bool:
        tsd_data = self.get_tsd(data, force)
        if not tsd_data:
            return False
        worksheet = self.get_worksheet()
        worksheet.append_row(
            tsd_data,
            value_input_option=self.value_input_option,
        )
        if self.log:
            with Path(self.log).open("w") as f:
                f.write(self.log_text(tsd_data))
        return True


def get(**kw) -> Tsd2Gspread:  # type: ignore[no-untyped-def]
    return Tsd2Gspread(**kw)
