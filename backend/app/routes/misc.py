from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def read_root():
    return {"message": "CrStats backend running"}


@router.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Hello {name}"}

