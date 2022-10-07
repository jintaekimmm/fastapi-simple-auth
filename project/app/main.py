from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import auth

app = FastAPI()
app.include_router(auth.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}

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
