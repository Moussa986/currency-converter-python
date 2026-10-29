# Currency Converter Using Python, Flask and API

A student minor project that converts currencies using the Frankfurter exchange-rate API and saves successful conversions in a local SQLite database.

## Features

- Currency dropdowns populated from the API (with a fallback list if the API is unavailable)
- Convert amount from one supported currency to another
- Swap source and target currencies
- Show exchange rate and the actual rate date returned by the API
- Save and display the 10 most recent conversions
- Clear conversion history
- Input validation and API/network error messages
- SQLite database is created automatically

## Requirements

- Windows 10/11
- Python 3.10 or later recommended
- VS Code with Python extension
- Internet connection for currency data

## Setup in VS Code (Windows)

Open the project folder in VS Code. Open Terminal > New Terminal and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, use Command Prompt in VS Code instead:

```bat
.venv\Scripts\activate.bat
```

Then install and run:

```bat
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser. Keep the terminal running while using the app. Press Ctrl+C in the terminal to stop it.

## How it works

1. The browser submits amount and currency codes to the Flask route `/`.
2. Flask validates the amount and currency selections.
3. Python sends an HTTP GET request to `https://api.frankfurter.dev/v2/rate/BASE/QUOTE`.
4. The API returns JSON containing the base currency, quote currency, rate and rate date.
5. Python calculates `converted amount = amount × exchange rate`.
6. SQLite stores the conversion history.
7. Flask renders the result and history into the HTML template.

## Database

SQLite creates `conversions.db` automatically in the project directory. To reset history, use the Clear history button in the app. To reset the database manually, stop the app and delete `conversions.db`; it will be recreated on the next run.

## Test checklist

- Convert 10 USD to INR.
- Swap the currencies and convert again.
- Convert USD to USD (rate should be 1).
- Enter zero, a negative number, or non-numeric input.
- Try an unsupported currency pair if available.
- Turn off internet and confirm an error is displayed.
- Confirm successful conversions appear in history.
- Clear history and confirm the table is empty.

## Notes and limitations

- Frankfurter supplies reference exchange rates, not guaranteed cash-exchange or real-time trading prices.
- The most recent available rate date may be an earlier business day, such as after a weekend or public holiday. The app displays the API's returned date.
- The app is intended for local educational use. Before deployment, change the Flask secret key, disable debug mode, and add production security settings.
