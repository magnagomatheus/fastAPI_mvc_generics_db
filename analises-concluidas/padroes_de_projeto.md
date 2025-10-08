```markdown
# padroes_de_projeto.md

Este documento detalha a aplicação de padrões de projeto para melhorar a modularidade, o baixo acoplamento e a aderência aos princípios SOLID no projeto.

## 1. Separação de Responsabilidades e Fachada

**Problema:** O arquivo `main.py` possui múltiplas responsabilidades, violando o Princípio da Responsabilidade Única (SRP).

**Solução:** Aplicar o padrão de Fachada (Facade) e a separação de responsabilidades para organizar o código em módulos distintos.

**Implementação:**

1.  **Módulos:**
    *   `models.py`: Define os modelos SQLModel (`Person`, `Address`).
    *   `database.py`: Configura o banco de dados (engine, sessão, funções de inicialização).  Pode-se usar um Singleton para garantir que haja apenas uma instância do engine de banco de dados.
    *   `api/endpoints/person.py`: Define as rotas da API relacionadas a `Person`.
    *   `api/endpoints/address.py`: Define as rotas da API relacionadas a `Address`.
    *   `services.py`: Implementa a camada de serviços com a lógica de negócios.
    *   `main.py`: Inicializa a aplicação FastAPI e registra as rotas.

2.  **Fachada (Facade):** A camada de serviços atua como uma fachada,simplificando o acesso às operações do banco de dados e escondendo a complexidade da interação direta com o SQLModel.

**Exemplo (services.py):**

```python
# services.py
from sqlmodel import Session, select
from models import Person, Address  # Importa os modelos definidos em models.py

class PersonService:
    def __init__(self, session: Session):
        self.session = session

    def create_person(self, person: Person) -> Person:
        self.session.add(person)
        self.session.commit()
        self.session.refresh(person)
        return person

    def get_person_by_id(self, person_id: int) -> Person | None:
        return self.session.get(Person, person_id)

    def list_persons(self, offset: int = 0, limit: int = 10) -> list[Person]:
         return self.session.exec(select(Person).offset(offset).limit(limit)).all()

    def delete_person(self, person_id: int):
        person = self.get_person_by_id(person_id)
        if person:
            self.session.delete(person)
            self.session.commit()
```

**Exemplo (api/endpoints/person.py):**

```python
# api/endpoints/person.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import Annotated

from database import get_session # Importa a função para obter a sessão do banco
from models import Person
from services import PersonService

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]


@router.post("/persons/", response_model=Person)
def create_person(person: Person, session: SessionDep):
    person_service = PersonService(session)
    return person_service.create_person(person)


