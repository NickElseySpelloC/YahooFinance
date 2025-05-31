"""Uses the yfinance library to fetch and display the historical stock prices of the specified stocks and write the data to a CSV file."""
import csv
import sys

import pandas as pd
import yfinance as yf
import yfinance.shared as yfshared
from sc_utility import SCConfigManager, SCLogger

from config_schemas import ConfigSchema

CONFIG_FILE = "config.yaml"

def get_yf_errors(logger, log_errors=True):  # noqa: FBT002
    """Get the errors from yfinance shared module. Returns a list of error dict objects."""
    # Extract errors from yfshared._ERRORS.items()
    yf_error_list = yfshared._ERRORS.items()  # noqa: SLF001

    if yf_error_list is None:
        return None

    # Convert errors into a list of dictionaries
    error_list = []
    for symbol, error in yf_error_list:
        error_item = {
            "Symbol": symbol,
            "Error": error,
        }
        error_list.append(error_item)

    if log_errors:
        for error in error_list:
            logger.log_message(f"Symbol: {error['Symbol']}, Error: {error['Error']}", "warning")

    return error_list

def get_stock_data(config, logger, symbols):
    """Fetch historical stock data for the given symbols using yfinance. Returns a DataFrame and error list."""
    # Define parameters
    yf_period = config.get("Yahoo", "Period")
    yf_interval = config.get("Yahoo", "Interval")

    logger.log_message(f"Fetching data for symbols: {symbols}", "debug")
    # Fetch data from Yahoo Finance
    try:
        # Download data
        data = yf.download(
            tickers=symbols,
            period=yf_period,
            interval=yf_interval,
            group_by="ticker",
            auto_adjust=True,
            threads=True,
        )

        # Check if the data is empty
        if data.empty:
            logger.log_fatal_error("No data returned. Check if the parameters (e.g., period, interval) are valid.")
            get_yf_errors(logger)
            return None, 0

        if config.get("Files", "LogFileVerbosity") == "all":
            # Print the entire DataFrame for debugging purposes
            stock_data = {}
            for symbol in symbols:
                if symbol in data.columns.get_level_values(0):
                    stock_data[symbol] = data[symbol]

            # Display the dictionary
            for symbol, df in stock_data.items():
                print(f"\n=== {symbol} ===")
                print(df)

        # Validate columns for each symbol
        for symbol in symbols:
            if symbol in data.columns.get_level_values(0):
                required_columns = {"Open", "High", "Low", "Close", "Volume"}
                if not required_columns.issubset(data[symbol].columns):
                    logger.log_fatal_error(f"Missing expected columns for symbol {symbol}. Data might be incomplete.")
                    get_yf_errors(logger)
                    return None, 0
            else:
                logger.log_fatal_error(f"Symbol {symbol} not found in the returned data.")
                get_yf_errors(logger)
                return None, 0

        # Now see if there are any Yahoo errors from the download call
        error_list = get_yf_errors(logger)

        # Look for any global errors
        # Look at the error_list list and see if any of the Error values start with 'YFRateLimitError'
        if any(error["Error"].startswith("YFRateLimitError") for error in error_list):
            logger.log_fatal_error("Yahoo Finance rate limit error. Please try again later.")
            return None, 0

        if any(error["Error"].contains("Invalid input - interval") for error in error_list):
            logger.log_fatal_error(f"Yahoo Finance API called with invalid interval: {yf_interval}.")
            return None, 0

        if any(error["Error"].contains("YFInvalidPeriodError") for error in error_list):
            logger.log_fatal_error(f"Yahoo Finance API called with invalid period: {yf_period}.")
            return None, 0

    except Exception as e:  # noqa: BLE001
        logger.log_fatal_error(f"Exception caught when fetching data from Yahoo Finance: {e}", exit_program=True)

    return data, error_list

