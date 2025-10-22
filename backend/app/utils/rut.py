"""RUT (Chilean Tax ID) validation and normalization utilities."""

import re


def normalize_rut(rut: str) -> str:
    """
    Normalize a Chilean RUT to a consistent format.

    Rules:
    - Remove all non-alphanumeric characters (hyphens, dots, spaces)
    - Convert to lowercase
    - Format: 12345678k (without hyphen)

    Args:
        rut: RUT in any format (e.g., "12.345.678-K", "12345678-k", "12345678K")

    Returns:
        Normalized RUT (e.g., "12345678k")

    Examples:
        >>> normalize_rut("12.345.678-K")
        "12345678k"
        >>> normalize_rut("12345678-k")
        "12345678k"
        >>> normalize_rut("12345678K")
        "12345678k"
    """
    if not rut:
        return ""

    # Remove all non-alphanumeric characters
    clean_rut = re.sub(r'[^0-9kK]', '', rut)

    # Convert to lowercase
    normalized = clean_rut.lower()

    return normalized


def validate_rut(rut: str) -> bool:
    """
    Validate a Chilean RUT using the verification digit algorithm.

    Args:
        rut: RUT to validate (can be in any format)

    Returns:
        True if RUT is valid, False otherwise

    Examples:
        >>> validate_rut("12.345.678-5")
        True
        >>> validate_rut("12345678-5")
        True
        >>> validate_rut("12345678-9")
        False
    """
    # Normalize first
    normalized = normalize_rut(rut)

    if not normalized or len(normalized) < 2:
        return False

    # Extract number and verification digit
    rut_number = normalized[:-1]
    verification_digit = normalized[-1]

    # Verification digit can be 0-9 or k
    if not rut_number.isdigit():
        return False

    if verification_digit not in '0123456789k':
        return False

    # Calculate expected verification digit
    reversed_digits = map(int, reversed(rut_number))
    factors = [2, 3, 4, 5, 6, 7]
    s = sum(d * factors[i % 6] for i, d in enumerate(reversed_digits))

    remainder = (-s) % 11

    if remainder == 10:
        expected_dv = 'k'
    else:
        expected_dv = str(remainder)

    return verification_digit == expected_dv


def format_rut(rut: str) -> str:
    """
    Format a RUT for display with proper formatting.

    Args:
        rut: RUT in any format

    Returns:
        Formatted RUT (e.g., "12.345.678-K")

    Examples:
        >>> format_rut("12345678k")
        "12.345.678-K"
        >>> format_rut("77794858k")
        "77.794.858-K"
    """
    normalized = normalize_rut(rut)

    if not normalized or len(normalized) < 2:
        return rut

    # Extract parts
    rut_number = normalized[:-1]
    verification_digit = normalized[-1].upper()

    # Add dots for thousands separator
    formatted_number = ""
    for i, digit in enumerate(reversed(rut_number)):
        if i > 0 and i % 3 == 0:
            formatted_number = "." + formatted_number
        formatted_number = digit + formatted_number

    return f"{formatted_number}-{verification_digit}"
