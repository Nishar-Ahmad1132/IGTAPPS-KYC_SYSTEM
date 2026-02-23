from fastapi import FastAPI
from .database import engine
from .models import Base
from .routers import user
from .routers import upload
from .routers import kyc
from .routers import selfie
from .routers import liveness
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(upload.router)
app.include_router(kyc.router)
app.include_router(selfie.router)
app.include_router(liveness.router)


Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {"msg": "KYC API Running on Port 8080 "}
