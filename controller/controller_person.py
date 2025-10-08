from fastapi import APIRouter, Query, Depends
from typing import List, Annotated
from util.database import SessionDep
from model.dto import PersonCreate, PersonUpdate, PersonPublic
from service.person_service import PersonService

router = APIRouter(prefix="/persons", tags=["Persons"])

def get_person_service(session: SessionDep) -> PersonService:
    return PersonService(session)

ServiceDep = Annotated[PersonService, Depends(get_person_service)]

@router.post("/", response_model=PersonPublic, status_code=201)
def create_person(person: PersonCreate, service: ServiceDep):
    return service.create(person)


@router.get("/{person_id}", response_model=PersonPublic)
def read_person(person_id: int, service: ServiceDep):
    return service.get(person_id)

@router.patch("/{person_id}", response_model=PersonPublic)
def update_person(person_id: int, person: PersonUpdate, service: ServiceDep):
    return service.update(person_id, person)

@router.delete("/{person_id}", status_code=204)
def delete_hero(person_id: int, service: ServiceDep):
    service.delete(person_id)
    return None