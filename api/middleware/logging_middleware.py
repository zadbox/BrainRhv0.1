"""
Middleware de logging avec correlation ID pour tracer les requêtes
"""

import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware pour logger toutes les requêtes avec correlation ID"""

    async def dispatch(self, request: Request, call_next):
        # Récupérer ou générer request ID
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))

        # Timer
        start_time = time.time()

        # Log requête entrante
        query_string = f"?{request.url.query}" if request.url.query else ""
        print(f"[API][{request_id}] → {request.method} {request.url.path}{query_string}")

        # Log body si POST/PUT (limité à 500 chars)
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    body_str = body.decode()[:500]
                    print(f"[API][{request_id}]   body: {body_str}...")
            except Exception:
                pass

        # Exécuter la requête
        try:
            response = await call_next(request)

            # Calculer durée
            duration_ms = int((time.time() - start_time) * 1000)

            # Log réponse
            print(f"[API][{request_id}] ← {response.status_code} ({duration_ms}ms)")

            # Ajouter request ID dans les headers de réponse
            response.headers["x-request-id"] = request_id

            return response

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"[API][{request_id}] ✗ ERROR ({duration_ms}ms): {str(e)}")
            raise
