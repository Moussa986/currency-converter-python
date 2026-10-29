from datetime import datetime
from decimal import Decimal, InvalidOperation
import sqlite3
from pathlib import Path

import requests
from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "change-this-development-secret"

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "conversions.db"
API_BASE = "https://api.frankfurter.dev/v2"

# Used if the currency-list API is temporarily unavailable.
FALLBACK_CURRENCIES = {
    "AUD": "Australian Dollar",
    "CAD": "Canadian Dollar",
    "CHF": "Swiss Franc",
    "CNY": "Chinese Yuan",
    "CZK": "Czech Koruna",
    "DKK": "Danish Krone",
    "EUR": "Euro",
    "GBP": "British Pound",
    "HKD": "Hong Kong Dollar",
    "HUF": "Hungarian Forint",
    "IDR": "Indonesian Rupiah",
    "ILS": "Israeli New Shekel",
    "INR": "Indian Rupee",
    "ISK": "Icelandic Króna",
    "JPY": "Japanese Yen",
    "KRW": "South Korean Won",
    "MXN": "Mexican Peso",
    "MYR": "Malaysian Ringgit",
    "NOK": "Norwegian Krone",
    "NZD": "New Zealand Dollar",
    "PHP": "Philippine Peso",
    "PLN": "Polish Złoty",
    "RON": "Romanian Leu",
    "SEK": "Swedish Krona",
    "SGD": "Singapore Dollar",
    "THB": "Thai Baht",
    "TRY": "Turkish Lira",
    "USD": "United States Dollar",
    "ZAR": "South African Rand",
}

def init_db():
    """Create the local history table if it does not already exist."""
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversion_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                amount TEXT NOT NULL,
                from_currency TEXT NOT NULL,
                to_currency TEXT NOT NULL,
                exchange_rate TEXT NOT NULL,
                converted_amount TEXT NOT NULL,
                rate_date TEXT NOT NULL
            )
        """)
        conn.commit()


def get_currencies():
    """Load currency codes and names from Frankfurter, with a safe fallback."""
    try:
        response = requests.get(f"{API_BASE}/currencies", timeout=8)
        response.raise_for_status()
        data = response.json()

        # v2 currency records include iso_code and name.
        currencies = {
            item["iso_code"]: item["name"]
            for item in data
            if item.get("iso_code") and item.get("name")
        }
        if currencies:
            return dict(sorted(currencies.items()))
    except (requests.RequestException, ValueError, KeyError, TypeError):
        pass

    return dict(sorted(FALLBACK_CURRENCIES.items()))


def fetch_rate(from_currency, to_currency):
    """Return (rate, rate_date) from the API."""
    if from_currency == to_currency:
        return Decimal("1"), "Not required (same currency)"

    url = f"{API_BASE}/rate/{from_currency}/{to_currency}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    rate = Decimal(str(data["rate"]))
    rate_date = str(data["date"])
    return rate, rate_date


def save_conversion(amount, from_currency, to_currency,
                    rate, converted_amount, rate_date):
    """Save one successful conversion to SQLite."""
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            INSERT INTO conversion_history
            (created_at, amount, from_currency, to_currency,
             exchange_rate, converted_amount, rate_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            str(amount), from_currency, to_currency,
            str(rate), str(converted_amount), rate_date
        ))
        conn.commit()


def get_history(limit=10):
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT * FROM conversion_history
            ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
    return rows


@app.route("/", methods=["GET", "POST"])
def index():
    currencies = get_currencies()
    result = None
    form = {
        "amount": "1",
        "from_currency": "USD",
        "to_currency": "INR",
    }

    if request.method == "POST":
        form["amount"] = request.form.get("amount", "").strip()
        form["from_currency"] = request.form.get("from_currency", "").upper().strip()
        form["to_currency"] = request.form.get("to_currency", "").upper().strip()

        try:
            amount = Decimal(form["amount"])
            if not amount.is_finite() or amount <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            flash("Enter a valid amount greater than zero.", "error")
            return render_template(
                "index.html", currencies=currencies,
                form=form, result=None, history=get_history()
            )

        from_currency = form["from_currency"]
        to_currency = form["to_currency"]

        # Validate submitted values instead of trusting browser dropdowns.
        if from_currency not in currencies or to_currency not in currencies:
            flash("Please select currencies from the available dropdowns.", "error")
            return render_template(
                "index.html", currencies=currencies,
                form=form, result=None, history=get_history()
            )

        try:
            rate, rate_date = fetch_rate(from_currency, to_currency)
            converted = (amount * rate).quantize(Decimal("0.01"))
            result = {
                "amount": f"{amount:,.2f}",
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": f"{rate:.6f}",
                "converted": f"{converted:,.2f}",
                "rate_date": rate_date,
            }
            save_conversion(amount, from_currency, to_currency,
                            rate, converted, rate_date)
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            if status in (404, 422):
                message = "This currency pair is not available from the exchange-rate provider."
            else:
                message = f"The exchange-rate API returned an HTTP error ({status}). Try again."
            flash(message, "error")
        except (requests.RequestException, ValueError, KeyError, TypeError):
            flash("Could not retrieve a valid exchange rate. Check your internet connection and try again.", "error")

    return render_template(
        "index.html",
        currencies=currencies,
        form=form,
        result=result,
        history=get_history()
    )


@app.route("/history/clear", methods=["POST"])
def clear_history():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("DELETE FROM conversion_history")
        conn.commit()
    flash("Conversion history cleared.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
