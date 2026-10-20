from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from time import monotonic
from uuid import UUID

from app.core.exceptions import TooManyAdminPinAttemptsError


@dataclass
class _AttemptState:
    """Fallos recientes y bloqueo vigente de una combinación recurso + IP."""

    failures: deque[float] = field(default_factory=deque)
    locked_until: float = 0


class PinAttemptLimiter:
    """Limita intentos consecutivos de PIN dentro del proceso de la API.

    La clave es (tipo, id de publicación, IP). Tras max_attempts fallos dentro de
    window_seconds, la combinación queda bloqueada durante esa misma ventana.
    El estado vive en memoria: no se comparte entre procesos ni sobrevive reinicios.
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 900):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._states: dict[tuple[str, UUID, str], _AttemptState] = {}
        self._lock = Lock()
        self._operations = 0

    def check(self, resource_type: str, resource_id: UUID, client_ip: str) -> None:
        """Lanza TooManyAdminPinAttemptsError si la combinación está bloqueada."""
        key = (resource_type, resource_id, client_ip)
        now = monotonic()
        with self._lock:
            self._cleanup(now)
            state = self._states.get(key)
            if state is None:
                return
            if state.locked_until > now:
                raise TooManyAdminPinAttemptsError()
            self._trim(state, now)
            if not state.failures:
                self._states.pop(key, None)

    def record_failure(
        self, resource_type: str, resource_id: UUID, client_ip: str
    ) -> None:
        """Registra un PIN incorrecto y activa el bloqueo al llegar al límite."""
        key = (resource_type, resource_id, client_ip)
        now = monotonic()
        with self._lock:
            self._cleanup(now)
            state = self._states.setdefault(key, _AttemptState())
            self._trim(state, now)
            state.failures.append(now)
            if len(state.failures) >= self.max_attempts:
                state.locked_until = now + self.window_seconds

    def record_success(
        self, resource_type: str, resource_id: UUID, client_ip: str
    ) -> None:
        """Reinicia el contador tras un PIN correcto."""
        with self._lock:
            self._states.pop((resource_type, resource_id, client_ip), None)

    def _trim(self, state: _AttemptState, now: float) -> None:
        """Descarta fallos más antiguos que la ventana."""
        while state.failures and now - state.failures[0] >= self.window_seconds:
            state.failures.popleft()

    def _cleanup(self, now: float) -> None:
        self._operations += 1
        # Limpia por lotes para evitar recorrer el mapa en cada intento.
        if self._operations % 256:
            return
        expired = []
        for key, state in self._states.items():
            self._trim(state, now)
            if not state.failures and state.locked_until <= now:
                expired.append(key)
        for key in expired:
            self._states.pop(key, None)


# Instancia compartida por los servicios de productos y avisos.
pin_attempt_limiter = PinAttemptLimiter()
