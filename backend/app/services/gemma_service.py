
from ai.extractor import extract_opportunity


def analyze_opportunity(text: str) -> dict:
    """
    Analyze opportunity text using Gemma 4.

    The returned data is extracted AI output,
    not independently verified information.
    """
    return extract_opportunity(text)
