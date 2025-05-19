'''
Uses the yfinance library to fetch and display the historical stock prices of the specified stocks and write the data to a CSV file.


'''
import sys
import csv
from datetime import datetime
import pandas as pd
import yfinance as yf
import yfinance.shared as yfshared
from utility import ConfigManager, UtilityFunctions


# Create an instance of ConfigManager
system_config = ConfigManager()

# Create an instance of the PowerControllerState
utility_funcs = UtilityFunctions(system_config)

def get_yf_errors(log_errors=True):
    """Get the errors from yfinance shared module. Returns a list of error dict objects."""
    # Extract errors from yfshared._ERRORS.items()
    yf_error_list = yfshared._ERRORS.items()

    if yf_error_list is None:
        return None

    # Convert errors into a list of dictionaries
    error_list = []
    for symbol, error in yf_error_list:
        error_item = {
            "Symbol": symbol,
            "Error": error
        }
        error_list.append(error_item)

    if log_errors:
        for error in error_list:
            utility_funcs.log_message(f"Symbol: {error['Symbol']}, Error: {error['Error']}", "warning")

    return error_list

def get_stock_data(symbols):
    """Fetch historical stock data for the given symbols using yfinance. Returns a DataFrame and error list."""

    # Define parameters
    yf_period = utility_funcs.config['Yahoo']['Period']
    yf_interval = utility_funcs.config['Yahoo']['Interval']

    utility_funcs.log_message(f"Fetching data for symbols: {symbols}", "debug")
    # Fetch data from Yahoo Finance
    try:
        # Download data
        data = yf.download(
            tickers=symbols,
            period=yf_period,
            interval=yf_interval,
            group_by='ticker',
            auto_adjust=True,
            threads=True
        )

        # Check if the data is empty
        if data.empty:
            utility_funcs.report_fatal_error("No data returned. Check if the parameters (e.g., period, interval) are valid.")
            get_yf_errors()
            return None, 0

        if utility_funcs.config["Files"]["LogFileVerbosity"] == "all":
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
                required_columns = {'Open', 'High', 'Low', 'Close', 'Volume'}
                if not required_columns.issubset(data[symbol].columns):
                    utility_funcs.report_fatal_error(f"Missing expected columns for symbol {symbol}. Data might be incomplete.")
                    get_yf_errors()
                    return None, 0
            else:
                utility_funcs.report_fatal_error(f"Symbol {symbol} not found in the returned data.")
                get_yf_errors()
                return None, 0

        # Now see if there are any Yahoo errors from the download call
        error_list = get_yf_errors()

        # Look for any global errors
        # Look at the error_list list and see if any of the Error values start with 'YFRateLimitError'
        if any(error['Error'].startswith('YFRateLimitError') for error in error_list):
            utility_funcs.report_fatal_error("Yahoo Finance rate limit error. Please try again later.")
            return None, 0

        if any(error['Error'].contains('Invalid input - interval') for error in error_list):
            utility_funcs.report_fatal_error(f"Yahoo Finance API called with invalid interval: {yf_interval}.")
            return None, 0

        if any(error['Error'].contains('YFInvalidPeriodError') for error in error_list):
            utility_funcs.report_fatal_error(f"Yahoo Finance API called with invalid period: {yf_period}.")
            return None, 0

    except Exception as e:
        utility_funcs.report_fatal_error(f"Exception caught when fetching data from Yahoo Finance: {e}", exit_program=True)

    return data, error_list

