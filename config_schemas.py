"""Configuration schemas for use with the SCConfigManager class."""

class ConfigSchema:
    """Base class for configuration schemas."""

    def __init__(self):
        self.default = {
            "Yahoo": {
                "Symbols": ["AAPL", "MSFT", "GOOGL"],
                "Period": "1m",
                "Interval": "1d",
            },
            "Files": {
                "OutputCSV": "yahoo_prices.csv",
                "LogfileName": "YahooFinance.log",
                "LogfileMaxLines": 500,
                "LogfileVerbosity": "detailed",
                "ConsoleVerbosity": "summary",
            },
            "Email": {
                "EnableEmail": False,
                "SendEmailsTo": None,
                "SMTPServer": None,
                "SMTPPort": None,
                "SMTPUsername": None,
                "SMTPPassword": None,
                "SubjectPrefix": None,
            },
        }

        self.placeholders = {
            "AmberAPI": {
                "APIKey": "<Your API Key Here>",
            },
            "Email": {
                "SendEmailsTo": "<Your email address here>",
                "SMTPUsername": "<Your SMTP username here>",
                "SMTPPassword": "<Your SMTP password here>",
            }
        }

        self.validation = {
           "Yahoo": {
                "type": "dict",
                "schema": {
                    "Symbols": {"type": "list", "required": True, "schema": {"type": "string"}},
                    "Period": {
                        "type": "string",
                        "required": False,
                        "nullable": True,
                        "allowed": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                    },
                    "Interval": {
                        "type": "string",
                        "required": False,
                        "nullable": True,
                        "allowed": ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1d", "5d", "1wk", "1mo", "3mo"],
                    },
                },
            },
            "Files": {
                "type": "dict",
                "schema": {
                    "OutputCSV": {"type": "string", "required": True},
                    "LogfileName": {"type": "string", "required": False, "nullable": True},
                    "LogfileMaxLines": {"type": "number", "min": 0, "max": 100000},
                    "LogfileVerbosity": {
                        "type": "string",
                        "required": True,
                        "allowed": ["none", "error", "warning", "summary", "detailed", "debug", "all"],
                    },
                    "ConsoleVerbosity": {
                        "type": "string",
                        "required": True,
                        "allowed": ["error", "warning", "summary", "detailed", "debug", "all"],
                    },
                 },
            },
            "Email": {
                "type": "dict",
                "schema": {
                    "EnableEmail": {"type": "boolean", "required": True},
                    "SendEmailsTo": {"type": "string", "required": False, "nullable": True},
                    "SMTPServer": {"type": "string", "required": False, "nullable": True},
                    "SMTPPort": {"type": "number", "required": False, "nullable": True, "min": 25, "max": 1000},
                    "SMTPUsername": {"type": "string", "required": False, "nullable": True},
                    "SMTPPassword": {"type": "string", "required": False, "nullable": True},
                    "SubjectPrefix": {"type": "string", "required": False, "nullable": True},
                },
            },
        }

        self.csv_header_config = [
            {
                "name": "Symbol",
                "type": "str",
                "sort": 2,
            },
            {
                "name": "Date",
                "type": "date",
                "format": "%Y-%m-%d",
                "sort": 1,
            },
            {
                "name": "Name",
                "type": "str",
            },
            {
                "name": "Currency",
                "type": "str",
            },
            {
                "name": "Price",
                "type": "float",
                "format": ".2f",
            },
        ]

