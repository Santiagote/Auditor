import requests
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class SacarfClient:
    def __init__(self):
        self.base_url = settings.SACARF_API_BASE_URL
        self.timeout = settings.SACARF_API_TIMEOUT
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "SACAUDIT-AuditSystem/1.0",
        })

    def _get(self, path, params=None):
        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            logger.error(f"Conexión rechazada: {url}")
            return None
        except requests.exceptions.Timeout:
            logger.error(f"Timeout: {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP {e.response.status_code}: {url}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado en {url}: {e}")
            return None

    def check_availability(self):
        result = self._get("/auth/profile/")
        if result is None:
            return False, None
        return True, result

    def get_attendance_history(self, page=1):
        return self._get("/attendance/records/history/", {"page": page})

    def get_exceptions(self, page=1):
        return self._get("/attendance/exceptions/audit/", {"page": page})

    def get_students(self, page=1):
        return self._get("/students/", {"page": page})

    def get_swagger_docs(self):
        url = self.base_url.replace("/api/v1", "")
        try:
            response = self.session.get(f"{url}/swagger/", timeout=self.timeout)
            return response.status_code == 200
        except Exception:
            return False

    def test_login(self, email="admin@test.com", password="test"):
        url = f"{self.base_url}/auth/login/"
        try:
            response = self.session.post(
                url,
                json={"email": email, "password": password},
                timeout=self.timeout,
            )
            return response.status_code, response.json() if response.ok else None
        except Exception as e:
            logger.error(f"Error en test_login: {e}")
            return None, None
