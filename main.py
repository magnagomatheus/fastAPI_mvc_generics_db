from fastapi import FastAPI
from pydantic import BaseModel
#
# import do sqlmodel para construcao da classe
from sqlmodel import Field, Session, SQLModel, create_engine, select

#class Person:
#    def __init__(self, name: str):
#        self.name = name


#def get_person_name(one_person: Person):
#   return one_person.name

# Classe pessoa herdando BaseModel from pydantic
#class Pessoa000(BaseModel):
#    name:str
#    endereco:str
    # None = None para deixar um atributo como opcional.
#    telefone:str | None = None


# Criando a classe Pessoa para conexao com banco de dados, usando SQLModel
# table = true --> Tells SQLModel that it should represent a table in the SQL database.
class Person(SQLModel, table=true):
    # Field(primary_key = True) tells that the ID is the primary key in the SQL database
    id: int | None = Field(default=None, primary_key = True)
    # Field(index = True) make SQLModel create a SQL index for this column (attribute)
    name: str = Field(index=True)
    address: str = Field(index = True)

class Address(SQLModel, table=true):
    id: int | None = Field(default=None, primary_key = True)
    logradouro: str = Field(index=True)
    numero: int = Field(index=True)
    estado: str = Field(index=True)
    cidade: str = Field(index=True)
    bairro: str = Field(index=True)

# Creating the Engine of SQLModel --> this is what holds the connections to the database
# It's necessary just one engine object for the code to connect to the database.
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# {"check_same_thread": False} allows fastAPI to use the same SQLite db in different thread.
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

#creating the tables for all the table models (Pessoa class above)
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# Creating a Session Dependency --> Session will store the object in memory and keep track of any changes needed in the data, 
# then it uses the engine to communicate with the database.
def get_session():
    with Session(engine) as session:
        yield session

# session dependency
SessionDep = Annotated[Session, Depends(get_session)]

# Now all DB functions are created, so now i will initiate then in the application below.

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


#@app.get("/cadastrar/{nome}/{endereco}")
#def cadastrar(nome:str, endereco:str):
 #   return {"message": f"{nome} foi cadastrado com o endereco: {endereco}"}

# creating a path operation .post declaring the class Pessoa as path/query parameter.
#@app.post("/cadastrarPessoa/")
#async def cadastrarPessoa(p:Pessoa):
 #   return p

#@app.get("/pessoas/")
#def listarPessoas(pessoas: list[Pessoa]):
#    for p in pessoas:
 #       print(p)






# WITH DATABASE

# Creating Database Tables on the app inicialization
@app.on_event("startup")
def on_startup():
    # Calls the method that will create all the db tables from the SQLModels created above.
    create_db_and_tables() 


# Creating a Person
@app.post("/create_person/")
def create_person(person: Pessoa, session: SessionDep) -> Pessoa:
    session.add(person)
    session.commit()
    session.refresh(person)
    return person


# Read Persons from the database

@app.get("/read_persons/")
def read_persons(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le = 100)] = 100,
) -> list[Person]:
    persons = session.exec(select(Person).offset(offset).limit(limit)).all()
    return persons


@app.delete("/person/{person_id}")
def delete_person(person_id: int, session:SessionDep):
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    session.delete(person)
    session.commit()
    return {"ok": True}



# ADDRESS

# Creating a Address
@app.post("/create_address/")
def create_address(address: Address, session: SessionDep) -> Address:
    session.add(address)
    session.commit()
    session.refresh(address)
    return address


# Read Persons from the database

@app.delete("/address/{address_id}")
def delete_address(address_id: int, session:SessionDep):
    person = session.get(Address, address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    session.delete(address)
    session.commit()
    return {"ok": True}