def extract_stock_data(data, symbols, error_list):
    """Extract stock data from the downloaded data and format it into a list of dictionaries.
    
    :param data: DataFrame containing the downloaded stock data.
    :param symbols: List of stock symbols to extract data for.
    :param error_list: List of errors encountered during the download process.
    :return: List of dictionaries containing the extracted stock data and error count.
    """

    utility_funcs.log_message(f"Extracting stock data for symbols: {symbols}", "debug")

    # Output list of dicts
    stock_records = []
    error_count = 0

    # Extract data per symbol and row
    for symbol in symbols:
        # Check if the symbol is in the error list
        if any(error['Symbol'] == symbol for error in error_list):
            utility_funcs.log_message(f"Skipping symbol {symbol} due to previous error reported during download", "debug")
            continue

        if symbol not in data.columns.get_level_values(0):
            continue

        df = data[symbol].reset_index()  # Reset index to get 'Date' as column

        try:    # Try and extract the data
            for _, row in df.iterrows():
                record = {
                    'Date': row['Date'].strftime('%Y-%m-%d'),
                    'Symbol': symbol,
                    'Open': float(row['Open']) if not pd.isna(row['Open']) else 0.0,
                    'High': float(row['High']) if not pd.isna(row['High']) else 0.0,
                    'Low': float(row['Low']) if not pd.isna(row['Low']) else 0.0,
                    'Close': float(row['Close']) if not pd.isna(row['Close']) else 0.0,
                    'Volume': int(row['Volume']) if not pd.isna(row['Volume']) else 0.0,
                }
                # Append each record to the stock_records list
                if record['Open'] != 0.0 or record['High'] != 0.0 or record['Low'] != 0.0 or record['Close'] != 0.0 or record['Volume'] != 0:
                    stock_records.append(record)

        except Exception as e:
            utility_funcs.log_message(f"Exception reported when extracting data for symbol {symbol}: {e}", "error")
            error_count += 1
            continue

    # Sort the stock_records by ascending date then symbol
    stock_records.sort(key=lambda x: (x['Date'], x['Symbol']))

    return stock_records, error_count

def save_to_csv(stock_data):
    """Save the extracted fund stock_data to a CSV file."""

    csv_file_name = utility_funcs.config['Files']['OutputCSV']
    file_path = utility_funcs.config_manager.select_file_location(csv_file_name)

    # Write the data to a CSV file
    header = ['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume']

    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow(header)

        # Write today's new rows
        for row in stock_data:
            writer.writerow(row.values())

    return True

def main_module():
    """Main function to run the script."""
    try:
        yf_symbols = utility_funcs.config['Yahoo']['Symbols']

        # Download the stock data using yfinance
        yf_data, yf_errors = get_stock_data(yf_symbols)

        # Extract the price data into a list of dictionaries
        extract_error_count = 0
        if yf_data is None:
            sys.exit(1)     # Exit if there was an error downloading the data. Error already reported.
        else:
            # Extract the stock data
            stock_prices, extract_error_count = extract_stock_data(yf_data, yf_symbols, yf_errors)

            # Save the data to a CSV file
            if stock_prices is None:
                sys.exit(1)     # Exit if there was an error extracting the data. Error already reported.
            else:
                save_to_csv(stock_prices)

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
                if not utility_funcs.fatal_error_tracking("get"):
                    utility_funcs.log_message("Stock errors reporting - sending notification email.", "detailed")
                    utility_funcs.send_email("Problems with Yahoo stock download", error_message)

                # Record the error in the fatal error tracking so that we don't send multiple emails
                utility_funcs.fatal_error_tracking("set", error_message)
                sys.exit(1)

    # Catch any unexpected exceptions
    except Exception as e:
        utility_funcs.report_fatal_error(f"An unexpected error occurred while writing: {e}")
        sys.exit(1)

    utility_funcs.log_message("Data extracted and saved to file successfully.", "summary")

    # If the prior run fails, send email that this run worked OK
    if utility_funcs.fatal_error_tracking("get"):
        utility_funcs.log_message("Run was successful after a prior failure.", "summary")
        utility_funcs.send_email("Run recovery", "Yahoo Finance Downloaded run was successful after a prior failure.")
        utility_funcs.fatal_error_tracking("set")

if __name__ == "__main__":
    utility_funcs.log_message("Starting Yahoo Finance Downloader utility" , "summary")

    # Run the main module
    main_module()

    sys.exit(0)
# End of script
