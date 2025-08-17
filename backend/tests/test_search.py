from backend.app.routers.search import _normalize


def test_normalize():
    assert _normalize("Samsung Electronics") == "samsungelectronics"
    assert _normalize("삼성-전자") == "삼성전자"
