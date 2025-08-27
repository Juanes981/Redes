import socket
import threading
import time
import json
import random
import os

HOST = '127.0.0.1'
PORT = 65432

preguntas = {
    'general': [
        {"pregunta": "¿Cuál es el río más largo del mundo?", "opciones": ["Nilo", "Amazonas", "Yangtsé", "Misisipi"], "respuesta": "2"},
        {"pregunta": "¿Quién escribió 'Cien años de soledad'?", "opciones": ["Julio Cortázar", "Gabriel García Márquez", "Jorge Luis Borges", "Mario Vargas Llosa"], "respuesta": "2"},
        {"pregunta": "¿En qué país se encuentra la Gran Muralla China?", "opciones": ["Japón", "Corea del Sur", "China", "Vietnam"], "respuesta": "3"},
        {"pregunta": "¿Qué animal es el mamífero más grande del mundo?", "opciones": ["Elefante", "Ballena azul", "Jirafa", "Tigre"], "respuesta": "2"},
        {"pregunta": "¿Cuántos lados tiene un heptágono?", "opciones": ["5", "6", "7", "8"], "respuesta": "3"},
        {"pregunta": "¿Cuál es la capital de Canadá?", "opciones": ["Toronto", "Vancouver", "Montreal", "Ottawa"], "respuesta": "4"},
        {"pregunta": "¿En qué año llegó el hombre a la luna?", "opciones": ["1969", "1970", "1968", "1971"], "respuesta": "1"},
        {"pregunta": "¿Cuál es el océano más grande del mundo?", "opciones": ["Atlántico", "Índico", "Pacífico", "Ártico"], "respuesta": "3"},
        {"pregunta": "¿Quién pintó 'La noche estrellada'?", "opciones": ["Leonardo da Vinci", "Pablo Picasso", "Vincent van Gogh", "Salvador Dalí"], "respuesta": "3"},
        {"pregunta": "¿Cuál es el metal más abundante en la corteza terrestre?", "opciones": ["Hierro", "Aluminio", "Oro", "Cobre"], "respuesta": "2"},
        {"pregunta": "¿Qué país tiene la mayor población del mundo?", "opciones": ["India", "Estados Unidos", "China", "Brasil"], "respuesta": "1"},
        {"pregunta": "¿Cuál es el único mamífero que puede volar?", "opciones": ["Murciélago", "Ardilla voladora", "Pterodáctilo", "Pingüino"], "respuesta": "1"},
        {"pregunta": "¿Qué instrumento musical tiene cuerdas pero se toca con un arco?", "opciones": ["Guitarra", "Arpa", "Violín", "Piano"], "respuesta": "3"},
        {"pregunta": "¿Cuál es el desierto más grande del mundo?", "opciones": ["Sahara", "Gobi", "Atacama", "Antártico"], "respuesta": "4"},
        {"pregunta": "¿Cuántos huesos tiene el cuerpo humano adulto?", "opciones": ["206", "208", "210", "200"], "respuesta": "1"},
        {"pregunta": "¿Cuál es la capital de Australia?", "opciones": ["Sídney", "Melbourne", "Camberra", "Brisbane"], "respuesta": "3"},
        {"pregunta": "¿Quién escribió la Odisea?", "opciones": ["Sócrates", "Homero", "Platón", "Aristóteles"], "respuesta": "2"},
        {"pregunta": "¿Cuál es el componente principal del aire que respiramos?", "opciones": ["Oxígeno", "Dióxido de carbono", "Nitrógeno", "Argón"], "respuesta": "3"},
        {"pregunta": "¿Qué país ganó la primera Copa Mundial de Fútbol?", "opciones": ["Brasil", "Italia", "Alemania", "Uruguay"], "respuesta": "4"},
        {"pregunta": "¿Cuál es el planeta más cercano al Sol?", "opciones": ["Venus", "Marte", "Mercurio", "Tierra"], "respuesta": "3"},
        {"pregunta": "¿En qué año se disolvió la Unión Soviética?", "opciones": ["1989", "1991", "1993", "1987"], "respuesta": "2"},
        {"pregunta": "¿Qué sustancia química tiene la fórmula H2O?", "opciones": ["Cloruro de sodio", "Metano", "Agua", "Amoníaco"], "respuesta": "3"},
        {"pregunta": "¿Quién es conocido como el padre de la computación?", "opciones": ["Bill Gates", "Alan Turing", "Steve Jobs", "Tim Berners-Lee"], "respuesta": "2"},
        {"pregunta": "¿Cuál es el país más grande del mundo por área terrestre?", "opciones": ["Canadá", "Estados Unidos", "China", "Rusia"], "respuesta": "4"},
        {"pregunta": "¿Cuál es la moneda de Japón?", "opciones": ["Yuan", "Dólar", "Yen", "Euro"], "respuesta": "3"},
        {"pregunta": "¿Cuántos continentes hay basadonos en terminos geograficos?", "opciones": ["5", "6", "7", "8"], "respuesta": "1"},
        {"pregunta": "¿Quién fue el primer presidente de los Estados Unidos?", "opciones": ["Thomas Jefferson", "Abraham Lincoln", "George Washington", "John Adams"], "respuesta": "3"},
        {"pregunta": "¿Cuál es el animal terrestre más rápido?", "opciones": ["León", "Gacela", "Guepardo", "Caballo"], "respuesta": "3"},
        {"pregunta": "¿Qué tipo de animal es una orca?", "opciones": ["Pez", "Foca", "Delfín", "Ballena"], "respuesta": "3"},
        {"pregunta": "¿Cuál es el punto más alto de la Tierra?", "opciones": ["Monte Everest", "Monte Kilimanjaro", "Monte McKinley", "Monte Aconcagua"], "respuesta": "1"}
    ]
}

