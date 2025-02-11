import datetime
import math
import pathlib

import geopandas as gpd


def ensure_path_exists(path: str):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def extract_coords(geo_df: gpd.GeoDataFrame) -> list[tuple[float, float]]:
    poly = geo_df.iloc[0]['geometry']
    print(geo_df)
    try:
        coords = poly.exterior.coords
    except AttributeError as err:
        print("Expected polygon, fallback to point")
        coords = poly.coords

    return coords


## GENERATED WITH GEMINI DO NOT TRUST
def decimal_year(year, month=1, day=1, hour=0, minute=0, second=0):
    """
    Calculates the decimal year for a given date and time.

    Args:
        year: The year.
        month: The month (default: 1).
        day: The day (default: 1).
        hour: The hour (default: 0).
        minute: The minute (default: 0).
        second: The second (default: 0).

    Returns:
        The decimal year as a float. Returns None if there's an error 
        (e.g., invalid date).
    """
    try:
        date_obj = datetime.datetime(year, month, day, hour, minute, second)

        # Calculate the day of the year
        day_of_year = date_obj.timetuple().tm_yday

        # Check for leap year
        is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

        # Calculate the total number of days in the year
        days_in_year = 366 if is_leap else 365

        # Calculate the fractional part of the year
        fractional_year = (day_of_year - 1 + (hour / 24) + (minute / (24 * 60)) + (second / (24 * 60 * 60))) / days_in_year

        decimal_y = year + fractional_year
        return decimal_y

    except ValueError:  # Handle invalid date combinations
        print("Error: Invalid date.")
        return None  # Or raise the exception if you prefer

    except Exception as e: # Catch other potential errors
        print(f"An error occurred: {e}")
        return None


def decimal_year_to_date(decimal_year):
    """
    Converts a decimal year (e.g., 2023.5) to a datetime.date object.

    Args:
        decimal_year: A float representing the year in decimal format.

    Returns:
        datetime.date: A date object representing the corresponding date.
                     Returns None if the input is not a valid number.
    """
    try:
        year = int(decimal_year)
        fractional_year = decimal_year - year

        if fractional_year < 0 or fractional_year >= 1:
            raise ValueError("Fractional year part must be between 0 and 1 (exclusive of 1).")

        start_of_year = datetime.date(year, 1, 1)
        end_of_year = datetime.date(year, 12, 31)
        days_in_year = (end_of_year - start_of_year).days + 1 # +1 to include the end date

        day_of_year = round(fractional_year * days_in_year)

        if day_of_year >= days_in_year: # Handle edge case where rounding might push it to next year
            day_of_year = days_in_year -1 # Last day of the year

        if day_of_year < 0: # Should not happen with valid fractional year, but for robustness
            day_of_year = 0

        target_date = start_of_year + datetime.timedelta(days=day_of_year)
        return target_date

    except (TypeError, ValueError) as e:
        print(f"Error: Invalid input. {e}")
        return None


def yearday_to_date(yearday_str):
    """
    Converts a date string in YYYY.DDD format (year and day number) to a datetime.date object.

    Args:
        yearday_str: A string in "YYYY.DDD" format, e.g., "2023.200".

    Returns:
        datetime.date: A date object representing the corresponding date.
                     Returns None if the input string is not in the correct format or represents an invalid date.
    """
    try:
        year_part, day_part = yearday_str.split('.')
        year = int(year_part)
        day_number = int(day_part)

        if not (1 <= day_number <= 366): # Basic day number check, leap year handling is done by datetime
            raise ValueError("Day number out of valid range (1-366).")

        start_of_year = datetime.date(year, 1, 1)
        target_date = start_of_year + datetime.timedelta(days=day_number - 1) # Subtract 1 because day_number is 1-indexed

        # Validate that the calculated date is still within the same year
        if target_date.year != year:
            raise ValueError("Day number is too high for the given year (considering leap year).")

        return target_date

    except ValueError as ve:
        print(f"Error: Invalid date format or value. {ve}")
        return None
    except AttributeError: # if split fails because input is not a string
        print(f"Error: Input must be a string in 'YYYY.DDD' format.")
        return None


def test_gemini_generated_func():
        # Example usage:
    year = 2023
    month = 6
    day = 15
    hour = 0
    minute = 0
    second = 0

    dec_year = decimal_year(year, month, day, hour, minute, second)

    if dec_year is not None:
        print(f"Decimal year for {year}-{month}-{day} {hour}:{minute}:{second}: {dec_year}")

    year = 2024
    month = 2
    day = 29 # Leap year

    dec_year = decimal_year(year, month, day)

    if dec_year is not None:
        print(f"Decimal year for {year}-{month}-{day}: {dec_year}")


    # year = 2024
    # month = 2
    # day = 30 # Not a valid date

    # dec_year = decimal_year(year, month, day)

    # if dec_year is not None:
    #     print(f"Decimal year for {year}-{month}-{day}: {dec_year}")

    # # Example with just year:
    # decimal_year_only = decimal_year(2023)
    # if decimal_year_only is not None:
    #     print(f"Decimal year for 2023: {decimal_year_only}")  # Defaults to Jan 1st, 00:00:00

    
    # Example usage:
    # decimal_year_val = 2024.456
    decimal_year_val = dec_year

    date_time_obj = decimal_year_to_date(decimal_year_val)
    print(date_time_obj)
    if date_time_obj:
        print(f"Date and time for {decimal_year_val}: {date_time_obj}")


if __name__ == "__main__":
    # test_gemini_generated_func()
    # timestamp = yearday_to_date("2003.169")
    timestamp = yearday_to_date("2010.001")
    dec_year = decimal_year(year=timestamp.year, month=timestamp.month, day=timestamp.day)
    print(dec_year)