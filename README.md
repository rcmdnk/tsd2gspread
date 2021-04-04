# tsd2gspread
A tool to write Time Series Data to Google Sheets,
using [gspread](https://github.com/burnash/gspread).

# Requirement

* Python 3.6 or later

# Installation

    $ pip install tsd2gspread

# Preparation

## Service account

Get a service account file (json) for Google APIs following [Authentication — gspread 3.7.0 documentation](https://gspread.readthedocs.io/en/latest/oauth2.html#for-bots-using-service-account).

## Google Sheets

Tsd2Gspread can create new Google Sheets if you want.

Otherwise, you can use prepared Google Sheets.

To allow the service account to access the Sheet,
go to the Sheet and share it with `client_email` from the above service account file.

# Example

## Use Tsd2Gspread directly

    import tsd2gspread

    tg = tsd2gspread.get(
        service_account='~/service_account.json',
        sheet_name='MySheet',
        create=1,
        worksheet_name='MyWork',
        columns='foo,bar,
        share='rcmdnk@gmail.com')

    # Make function to get data
    def get_data():
        foo = 1
        bar = 2
        return (foo, bar)

    # Set data getter
    tg.get_data = get_data

    # Write Time Series Data to Google Sheets
    tg.write()

This will make Google Sheets like:

Datetime|foo|bar
-|-|-
2021-04-30 12:34:56|1|2

Options for `get`:

Option|Mean|Default
:-|:-|:-
config_file|Configuration file of Tsd2Gspread.|None
service_account|Path for the **service_account.json** (Google API service_account file).<br> If  `None`, tsd2gspread(gspread) will use **~/.config/gspread/service_account.json**.|`None`
sheet_name|If set, Sheet is searched by name.|`None`
create|If set to 1, new Sheet is created if it is not found by name.<br>Only works if **sheet_name** is not `None`|`None`
sheet_url|If set, Sheet is searched by URL.|`None`
sheet_key|If set, Sheet is searched by key.|`None`
worksheet_name|Work sheet name.|`None`
columns|Column names separated by `,`.<br>If set, the title like will be inserted when the sheet is created.|`None`
share|Email address of your Google account. <br>If it is not set, only the service account can access to the Sheet and you can not see the Sheet from your account.|`None`
perm_type|Ref [API Reference - gspread](https://gspread.readthedocs.io/en/latest/api.html): client.insert_permission |`user`
perm_type|Ref [API Reference - gspread](https://gspread.readthedocs.io/en/latest/api.html): client.insert_permission|`owner`
add_datetime|If set to 1, current time is added to the data as the first column.|1
timedelta|The time offset from UTC.|0
timeformat|The time format to be written.|`%Y-%m-%d %H:%M:%S`
value_input_option|If `add_datetime` is 1, use `USER_ENTERED` to fill datetime value as datetime.<br>Ref [API Reference - gspread](https://gspread.readthedocs.io/en/latest/api.html):Wworksheet.append_row|`USER_ENTERED`


If you set options by the configuration file, write options as

    OPTION=VALUE

and give the file name as `config_file`.

## Make new inherited class from Tsd2Gspread

    from tsd2gspread import Tsd2Gspread

    class MyClass(Tsd2Gspread):
        def get_data(self):
            foo = 1
            bar = 2
            return (foo, bar)

    tg = MyClass(
        service_account='~/service_account.json',
        sheet_name='MySheet',
        create=1,
        worksheet_name='MyWork',
        columns='foo,bar,
        share='rcmdnk@gmail.com')

    # Write Time Series Data to Google Sheets
    tg.write()
