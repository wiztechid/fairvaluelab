# WISS Fair Value Lab 🔥

Automatic fair-value research engine for IDX equities.

## v1 scope

- Yahoo Finance / `yfinance` market and financial-statement data
- DCF based on FCF/share
- FCF Yield fair value
- Historical P/E reconstructed from price + annual earnings
- Historical PBV reconstructed from price + annual book equity
- Justified PBV
- Reverse DCF implied growth
- Confidence-weighted composite fair value
- Model dispersion / confidence
- MA20/50/200, RSI14, MACD, 1M/3M returns and 52-week position

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:8000` and enter an IDX ticker without `.JK`, e.g. `TOTL`, `STAA`, or `CMRY`.

## Valuation philosophy

Intrinsic value and historical/relative valuation are calculated separately, then combined only when the required data is valid. Technical indicators do **not** determine intrinsic value; they provide market/price-in context.

The dashboard reports Bear, Base and Bull fair values, upside/downside versus the latest market price, reverse-DCF implied growth, and model confidence.

> Fair value is a model estimate, not a guarantee or investment recommendation. Always review corporate actions, one-off earnings, share dilution and source-data quality.
