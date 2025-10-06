from fastapi import FastAPI
from pydantic import BaseModel


# Classe pessoa herdando BaseModel from pydantic
class Pessoa(BaseModel):
    name:str
    endereco:str
    # None = None para deixar um atributo como opcional.
    telefone:str | None = None

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/cadastrar/{nome}/{endereco}")
def cadastrar(nome:str, endereco:str):
    return {"message": f"{nome} foi cadastrado com o endereco: {endereco}"}

# creating a path operation .post declaring the class Pessoa as path/query parameter.
@app.post("/cadastrarPessoa/")
async def cadastrarPessoa(p:Pessoa):
    return p