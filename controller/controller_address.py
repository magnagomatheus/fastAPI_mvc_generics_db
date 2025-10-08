from fastapi import APIRouter, Query, Depends
from typing import List, Annotated
from util.database import SessionDep
from model.dto import AddressCreate, AddressUpdate, AddressPublic
from service.address_service import AddressService

router = APIRouter(prefix="/address", tags=["Address"])

def get_address_service(session: SessionDep) -> AddressService:
    return AddressService(session)

ServiceDep = Annotated[AddressService, Depends(get_address_service)]

@router.post("/", response_model=AddressPublic, status_code=201)
def create_address(address: AddressCreate, service: ServiceDep):
    return service.create(address)


@router.get("/{address_id}", response_model=AddressPublic)
def read_address(address_id: int, service: ServiceDep):
    return service.get(address_id)

@router.patch("/{address_id}", response_model=AddressPublic)
def update_address(address_id: int, address: AddressUpdate, service: ServiceDep):
    return service.update(address_id, address)

@router.delete("/{address_id}", status_code=204)
def delete_hero(address_id: int, service: ServiceDep):
    service.delete(address_id)
    return None