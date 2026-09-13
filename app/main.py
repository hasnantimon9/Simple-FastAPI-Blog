# import psycopg
from fastapi import Depends, FastAPI

# from psycopg.rows import dict_row
from sqlalchemy.orm import Session

from . import models
from .database import engine, get_db

from .config import settings 

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

my_posts = []

from .routers import auth, post, user


@app.get("/sqlalchemy")
def test_posts(db: Session = Depends(get_db)):
	return {'status': "Success"}

app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
