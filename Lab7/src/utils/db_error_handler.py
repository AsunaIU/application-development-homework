import logging
from functools import wraps
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar

from litestar.exceptions import HTTPException, NotFoundException
from sqlalchemy.exc import IntegrityError, OperationalError

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def _extract_integrity_detail(exc: IntegrityError) -> str:
    """Return a safe, user-friendly detail for IntegrityError without leaking SQL."""
    try:
        orig = exc.orig
        # orig may be DBAPIError or string-like; guard access
        orig_msg = str(orig).lower() if orig is not None else ""
    except Exception:
        orig_msg = ""

    if "email" in orig_msg:
        return "Email already exists"
    if "username" in orig_msg:
        return "Username already exists"
    # Generic fallback for constraint violation
    return "Database integrity error (duplicate or constraint violation)"


def handle_db_errors(
    fn: Callable[P, Coroutine[Any, Any, R]],
) -> Callable[P, Coroutine[Any, Any, R]]:
    """Decorator to map DB and domain errors to appropriate HTTP responses."""

    @wraps(fn)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return await fn(*args, **kwargs)
        except NotFoundException:
            # Already a proper HTTP 404 — re-raise unchanged
            raise
        except IntegrityError as e:
            logger.exception("IntegrityError in %s", fn.__name__)
            detail = _extract_integrity_detail(e)
            # 409 Conflict for unique/constraint violations
            raise HTTPException(status_code=409, detail=detail) from e
        except OperationalError as e:
            logger.exception("OperationalError (DB) in %s", fn.__name__)
            # Service unavailable — transient DB issues
            raise HTTPException(
                status_code=503, detail="Database unavailable, try again later"
            ) from e
        except ValueError as e:
            # Domain-layer ValueError — map "not found" to 404 when sensible
            msg = str(e) or "Invalid value"
            logger.exception("ValueError in %s: %s", fn.__name__, msg)
            if "not found" in msg.lower():
                raise NotFoundException(detail=msg) from e
            # Treat other ValueErrors as Bad Request
            raise HTTPException(status_code=400, detail=msg) from e
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all: log full traceback, return generic 500 to client
            logger.exception("Unhandled exception in %s", fn.__name__)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    return wrapper