salas = {}
lock_salas = threading.Lock()
ranking_global = {}
lock_ranking = threading.Lock()

def guardar_rankings():
    """Guarda el ranking global en un archivo JSON."""
    with lock_ranking:
        with open('ranking_global.json', 'w') as f:
            json.dump(ranking_global, f, indent=4)
    print("Rankings guardados en ranking_global.json")

def cargar_rankings():
    """Carga el ranking global desde un archivo JSON."""
    global ranking_global
    if os.path.exists('ranking_global.json'):
        with open('ranking_global.json', 'r') as f:
            ranking_global = json.load(f)
        print("Rankings cargados desde el archivo.")

def manejar_cliente(conn, addr):
    print(f"Conectado a {addr}")
    user_data = None
    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break
            
            peticion = json.loads(data)
            comando = peticion['comando']

            if comando == "registrar_usuario":
                user_data = {'nombre': peticion['nombre_usuario'], 'conn': conn, 'addr': addr}
                print(f"Usuario {user_data['nombre']} registrado desde {addr}")
                conn.sendall(json.dumps({"status": "ok", "mensaje": f"Bienvenido, {user_data['nombre']}!"}).encode('utf-8'))
            
            elif comando == "crear_sala":
                if not user_data:
                    conn.sendall(json.dumps({"status": "error", "mensaje": "Usuario no registrado."}).encode('utf-8'))
                    continue
                
                modo = peticion['modo']
                num_preguntas = peticion.get('num_preguntas', 5)
                sala_id = f"sala_{len(salas) + 1}"
                with lock_salas:
                    salas[sala_id] = {'jugadores': {user_data['nombre']: user_data['conn']}, 'modo': modo, 'estado': 'esperando', 'num_preguntas': num_preguntas, 'puntajes': {user_data['nombre']: 0}, 'preguntas_usadas': []}
                print(f"Sala {sala_id} creada en modo {modo} por {user_data['nombre']}. Preguntas: {num_preguntas}")
                conn.sendall(json.dumps({"status": "ok", "mensaje": f"Sala {sala_id} creada. Esperando jugadores...", "sala_id": sala_id}).encode('utf-8'))
                
                if modo == 1:
                    threading.Thread(target=jugar_sala, args=(sala_id,)).start()

            elif comando == "unirse_sala":
                if not user_data:
                    conn.sendall(json.dumps({"status": "error", "mensaje": "Usuario no registrado."}).encode('utf-8'))
                    continue

                sala_id = peticion['sala_id']
                with lock_salas:
                    if sala_id in salas and len(salas[sala_id]['jugadores']) < salas[sala_id]['modo']:
                        salas[sala_id]['jugadores'][user_data['nombre']] = user_data['conn']
                        salas[sala_id]['puntajes'][user_data['nombre']] = 0
                        print(f"Jugador {user_data['nombre']} se unió a la sala {sala_id}")
                        conn.sendall(json.dumps({"status": "ok", "mensaje": f"Te uniste a la sala {sala_id}", "sala_id": sala_id}).encode('utf-8'))
                        if len(salas[sala_id]['jugadores']) == salas[sala_id]['modo']:
                            threading.Thread(target=jugar_sala, args=(sala_id,)).start()
                    else:
                        conn.sendall(json.dumps({"status": "error", "mensaje": "Sala no encontrada o llena."}).encode('utf-8'))

            elif comando == "ver_rankings":
                with lock_ranking:
                    ranking_ordenado = sorted(ranking_global.items(), key=lambda item: item[1], reverse=True)
                    conn.sendall(json.dumps({"status": "ok", "rankings": ranking_ordenado}).encode('utf-8'))
            
            elif comando == "enviar_respuesta":
                sala_id = peticion['sala_id']
                respuesta_cliente = peticion['respuesta']
                timestamp_cliente = peticion['timestamp']

                with lock_salas:
                    sala = salas.get(sala_id)
                    if not sala or sala['estado'] != 'jugando':
                        continue
                    
                    pregunta_info = sala['pregunta_actual']
                    if pregunta_info['pregunta']['respuesta'].lower() == respuesta_cliente.lower():
                        timestamp_pregunta = pregunta_info['timestamp_envio']
                        latencia = timestamp_cliente - timestamp_pregunta
                        
                        puntos = max(1, 100 - int(latencia * 10)) 
                        sala['puntajes'][user_data['nombre']] += puntos
                        
                        if not pregunta_info['respondido']:
                            sala['pregunta_actual']['respondido'] = True
                            
                            for jugador_nombre, jugador_conn in sala['jugadores'].items():
                                jugador_conn.sendall(json.dumps({"status": "respuesta_correcta", "jugador": user_data['nombre'], "puntos": puntos, "marcador": sala['puntajes']}).encode('utf-8'))
    
    except Exception as e:
        print(f"Error con el cliente {addr}: {e}")
    finally:
        print(f"Desconectado de {addr}")
        if user_data:
            nombre_usuario = user_data['nombre']
            with lock_salas:
                for sala_id, sala in list(salas.items()):
                    if nombre_usuario in sala['jugadores']:
                        del sala['jugadores'][nombre_usuario]
                        del sala['puntajes'][nombre_usuario]
                        if not sala['jugadores']:
                            del salas[sala_id]