@router.get("/persons/{person_id}", response_model=Person)
def read_person(person_id: int, session: SessionDep):
    person_service = PersonService(session)
    person = person_service.get_person_by_id(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person

@router.get("/persons/", response_model=list[Person])
def read_persons(session: SessionDep, offset: int = 0, limit: int = 10):
    person_service = PersonService(session)
    persons = person_service.list_persons(offset, limit)
    return persons

@router.delete("/persons/{person_id}")
def delete_person(person_id: int, session: SessionDep):
    person_service = PersonService(session)
    person = person_service.get_person_by_id(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    person_service.delete_person(person_id)
    return {"ok": True}
```

**Benefícios:**

*   Melhora a organização e a legibilidade do código.
*   Facilita a manutenção e a escalabilidade.
*   Permite o desenvolvimento e o teste independentes dos módulos.
*   A camada de serviços centraliza a lógica de negócios, facilitando a reutilização e a testabilidade.

## 2. Inversão de Dependência e Injeção de Dependência

**Problema:** O código depende diretamente de implementações concretas, dificultando a testabilidade e a flexibilidade.

**Solução:** Aplicar o padrão de Inversão de Dependência (DIP) e a Injeção de Dependência (DI) para desacoplar os componentes.

**Implementação:**

1.  **Injeção de Dependência:** Utilizar o sistema de injeção de dependência do FastAPI para fornecer a sessão do banco de dados e as instâncias dos serviços para as rotas da API.  Isso já está sendo feito com `Depends(get_session)`.
2.  **Abstrações (Interfaces):**  Criar interfaces para os serviços (e.g., `PersonServiceProtocol`) e injetar as implementações concretas nas rotas da API.

**Exemplo (Definindo um protocolo para o serviço):**

```python
# services.py
from typing import Protocol, List, Optional
from sqlmodel import Session
from models import Person

class PersonServiceProtocol(Protocol):
    def __init__(self, session: Session):
        ...
    def create_person(self, person: Person) -> Person:
        ...
    def get_person_by_id(self, person_id: int) -> Optional[Person]:
        ...
    def list_persons(self, offset: int = 0, limit: int = 10) -> List[Person]:
        ...
    def delete_person(self, person_id: int):
        ...

class PersonService: #implements PersonServiceProtocol
    def __init__(self, session: Session):
        self.session = session

    def create_person(self, person: Person) -> Person:
        self.session.add(person)
        self.session.commit()
        self.session.refresh(person)
        return person

    def get_person_by_id(self, person_id: int) -> Person | None:
        return self.session.get(Person, person_id)

    def list_persons(self, offset: int = 0, limit: int = 10) -> list[Person]:
         return self.session.exec(select(Person).offset(offset).limit(limit)).all()

    def delete_person(self, person_id: int):
        person = self.get_person_by_id(person_id)
        if person:
            self.session.delete(person)
            self.session.commit()
```

**Exemplo (api/endpoints/person.py - Usando o protocolo):**

```python
# api/endpoints/person.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import Annotated

from database import get_session # Importa a função para obter a sessão do banco
from models import Person
from services import PersonService, PersonServiceProtocol

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]

def get_person_service(session: SessionDep) -> PersonServiceProtocol:
    return PersonService(session)

PersonServiceDep = Annotated[PersonServiceProtocol, Depends(get_person_service)]

@router.post("/persons/", response_model=Person)
def create_person(person: Person, person_service: PersonServiceDep):
    return person_service.create_person(person)


@router.get("/persons/{person_id}", response_model=Person)
def read_person(person_id: int, person_service: PersonServiceDep):
    person = person_service.get_person_by_id(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person

@router.get("/persons/", response_model=list[Person])
def read_persons(person_service: PersonServiceDep, offset: int = 0, limit: int = 10):
    persons = person_service.list_persons(offset, limit)
    return persons

@router.delete("/persons/{person_id}")
def delete_person(person_id: int, person_service: PersonServiceDep):
    person = person_service.get_person_by_id(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    person_service.delete_person(person_id)
    return {"ok": True}
```

**Benefícios:**

*   Torna o código mais flexível e testável.
*   Permite substituir as implementações concretas por mocks ou stubs durante os testes.
*   Reduz o acoplamento entre os diferentes componentes da aplicação.

## 3. Estratégia (Strategy) para Validação

**Problema:** A lógica de validação pode se tornar complexa e variar dependendo do contexto.

**Solução:** Aplicar o padrão Estratégia (Strategy) para encapsular diferentes algoritmos de validação e permitir que sejam selecionados dinamicamente.

**Implementação:**

1.  **Interface de Validação:** Definir uma interface para as estratégias de validação.
2.  **Estratégias Concretas:** Implementar classes concretas para cada algoritmo de validação.
3.  **Contexto:** Criar uma classe de contexto que recebe a estratégia de validação como um parâmetro e a utiliza para validar os dados.

**Exemplo:**

```python
# validations.py
from abc import ABC, abstractmethod

class ValidationStrategy(ABC):
    @abstractmethod
    def validate(self, data: dict) -> bool:
        pass

class PersonNameValidation(ValidationStrategy):
    def validate(self, data: dict) -> bool:
        if not isinstance(data.get("name"), str):
            return False
        return len(data.get("name")) > 3

# services.py
from validations import PersonNameValidation

class PersonService:
    def __init__(self, session: Session, validation_strategy: ValidationStrategy = PersonNameValidation()):
        self.session = session
        self.validation_strategy = validation_strategy

    def create_person(self, person: Person) -> Person:
        if not self.validation_strategy.validate(person.dict()):
            raise ValueError("Invalid person data")
        self.session.add(person)
        self.session.commit()
        self.session.refresh(person)
        return person
```

**Benefícios:**

*   Permite adicionar novas estratégias de validação sem modificar o código existente.
*   Facilita a testabilidade da lógica de validação.
*   Torna o código mais flexível e adaptável a diferentes requisitos de validação.

## 4. Singleton para Engine de Banco de Dados

**Problema:** A criação de múltiplas instâncias do engine de banco de dados pode levar a problemas de concorrência e desempenho.

**Solução:** Aplicar o padrão Singleton para garantir que haja apenas uma instância do engine de banco de dados.

**Implementação:**

```python
# database.py
from sqlmodel import create_engine

class DatabaseEngine:
    _instance = None

    def __new__(cls, database_url: str):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.engine = create_engine(database_url)
        return cls._instance.engine

def get_engine(database_url: str):
    return DatabaseEngine(database_url)
```

**Benefícios:**

*   Garante que haja apenas uma instância do engine de banco de dados.
*   Evita problemas de concorrência e desempenho.
*   Simplifica a configuração do banco de dados.

## 5. Observações Finais

A aplicação destes padrões de projeto visa melhorar a qualidade do código, tornando-o mais modular, flexível, testável e robusto. A refatoração da estrutura do projeto, a implementação da camada de serviços, a inversão de dependência, o uso de estratégias de validação e o padrão Singleton são passos importantes para garantir a sustentabilidade do projeto a longo prazo.
```