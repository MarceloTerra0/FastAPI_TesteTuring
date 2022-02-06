from fastapi import FastAPI, HTTPException
from models import AtualizarFilme, AtualizarPlaneta, Filme, Planeta, Excluido, InserirPlaneta
import sqlite3
import requests
import sys, asyncio

if sys.platform == "win32" and (3, 8, 0) <= sys.version_info < (3, 9, 0):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI()
conn = sqlite3.connect('Starwars.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
c = conn.cursor()

@app.get('/')
async def root():
    return {'Hello,': 'World!'}

@app.get('/api/v1/planets')
async def fetch_planets(show_deleted: bool):
    query = 'SELECT * FROM Planeta'if show_deleted else 'SELECT * FROM Planeta WHERE Excluido = 0'
    c.execute(query)
    results = [dict(row) for row in c.fetchall()]
    for i,result in enumerate(results):
        c.execute('SELECT FilmeID FROM Planeta_Apareceu_Filme WHERE PlanetaID=?', (result['id'], ))
        lista = [dict(row)['FilmeID'] for row in c.fetchall()]
        results[i][f'Filmes_em_que_apareceu'] = lista  
    return results

@app.get('/api/v1/planets/{planet_id}')
async def fetch_planet(planet_id: int):
    c.execute('SELECT * FROM Planeta WHERE id = ?', (planet_id, ))
    result = [dict(row) for row in c.fetchall()]
    if len(result) != 0:
        result = result[0]
        c.execute('SELECT FilmeID FROM Planeta_Apareceu_Filme WHERE PlanetaID=?', (result['id'], ))
        lista = [dict(row)['FilmeID'] for row in c.fetchall()]
        result[f'Filmes_em_que_apareceu'] = lista
        return result
    raise HTTPException(
        status_code=404,
        detail= f'planeta com o id {planet_id} não existe'
    )

@app.post('/api/v1/planets')
async def registrar_planeta(planeta: InserirPlaneta):
    c.execute('SELECT id FROM Filme')
    lista = [dict(row)['id'] for row in c.fetchall()]
    if not set(planeta.FilmesID).issubset(lista):
        raise HTTPException(
            status_code=400,
            detail= 'Pelo menos um dos filmes inseridos não existe'
        )
    try:
        clima = requests.get(f'https://swapi.dev/api/planets/{planeta.id}/').json()['climate']
        c.execute('INSERT INTO Planeta VALUES (?, ?, ?, ?, ?, ?)', (planeta.id ,planeta.Nome, clima, planeta.Diametro, planeta.Populacao, planeta.Excluido))
        aparicoes = [(Filme, planeta.id, Excluido.Nao) for Filme in planeta.FilmesID]
        print(aparicoes)
        c.executemany('INSERT INTO Planeta_Apareceu_Filme(FilmeID, PlanetaID, Excluido) VALUES (?, ?, ?)', aparicoes)
        conn.commit()
        return {"message": f'Planeta {planeta.Nome} inserido com sucesso',}
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=400,
            detail= 'Já existe um planeta com esse ID'
        )
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail= 'Não existe um planeta com esse id na `swapi`'
        )
    

@app.delete('/api/v1/planets/{planet_id}')
async def delete_planet(planet_id: int):
    if c.execute('UPDATE Planeta SET Excluido = 1 WHERE id=?', (planet_id, )).rowcount == 1:
        c.execute('UPDATE Planeta_Apareceu_Filme SET Excluido = 1 WHERE PlanetaID=?', (planet_id, ))
        conn.commit()
        return {"message": f"Planeta com o id {planet_id} excluido com sucesso"}

    raise HTTPException(
        status_code=404,
        detail= f'Planeta com o id {planet_id} não existe ou já está excluido'
    )

