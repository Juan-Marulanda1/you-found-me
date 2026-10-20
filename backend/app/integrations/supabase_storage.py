"""Adaptador REST de Supabase Storage para aislar el proveedor de las rutas."""

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urljoin, urlsplit
from urllib.request import Request, urlopen


class SupabaseStorageError(Exception):
    def __init__(self, *, not_found: bool = False):
        self.not_found = not_found
        super().__init__("Supabase Storage request failed.")


@dataclass(frozen=True)
class SignedUpload:
    token: str
    url: str


class SupabaseStorage:
    def __init__(self, project_url: str, api_key: str, bucket: str):
        self.project_url = project_url.rstrip("/")
        self.api_key = api_key
        self.bucket = bucket

    @property
    def configured(self) -> bool:
        return bool(self.project_url and self.api_key)

    def create_signed_upload(self, path: str) -> SignedUpload:
        response = self._request(
            "POST",
            f"/object/upload/sign/{self._bucket_path(path)}",
            payload={},
        )
        returned_url = response.get("url") or response.get("signedURL")
        if not isinstance(returned_url, str):
            raise SupabaseStorageError()
        signed_url = urljoin(f"{self.api_url}/", returned_url.lstrip("/"))
        token = parse_qs(urlsplit(signed_url).query).get("token", [None])[0]
        if not token:
            raise SupabaseStorageError()
        return SignedUpload(token=token, url=signed_url)

    def get_object_info(self, path: str) -> dict:
        response = self._request("GET", f"/object/info/{self._bucket_path(path)}")
        if not isinstance(response, dict):
            raise SupabaseStorageError()
        return response

    def remove(self, paths: list[str]) -> None:
        if not paths:
            return
        self._request(
            "DELETE",
            f"/object/{quote(self.bucket, safe='')}",
            payload={"prefixes": paths},
        )

    def public_url(self, path: str) -> str:
        return (
            f"{self.api_url}/object/public/"
            f"{quote(self.bucket, safe='')}/{quote(path, safe='/')}"
        )

    @property
    def api_url(self) -> str:
        return f"{self.project_url}/storage/v1"

    def _bucket_path(self, path: str) -> str:
        return f"{quote(self.bucket, safe='')}/{quote(path, safe='/')}"

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        if not self.configured:
            raise SupabaseStorageError()

        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"apikey": self.api_key}
        # Las claves secret nuevas no son JWT.
        # Las service_role antiguas sí requieren el encabezado Bearer.
        if not self.api_key.startswith("sb_secret_"):
            headers["Authorization"] = f"Bearer {self.api_key}"
        if body is not None:
            headers["Content-Type"] = "application/json"

        request = Request(
            f"{self.api_url}{path}",
            data=body,
            method=method,
            headers=headers,
        )
        try:
            with urlopen(request, timeout=10) as response:
                result = response.read()
        except HTTPError as error:
            raise SupabaseStorageError(not_found=error.code == 404) from None
        except (URLError, TimeoutError, OSError):
            raise SupabaseStorageError() from None

        if not result:
            return {}
        try:
            return json.loads(result)
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise SupabaseStorageError() from None
