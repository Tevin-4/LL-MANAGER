from datetime import datetime


def parse_date(value, fmt="%Y-%m-%d"):
    """Parse a date string, returning None if value is falsy. Raises ValueError on bad format."""
    if not value:
        return None
    return datetime.strptime(value, fmt).date()


def parse_datetime(value, fmt="%Y-%m-%dT%H:%M:%S"):
    """Parse a datetime string. Accepts both 'T' separated ISO and plain space separated."""
    if not value:
        return None
    try:
        return datetime.strptime(value, fmt)
    except ValueError:
        return datetime.fromisoformat(value)


def require_fields(data, fields):
    """Return a list of missing required fields from a request payload."""
    missing = [f for f in fields if data.get(f) in (None, "")]
    return missing


def paginate_query(query, request_args, default_per_page=20, max_per_page=100):
    """Apply pagination to a SQLAlchemy query based on request args."""
    page = request_args.get("page", 1, type=int)
    per_page = min(
        request_args.get("per_page", default_per_page, type=int), max_per_page
    )
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return pagination
