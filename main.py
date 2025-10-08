from fastapi import FastAPI
from util.database import init_db
from controller.controller_person import router as person_router
from controller.controller_address import router as address_router


# FAST API INSTANCE
app = FastAPI(title="FastAPI + SQLModel - MVC + Repository + Generics")

# Database inicialization
init_db()


app.include_router(person_router)
app.include_router(address_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}