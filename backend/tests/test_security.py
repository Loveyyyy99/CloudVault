import pytest

from app.utils.errors import ApiError
from app.utils.security import safe_filename, sha256_hex, validate_upload


def test_sha256_known_vector():
    assert sha256_hex(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


@pytest.mark.parametrize("raw", ["../../etc/passwd.txt", "..\\..\\win.txt", "/abs/path/x.txt"])
def test_path_traversal_is_stripped(raw):
    n = safe_filename(raw)
    assert "/" not in n and "\\" not in n and ".." not in n


def test_validate_rejects_bad_extension_empty_and_large():
    with pytest.raises(ApiError):
        validate_upload("virus.exe", 10)
    with pytest.raises(ApiError):
        validate_upload("a.txt", 0)
    with pytest.raises(ApiError):
        validate_upload("a.txt", 10**10)
    assert validate_upload("report.pdf", 100) == ("report.pdf", "application/pdf")