def jugar_sala(sala_id):
    with lock_salas:
        sala = salas[sala_id]
        sala['estado'] = 'jugando'
    
    preguntas_disponibles = list(preguntas['general'])
    
    for i in range(sala['num_preguntas']):
        if not preguntas_disponibles:
            break
        
        pregunta_ronda = random.choice(preguntas_disponibles)
        preguntas_disponibles.remove(pregunta_ronda)
        
        timestamp_envio = time.time()
        
        with lock_salas:
            sala['pregunta_actual'] = {'pregunta': pregunta_ronda, 'timestamp_envio': timestamp_envio, 'respondido': False}
        
        for jugador_nombre, jugador_conn in sala['jugadores'].items():
            jugador_conn.sendall(json.dumps({"status": "pregunta", "pregunta": pregunta_ronda, "timestamp_servidor": timestamp_envio, "ronda_actual": i + 1, "rondas_totales": sala['num_preguntas']}).encode('utf-8'))
        
        start_time_ronda = time.time()
        while time.time() - start_time_ronda < 30:
            with lock_salas:
                if sala['pregunta_actual']['respondido']:
                    time.sleep(5) 
                    break
            time.sleep(5)

    with lock_salas:
        if sala['puntajes']:
            ganador_nombre = max(sala['puntajes'], key=sala['puntajes'].get)
            ganador_puntaje = sala['puntajes'][ganador_nombre]
        else:
            ganador_nombre = "Nadie"
            ganador_puntaje = 0
            
        for jugador_nombre, jugador_conn in sala['jugadores'].items():
            jugador_conn.sendall(json.dumps({"status": "fin_juego", "marcador_final": sala['puntajes'], "ganador": ganador_nombre, "ganador_puntos": ganador_puntaje}).encode('utf-8'))

    with lock_ranking:
        for jugador, puntaje in sala['puntajes'].items():
            ranking_global[jugador] = ranking_global.get(jugador, 0) + puntaje
    
    guardar_rankings()
        
def iniciar_servidor():
    cargar_rankings()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Servidor escuchando en {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=manejar_cliente, args=(conn, addr))
            thread.start()

if __name__ == "__main__":
    iniciar_servidor()