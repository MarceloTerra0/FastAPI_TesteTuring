import json
import sqlite3
from urllib import response
from fastapi.testclient import TestClient
import time
import pytest

from main import test, app, conn, __name__, item
from models import AtualizarFilme, AtualizarPlaneta, Filme, Planeta, Excluido, InserirPlaneta

client = TestClient(app)


def test_create_schema():
    pytest.c.executescript("""

BEGIN TRANSACTION;
DROP TABLE IF EXISTS "Filme";
CREATE TABLE IF NOT EXISTS "Filme" (
	"id"	INTEGER NOT NULL,
	"Nome"	TEXT NOT NULL,
	"Data_de_lancamento"	TEXT NOT NULL,
	"Excluido"	INTEGER NOT NULL,
	PRIMARY KEY("id")
);
DROP TABLE IF EXISTS "Planeta";
CREATE TABLE IF NOT EXISTS "Planeta" (
	"id"	INTEGER NOT NULL,
	"Nome"	TEXT NOT NULL,
	"Clima"	TEXT NOT NULL,
	"Diametro"	INTEGER NOT NULL,
	"Populacao"	INTEGER NOT NULL,
	"Excluido"	INTEGER NOT NULL,
	PRIMARY KEY("id")
);
DROP TABLE IF EXISTS "Planeta_Apareceu_Filme";
CREATE TABLE IF NOT EXISTS "Planeta_Apareceu_Filme" (
	"id"	INTEGER NOT NULL UNIQUE,
	"PlanetaID"	INTEGER NOT NULL,
	"FilmeID"	INTEGER NOT NULL,
	"Excluido"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
INSERT INTO "Filme" VALUES (1,'A morte do jedi','2020-04-23 10:20:30.400000+02:30',0);
INSERT INTO "Filme" VALUES (2,'O jedi não morreu','2021-04-23 10:20:30.400000+02:30',0);
INSERT INTO "Filme" VALUES (3,'O jedi nunca morreu','1970-01-01 00:33:41+00:00',0);
INSERT INTO "Filme" VALUES (4,'Ou será que morreu?','1970-01-01 00:33:41+00:00',0);
INSERT INTO "Filme" VALUES (5,'Não morreu, eu sabia!','2032-04-23 10:20:30.400000+02:30',0);
INSERT INTO "Planeta" VALUES (1,'Marte','vento',55,66,0);
INSERT INTO "Planeta" VALUES (2,'Marte 2','vento',10000,564612,0);
INSERT INTO "Planeta" VALUES (3,'Planeta Voador','string',787878,152314856,0);
INSERT INTO "Planeta" VALUES (5,'Nao lembro','murky',5489645,5164,0);
INSERT INTO "Planeta" VALUES (6,'Planetoide','string',48654,1,1);
INSERT INTO "Planeta_Apareceu_Filme" VALUES (1,1,1,0);
INSERT INTO "Planeta_Apareceu_Filme" VALUES (2,1,2,0);
INSERT INTO "Planeta_Apareceu_Filme" VALUES (3,2,2,0);
INSERT INTO "Planeta_Apareceu_Filme" VALUES (4,6,1,1);
INSERT INTO "Planeta_Apareceu_Filme" VALUES (5,6,2,1);
INSERT INTO "Planeta_Apareceu_Filme" VALUES (10,6,3,1);
INSERT INTO "Planeta_Apareceu_Filme" VALUES (11,6,4,1);
INSERT INTO "Planeta_Apareceu_Filme" VALUES (12,6,5,1);
COMMIT;


""")

def test_read_root():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'Hello,': 'World!'}

def test_test():
    print(test())

def test_read_planets_error_without_bool():
    response = client.get('/api/v1/planets')
    #Sem ?show_deleted=true
    assert response.status_code == 422

def test_read_planets_deleted_true():
    response = client.get('/api/v1/planets?show_deleted=true')
    assert response.status_code == 200
    print(type(response.json()))
    assert response.json() == [
  {
    "id": 1,
    "Nome": "Marte",
    "Clima": "vento",
    "Diametro": 55,
    "Populacao": 66,
    "Excluido": 0,
    "Filmes_em_que_apareceu": [
      1,
      2
    ]
  },
  {
    "id": 2,
    "Nome": "Marte",
    "Clima": "vento",
    "Diametro": 55,
    "Populacao": 66,
    "Excluido": 0,
    "Filmes_em_que_apareceu": [
      2
    ]
  },
  {
    "id": 3,
    "Nome": "sexomaluco",
    "Clima": "string",
    "Diametro": 0,
    "Populacao": 0,
    "Excluido": 1,
    "Filmes_em_que_apareceu": []
  },
  {
    "id": 5,
    "Nome": "string",
    "Clima": "murky",
    "Diametro": 0,
    "Populacao": 0,
    "Excluido": 1,
    "Filmes_em_que_apareceu": []
  },
  {
    "id": 6,
    "Nome": "string",
    "Clima": "string",
    "Diametro": 0,
    "Populacao": 0,
    "Excluido": 1,
    "Filmes_em_que_apareceu": [
      1,
      2,
      3,
      4,
      5
    ]
  }
]

def test_read_planets_deleted_false():
    response = client.get('/api/v1/planets?show_deleted=false')
    assert response.status_code == 200

def test_read_planet():
    response = client.get('/api/v1/planets/1')
    assert response.status_code == 200
    assert response.json() == {
                            "id": 1,
                            "Nome": "Marte",
                            "Clima": "vento",
                            "Diametro": 55,
                            "Populacao": 66,
                            "Excluido": 0,
                            "Filmes_em_que_apareceu": [
                                1,
                                2
                            ]
                            }

def test_create_planet_movie_doesnt_exist():
    json={
            "id": 61,
            "Nome": "string",
            "Diametro": 0,
            "Populacao": 0,
            "FilmesID": [
            0
            ],
            "Excluido": 1
        }
    response = client.post('/api/v1/planets', 
    json=json
    )
    assert response.status_code == 400
    assert response.json() == {"detail": 'Pelo menos um dos filmes inseridos não existe',}

def test_create_planet():
    json={
            "id": 44,
            "Nome": "teste",
            "Diametro": 0,
            "Populacao": 0,
            "FilmesID": [
            1
            ],
            "Excluido": 0
        }
    response = client.post('/api/v1/planets', 
    json=json
    )
    assert response.status_code == 200
    #assert response.json() == {"detail": 'Pelo menos um dos filmes inseridos não existe',}