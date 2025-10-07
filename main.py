from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
#
# import do sqlmodel para construcao da classe
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship

# typing import to DB relations
from typing import Optional, List, Annotated



# Address has to be on top because the python read top to bottom...

# Criating the Address class to relate to Person
class Address(SQLModel, table=True):
    address_id: int | None = Field(default=None, primary_key = True)
    logradouro: str = Field(index=True)
    numero: int = Field(index=True)
    estado: str = Field(index=True)
    cidade: str = Field(index=True)
    bairro: str = Field(index=True)

    #back_populates liga Address e Person
    person: Optional["Person"] = Relationship(back_populates="address")


# Criando a classe Pessoa para conexao com banco de dados, usando SQLModel
# table = true --> Tells SQLModel that it should represent a table in the SQL database.
class Person(SQLModel, table=True):
    # Field(primary_key = True) tells that the ID is the primary key in the SQL database
    person_id: int | None = Field(default=None, primary_key = True)
    # Field(index = True) make SQLModel create a SQL index for this column (attribute)
    name: str = Field(index=True)

    #foreing key from address
    address_id: int = Field(foreign_key="address.address_id")

    # relation
    #back_populates liga Person e Address
    address: Optional[Address] = Relationship(back_populates="person")



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

# WITH DATABASE

# Creating Database Tables on the app inicialization
@app.on_event("startup")
def on_startup():
    # Calls the method that will create all the db tables from the SQLModels created above.
    create_db_and_tables() 


# Creating a Person
@app.post("/create_person/")
def create_person(person: Person, session: SessionDep) -> Person:
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

# Read one Person from database
@app.get("/read_person/{person_id}")
def read_person(person_id: int, session:SessionDep) -> Person:
    person = session.get(Person, person_id)
    if not Person:
        raise HTTPException(status_code=404, detail="Person not found")
    return Person

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
    address = session.get(Address, address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    session.delete(address)
    session.commit()
    return {"ok": True}
