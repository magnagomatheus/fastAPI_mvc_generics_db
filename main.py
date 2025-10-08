from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
#
# import do sqlmodel para construcao da classe
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship

# typing import to DB relations
from typing import Optional, List, Annotated


### SQLModel Classes creating

# Address has to be on top because the python read top to bottom...


class AddressBase(SQLModel):
    logradouro: str = Field(index=True)
    numero: int = Field(index=True)
    estado: str = Field(index=True)
    cidade: str = Field(index=True)
    bairro: str = Field(index=True) 

# Creating the Address class to relate to Person
class Address(AddressBase, table=True):
    address_id: int | None = Field(default=None, primary_key = True, index=True)
    #back_populates liga Address e Person
    person: Optional["Person"] = Relationship(back_populates="address")

class AddressPublic(AddressBase):
    address_id: int

class AddressCreate(AddressBase):
    pass

class AddressUpdate(AddressBase):
    logradouro: str | None = None
    numero: int | None = None
    estado: str | None = None
    cidade: str | None = None
    bairro: str | None = None

# Criando a classe Pessoa para conexao com banco de dados, usando SQLModel
# table = true --> Tells SQLModel that it should represent a table in the SQL database.

class PersonBase(SQLModel):
    # Field(index = True) make SQLModel create a SQL index for this column (attribute)
    name: str = Field(index=True)
    

class Person(PersonBase, table=True):
    # Field(primary_key = True) tells that the ID is the primary key in the SQL database
    person_id: int | None = Field(default=None, primary_key = True, index=True)
    
    #foreing key from address
    address_id: int = Field(foreign_key="address.address_id")

    # relation
    #back_populates liga Person e Address
    address: Optional[Address] = Relationship(back_populates="person")

class PersonPublic(PersonBase):
    person_id:int

# Create a person bonded with a address
class PersonCreate(PersonBase):
    address_id: Optional[int] = None

class PersonUpdate(PersonBase):
    name: str | None = None




### SQLModel Classes creating


# DATABASE CONFIG TO CONNECT TO CODE

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

# DATABASE CONFIG TO CONNECT TO CODE

# FAST API INSTANCE
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
@app.post("/create_person/", response_model=PersonPublic)
def create_person(person: PersonCreate, session: SessionDep):
    db_person = Person.model_validate(person)
    session.add(db_person)
    session.commit()
    session.refresh(db_person)
    return db_person


# Read Persons from the database
@app.get("/read_persons/", response_model=list[PersonPublic])
def read_persons(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le = 100)] = 100,
) -> list[Person]:
    persons = session.exec(select(Person).offset(offset).limit(limit)).all()
    return persons

# Read a Person from database by id
@app.get("/read_person/{person_id}", response_model=PersonPublic)
def read_person(person_id: int, session:SessionDep) -> Person:
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person

# Update a Person
@app.patch("/update_person/{person_id}", response_model=PersonPublic)
def update_person(person_id:int, person: PersonUpdate, session:SessionDep):
    db_person = session.get(Person, person_id)
    if not db_person:
        raise HTTPException(status_code=404, detail="Hero not found")
    person_data = person.model_dump(exclude_unset=True)
    db_person.sqlmodel_update(person_data)
    session.add(db_person)
    session.commit()
    session.refresh(db_person)
    return db_person


# Delete Person from database by id
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
@app.post("/create_address/", response_model=AddressPublic)
def create_address(address: AddressCreate, session: SessionDep) -> AddressPublic:
    db_address = Address.model_validate(address)
    session.add(db_address)
    session.commit()
    session.refresh(db_address)
    return db_address



# Read a Address from database by id
@app.get("/read_address/{address_id}", response_model=AddressPublic)
def read_address(address_id: int, session:SessionDep) -> Address:
    address = session.get(Address, address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return address


# Update a Address
@app.patch("/update_address/{address_id}", response_model=AddressPublic)
def update_address(address_id:int, address:AddressUpdate, session:SessionDep):
    db_address = session.get(Address, address_id)
    if not db_address:
        raise HTTPException(status_code=404, detail="Hero not found")
    address_data = address.model_dump(exclude_unset=True)
    db_address.sqlmodel_update(address_data)
    session.add(db_address)
    session.commit()
    session.refresh(db_address)
    return db_address


# Delete address from the database
@app.delete("/address_delete/{address_id}")
def delete_address(address_id: int, session:SessionDep):
    address = session.get(Address, address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    session.delete(address)
    session.commit()
    return {"ok": True}
