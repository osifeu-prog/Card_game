"""
מודול DB דמה – מאפשר להריץ את הבוט בלי שגיאות.
כאן אפשר להחליף בהמשך למימוש אמיתי מול PostgreSQL או SQLite.
"""

def init_schema():
    return None

def get_approval_stats():
    return {}

def get_monthly_payments():
    return []

def get_reserve_stats():
    return {}

def log_payment(*args, **kwargs):
    return True

def update_payment_status(*args, **kwargs):
    return True

def has_approved_payment(*args, **kwargs):
    return False

def get_pending_payments():
    return []
