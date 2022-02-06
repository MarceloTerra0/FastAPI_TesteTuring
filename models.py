from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class Excluido(int, Enum):
    Sim = 1
    Nao = 0

class AtualizarPlaneta(BaseModel):
    Nome: Optional[str]
    Clima: Optional[str]
    Diametro: Optional[int]
    Populacao: Optional[int]
    FilmesID: Optional[List[int]]
    Excluido: Optional[Excluido]

class Planeta(BaseModel):
    id: int
    Nome: str
    Clima: str
    Diametro: int
    Populacao: int
    FilmesID: List[int]
    Excluido: Excluido

class InserirPlaneta(BaseModel):
    id: int
    Nome: str
    #Sem Clima, já que o mesmo é pego ao ingerir a api do swapi
    Diametro: int
    Populacao: int
    FilmesID: List[int]
    Excluido: Excluido

class Filme(BaseModel):
    id: int
    Nome: str
    Data_de_lancamento: datetime
    Excluido: Excluido

class AtualizarFilme(BaseModel):
    Nome: Optional[str]
    Data_de_lancamento: Optional[datetime]
    Excluido: Optional[Excluido]

#class UserUpdateRequest(BaseModel)