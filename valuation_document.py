def is_valuation_document(d):
    """True only for first-party ticker valuation artifacts.

    Sidecar provenance, collector health/cache, disclosure lists and fixtures are
    intentionally excluded even when they contain a ticker field.
    """
    if not isinstance(d, dict): return False
    ticker=d.get('ticker')
    if not isinstance(ticker,str) or not ticker.strip(): return False
    if not isinstance(d.get('raw'),dict): return False
    return isinstance(d.get('methods'),list) or isinstance(d.get('fairValue'),dict)