@app.put('/api/v1/planets/{planet_id}')
async def atualizar_planeta_existente(planet_id: int, atualizarPlaneta: AtualizarPlaneta):

    if atualizarPlaneta == {}:
        return {"message": f'Insira dados para atualizar o planeta',}

    planeta_original = await fetch_planet(planet_id)
    #print(atualizarPlaneta, planeta_original)
    if planeta_original == {}:
        return {"message": f'planeta com o id {planet_id} não existe',}

    for key, value in atualizarPlaneta:
        if value == None:
            continue
        if key == 'FilmesID':
            c.execute('SELECT id FROM Filme')
            lista = [dict(row)['id'] for row in c.fetchall()]
            if not set(atualizarPlaneta.FilmesID).issubset(lista):
                return {"message": f'Pelo menos um dos filmes inseridos não existe',}
            values = value.copy()
            values.insert(0, planet_id)
            #DesExclui
            c.execute(f'UPDATE Planeta_Apareceu_Filme SET Excluido = 0 WHERE PlanetaID = ? AND FilmeID IN ({ ("?" if len(values)>1 else "")  + ", ?" * (len(values)-2)} )', values)
            #Apaga
            c.execute(f'UPDATE Planeta_Apareceu_Filme SET Excluido = 1 WHERE PlanetaID = ? AND FilmeID NOT IN ({ ("?" if len(values)>1 else "")  + ", ?" * (len(values)-2)} )', values )
            #Insere
            c.execute('SELECT FilmeID FROM Planeta_Apareceu_Filme WHERE PlanetaId = ? AND Excluido = 0', (planet_id, ))
            lista = [dict(row)['FilmeID'] for row in c.fetchall()]
            lista_insercoes_filmes = list(set(atualizarPlaneta.FilmesID)^set(lista))
            insercoes = [(insercao, planet_id, 0) for insercao in lista_insercoes_filmes]
            c.executemany('INSERT INTO Planeta_Apareceu_Filme(FilmeID, PlanetaID, Excluido) VALUES (?, ?, ?)', insercoes)
                
        planeta_original[f'{key}'] = value

    c.execute('UPDATE Planeta SET Nome = ?, Clima = ?, Diametro = ?, Populacao = ?, Excluido = ? WHERE id = ?', (planeta_original['Nome'], planeta_original['Clima'], planeta_original['Diametro'], planeta_original['Populacao'], planeta_original['Excluido'], planet_id))
    conn.commit()
    return {"message": f'Planeta {planeta_original["Nome"]} atualizado com sucesso',}
    
#------------------------------------------------------------------Filmes------------------------------------------------------------------
@app.get('/api/v1/films')
async def fetch_films():
    c.execute('SELECT * FROM Filme')
    results = [dict(row) for row in c.fetchall()]
    return results

@app.get('/api/v1/films/{film_id}')
async def fetch_film(film_id: int):
    c.execute('SELECT * FROM Filme WHERE id = ?', (film_id, ))
    result = [dict(row) for row in c.fetchall()]
    if len(result) != 0:
        result = result[0]
        return result
    raise HTTPException(
        status_code=404,
        detail= f'Filme com o id {film_id} não existe'
    )

@app.post('/api/v1/films')
async def registrar_filme(filme: Filme):
    try:
        c.execute('INSERT INTO Filme VALUES (?, ?, ?, ?)', (filme.id ,filme.Nome, filme.Data_de_lancamento, filme.Excluido))
        conn.commit()
        return {"message": f'Filme {filme.Nome} inserido com sucesso',}
    except sqlite3.IntegrityError:
        return {"message": f'Já existe um Filme com esse ID',}
    except KeyError:
        return {"message": f'Não existe um Filme com esse id na `swapi`',}
    

@app.delete('/api/v1/films/{film_id}')
async def deletar_filme(film_id: int):
    if c.execute('UPDATE Filme SET Excluido = 1 WHERE id=?', (film_id, )).rowcount == 1:
        c.execute('UPDATE Planeta_Apareceu_Filme SET Excluido = 1 WHERE FilmeID=?', (film_id, ))
        conn.commit()
        return {"message": f"Filme com o id {film_id} excluido com sucesso"}
        
    raise HTTPException(
        status_code=404,
        detail= f'Filme com o id {film_id} não existe ou já está excluido'
    )

@app.put('/api/v1/films/{film_id}')
async def atualizar_filme_existente(film_id: int, atualizarFilme: AtualizarFilme):

    if atualizarFilme == {}:
        return {"message": f'Insira dados para atualizar o filme',}

    filme_original = await fetch_film(film_id)
    if filme_original == {}:
        return {"message": f'filme com o id {film_id} não existe',}

    for key, value in atualizarFilme:
        if value == None:
            continue
        filme_original[f'{key}'] = value

    c.execute('UPDATE Filme SET Nome = ?, Data_de_lancamento = ?, Excluido = ? WHERE id = ?', (filme_original['Nome'], filme_original['Data_de_lancamento'], filme_original['Excluido'], film_id))
    conn.commit()
    return {"message": f'Filme {filme_original["Nome"]} atualizado com sucesso',}

#------------------------------------------------------------------Relacao_Planetas_Filmes------------------------------------------------------------------

@app.get('/api/v1/planets_in_movies')
async def fetch_relacao_planetas_filmes():
    c.execute('select Planeta.Nome as NomePlaneta, Filme.Nome as NomeFilme from Planeta_Apareceu_Filme join Planeta on PlanetaID = Planeta.id join Filme on FilmeID = Filme.id')
    results = [dict(row) for row in c.fetchall()]
    print(results)
    return results