"""Unit tests for pure functions in resources/lib/drauth.py (no Kodi needed)."""
from resources.lib.drauth import generate_code_challenge, generate_code_verifier


def test_generate_code_verifier_length():
    verifier = generate_code_verifier(64)
    assert len(verifier) == 64


def test_generate_code_challenge_rfc7636_vector():
    # RFC 7636 appendix B test vector
    verifier = 'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk'
    assert generate_code_challenge(verifier) == 'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM'
