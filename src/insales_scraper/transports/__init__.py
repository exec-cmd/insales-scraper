from .curl_cffi import CurlCFFITransport
from .httpx import HTTPXTransport
from .transport import Transport

TRANSPORT_VARIANTS = {"httpx": HTTPXTransport, "curl_cffi": CurlCFFITransport}

__all__ = ["TRANSPORT_VARIANTS", "CurlCFFITransport", "HTTPXTransport", "Transport"]
