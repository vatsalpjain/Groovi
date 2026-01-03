"""Utility helper functions (for future use)"""

def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate long text with ellipsis"""
    return text[:max_length] + "..." if len(text) > max_length else text

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division that handles zero division"""
    try:
        return numerator / denominator if denominator != 0 else default
    except:
        return default