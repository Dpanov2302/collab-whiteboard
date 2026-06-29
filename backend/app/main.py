from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.config import get_settings
from app.routers import admin, auth, boards, comments, elements, health, workspaces, ws

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version='1.0.0',
    debug=settings.DEBUG,
    openapi_url=f'{settings.API_PREFIX}/openapi.json',
    docs_url=f'{settings.API_PREFIX}/docs',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE', 'OPTIONS'],
    allow_headers=['Authorization', 'Content-Type'],
)

app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(workspaces.router, prefix=settings.API_PREFIX)
app.include_router(boards.router, prefix=settings.API_PREFIX)
app.include_router(elements.router, prefix=settings.API_PREFIX)
app.include_router(comments.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)
app.include_router(ws.router, prefix=settings.API_PREFIX)

COMMON_ERROR_RESPONSES = {
    '400': {'description': 'Bad Request'},
    '401': {'description': 'Unauthorized'},
    '403': {'description': 'Forbidden'},
    '404': {'description': 'Not Found'},
    '409': {'description': 'Conflict'},
    '422': {'description': 'Validation Error'},
}


def custom_openapi():
    """Synchronize OpenAPI with real API error behavior.

    FastAPI documents validation errors automatically, but authentication,
    authorization, ownership and conflict responses are raised from dependencies
    and services. Schemathesis checks status-code conformance against OpenAPI,
    so these common negative outcomes must be declared explicitly.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        openapi_version='3.1.0',
    )

    for path, path_item in openapi_schema.get('paths', {}).items():
        if path == f'{settings.API_PREFIX}/health':
            continue
        for method, operation in path_item.items():
            if method.lower() not in {'get', 'post', 'put', 'patch', 'delete'}:
                continue
            responses = operation.setdefault('responses', {})
            for status_code, response in COMMON_ERROR_RESPONSES.items():
                responses.setdefault(status_code, response)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
