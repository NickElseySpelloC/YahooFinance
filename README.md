# Yahoo Finance Downloaded
This app is a simply wrapper around the yfinance libraries. It makes it easy to download selected Yahoo symbols for a selected time period and append the price information to a CSV file that you can use with your portfolio manager. 

Please also see the companion [InvestSmartExport](https://github.com/NickElseySpelloC/InvestSmartExport) app that can be used to download Aussie wholesale fund prices.

# Features
* Specify multiple symbols to be downloaded at one time
* Specify the time period to download prices for
* Specify the time interval (daily, weekly, etc.) between price points
* Error and retry handling
* Designed to be run as a scheduled task (e.g. from crontab)
* Can send email notifications when there is a critical failure.

# Installation & Setup
## Prerequisites
* Python 3.x installed:
macOS: `brew install python3`
* UV for Python installed:
macOS: 'brew install uvicorn'

The shell script used to run the app (*launch.sh*) is uses the *uv sync* command to ensure that all the prerequitie Python packages are installed in the virtual environment.

# Configuration File 
The script uses the *config.yaml* YAML file for configuration. An example of included with the project (*config.yaml.example*). Copy this to *config.yaml* before running the app for the first time.  Here's an example config file:
```
Yahoo:
    Symbols:
        - MSFT
        - AAPL
        - AMZN
    Period: 3mo
    Interval: 1d

Files:
    OutputCSV: price_data.csv
    Logfile: logfile.log
    LogfileMaxLines: 200
    LogfileVerbosity: detailed
    ConsoleVerbosity: detailed

Email:
    EnableEmail: True
    SendEmailsTo: john.doe@gmail.com
    SMTPServer: smtp.gmail.com
    SMTPPort: 587
    SMTPUsername: john.doe@gmail.com
    SMTPPassword: <Your SMTP password>
    SubjectPrefix: "[Yahoo Finance Downloader] "
```

## Configuration Parameters
### Section: Yahoo

| Parameter | Description | 
|:--|:--|
| Symbols | A list of stock symbols to download data for. You can use any of the symbols listed on [Yahoo Finance site](https://finance.yahoo.com/lookup/)  |
| Period | The window of time to download prices for. Valid periods are 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max | 
| Interval | The time interval between each price point. Valid intervals are 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 4h, 1d, 5d, 1wk, 1mo, 3mo | 

### Section: Files

| Parameter | Description | 
|:--|:--|
| OutputCSV | The name of the CSV file to write prices to. If the file already exists, prices will be appended to the end of the CSV file. | 
| LogfileName | The name of the log file, can be a relative or absolute path. | 
| LogfileMaxLines | Maximum number of lines to keep in the log file. If zero, file will never be truncated. | 
| LogfileVerbosity | The level of detail captured in the log file. One of: none; error; warning; summary; detailed; debug; all | 
| ConsoleVerbosity | Controls the amount of information written to the console. One of: error; warning; summary; detailed; debug; all. Errors are written to stderr all other messages are written to stdout | 

### Section: Email

| Parameter | Description | 
|:--|:--|
| EnableEmail | Set to *True* if you want to allow the app to send emails. If True, the remaining settings in this section must be configured correctly. | 
| SMTPServer | The SMTP host name that supports TLS encryption. If using a Google account, set to smtp.gmail.com |
| SMTPPort | The port number to use to connect to the SMTP server. If using a Google account, set to 587 |
| SMTPUsername | Your username used to login to the SMTP server. If using a Google account, set to your Google email address. |
| SMTPPassword | The password used to login to the SMTP server. If using a Google account, create an app password for the app at https://myaccount.google.com/apppasswords  |
| SubjectPrefix | Optional. If set, the app will add this text to the start of any email subject line for emails it sends. |

# Running the Script

`launch.sh`

# Troubleshooting
## "No module named xxx"
Ensure all the Python modules are installed in the virtual environment. Make sure you are running the app via the *launch.sh* script.

## ModuleNotFoundError: No module named 'requests' (macOS)
If you can run the script just fine from the command line, but you're getting this error when running from crontab, make sure the crontab environment has the Python3 folder in it's path. First, at the command line find out where python3 is being run from:

`which python3`

And then add this to a PATH command in your crontab:

`PATH=/usr/local/bin:/usr/bin:/bin`
`0 8 * * * /Users/bob/scripts/YahooFinance/launch.sh`