def extract_stock_data(logger, data, symbols, error_list):
    """
    Extract stock data from the downloaded data and format it into a list of dictionaries.

    :param data: DataFrame containing the downloaded stock data.
    :param symbols: List of stock symbols to extract data for.
    :param error_list: List of errors encountered during the download process.
    :return: List of dictionaries containing the extracted stock data and error count.
    """
    logger.log_message(f"Extracting stock data for symbols: {symbols}", "debug")

    # Output list of dicts
    stock_records = []
    error_count = 0

    # Extract data per symbol and row
    for symbol in symbols:
        symbol_name = None
        symbol_divisor = 1
        symbol_currency = None

        # Check if the symbol is in the error list
        if any(error["Symbol"] == symbol for error in error_list):
            logger.log_message(f"Skipping symbol {symbol} due to previous error reported during download", "debug")
            continue

        if symbol not in data.columns.get_level_values(0):
            continue

        # Call yfinance.Ticker.get_info() andextract the following attributes from the info:
        # displayName or failing that longName
        # currency (convert to uppercase)
        # If currency = GBp, then price is in pence. Divide by 100 to get pounds.
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.get_info()

            symbol_name = info.get("displayName", info.get("longName", "Unknown Name"))
            # Replace "," with " " in the symbol name
            symbol_name = symbol_name.replace(",", " ")
            raw_currency = info.get("currency", "USD")  # Default to USD if not found
            symbol_divisor = 100 if raw_currency == "GBp" else 1  # Convert GBp to GBP by dividing by 100
            symbol_currency = raw_currency.upper()  # Ensure symbol is uppercase

        except (KeyError, AttributeError, TypeError) as e:
            logger.log_message(f"Exception reported when fetching info for symbol {symbol}: {e}", "error")

        symbol_data_frame = data[symbol].reset_index()  # Reset index to get 'Date' as column

        try:    # Try and extract the data
            for _, row in symbol_data_frame.iterrows():
                record = {
                    "Symbol": symbol,
                    "Date": row["Date"].strftime("%Y-%m-%d"),
                    "Name": symbol_name,
                    "Currency": symbol_currency,
                    "Price": float(row["Close"]) / symbol_divisor if not pd.isna(row["Close"]) else 0.0,
                    # "Open": float(row["Open"]) / symbol_divisor if not pd.isna(row["Open"]) else 0.0,
                    # "High": float(row["High"]) / symbol_divisor if not pd.isna(row["High"]) else 0.0,
                    # "Low": float(row["Low"]) / symbol_divisor if not pd.isna(row["Low"]) else 0.0,
                    # "Volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else 0.0,
                }
                # Append each record to the stock_records list
                if record["Price"] != 0:
                    stock_records.append(record)

        except (KeyError, ValueError, TypeError) as e:
            logger.log_message(f"Exception reported when extracting data for symbol {symbol}: {e}", "error")
            error_count += 1
            continue

    # Sort the stock_records by ascending date then symbol
    stock_records.sort(key=lambda x: (x["Date"], x["Symbol"]))

    return stock_records, error_count

def save_to_csv(config, stock_data):
    """Save the extracted fund stock_data to a CSV file."""
    csvfile = config.get("Files", "OutputCSV")
    file_path = config.select_file_location(csvfile)

    # Write the data to a CSV file
    header = ["Symbol", "Date", "Name", "Currency", "Price"]

    with file_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow(header)

        # Write today's new rows
        for row in stock_data:
            writer.writerow(row.values())

    return True

def main():
    """Main function to run the script."""
    # Get our default schema, validation schema, and placeholders
    schemas = ConfigSchema()

    # Initialize the SCConfigManager class
    try:
        config = SCConfigManager(
            config_file=CONFIG_FILE,
            default_config=schemas.default,  # Replace with your default config if needed
            validation_schema=schemas.validation,  # Replace with your validation schema if needed
            placeholders=schemas.placeholders  # Replace with your placeholders if needed
        )
    except RuntimeError as e:
        print(f"Configuration file error: {e}", file=sys.stderr)
        return

    # Initialize the SCLogger class
    try:
        logger = SCLogger(config.get_logger_settings())
    except RuntimeError as e:
        print(f"Logger initialisation error: {e}", file=sys.stderr)
        return

    logger.log_message("Starting Yahoo Finance Downloader utility" , "summary")

    # Setup email
    logger.register_email_settings(config.get_email_settings())

    try:
        yf_symbols = config.get("Yahoo", "Symbols")

        # Download the stock data using yfinance
        yf_data, yf_errors = get_stock_data(config, logger, yf_symbols)

        # Extract the price data into a list of dictionaries
        extract_error_count = 0
        if yf_data is None:
            sys.exit(1)     # Exit if there was an error downloading the data. Error already reported.
        else:
            # Extract the stock data
            stock_prices, extract_error_count = extract_stock_data(logger, yf_data, yf_symbols, yf_errors)

            # Save the data to a CSV file
            if stock_prices is None:
                sys.exit(1)     # Exit if there was an error extracting the data. Error already reported.
            else:
                save_to_csv(config, stock_prices)

            # Send email if we had any download or extract errors
            error_message = None
            if len(yf_errors) > 0:
                error_message = f"There were errors reported with {len(yf_errors)} stocks during the Yahoo Finance downloaded."
                if yf_errors:
                    error_message += "\n"
                    for error in yf_errors:
                        error_message += f"Symbol: {error['Symbol']}, Error: {error['Error']}"

            elif extract_error_count > 0:
                error_message = f"There were errors with {extract_error_count} stocks when extracting data from the downloaded data. See logs for details."

            if error_message is not None:
                # Only send the email if we have not already sent one for this run
                if not logger.get_fatal_error():
                    logger.log_message("Stock errors reporting - sending notification email.", "detailed")
                    logger.send_email("Problems with Yahoo stock download", error_message)

                # Record the error in the fatal error tracking so that we don't send multiple emails
                logger.set_fatal_error(error_message)
                sys.exit(1)

    # Catch any unexpected exceptions
    except Exception as e:  # noqa: BLE001
        logger.log_fatal_error(f"An unexpected error occurred while writing: {e}")
        sys.exit(1)

    logger.log_message("Data extracted and saved to file successfully.", "summary")

    # If the prior run fails, send email that this run worked OK
    if logger.get_fatal_error():
        logger.log_message("Run was successful after a prior failure.", "summary")
        logger.send_email("Run recovery", "Yahoo Finance Downloaded run was successful after a prior failure.")
        logger.clear_fatal_error()

if __name__ == "__main__":
    # Run the main module
    main()

    sys.exit(0)
# End of script
