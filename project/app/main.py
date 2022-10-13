from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import user,auth, roles, permissions

app = FastAPI()
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(roles.router)
app.include_router(permissions.router)


@app.get("/")
async def root():
    return {"message": "i'm alive"}

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/health')
async def health():
    return JSONResponse(content={'status': 'ok'})
