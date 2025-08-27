import socket
import threading
import time
import json
import random
import os

HOST = '127.0.0.1'
PORT = 65432

# Base de datos de preguntas del juego.
# Cada pregunta es un diccionario con la pregunta, opciones y la respuesta correcta.
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

# Diccionarios globales para gestionar el estado del juego.
# 'salas' guarda la información de cada partida en curso.
# 'ranking_global' almacena los puntajes de los jugadores a largo plazo.
salas = {}
lock_salas = threading.Lock()  # Bloqueo para proteger el acceso concurrente a las salas
ranking_global = {}
lock_ranking = threading.Lock()  # Bloqueo para proteger el acceso concurrente al ranking global

def guardar_rankings():
    """
    Guarda el ranking global en un archivo JSON para persistir los datos.
    El bloqueo 'lock_ranking' asegura que la escritura sea segura.
    """
    with lock_ranking:
        with open('ranking_global.json', 'w') as f:
            json.dump(ranking_global, f, indent=4)
    print("Rankings guardados.")

def cargar_rankings():
    """
    Carga el ranking global desde el archivo JSON al iniciar el servidor.
    Maneja el caso en que el archivo no exista o esté corrupto.
    """
    global ranking_global
    if os.path.exists('ranking_global.json'):
        try:
            with open('ranking_global.json', 'r') as f:
                ranking_global = json.load(f)
            print("Rankings cargados.")
        except json.JSONDecodeError:
            print("Error al cargar rankings, el archivo puede estar corrupto.")
            ranking_global = {}

def manejar_cliente(conn, addr):
    """
    Función que se ejecuta en un hilo para cada cliente.
    Gestiona la comunicación y las peticiones del cliente (registro, salas, respuestas).
    """
    print(f"Conectado a {addr}")
    user_data = None
    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break
            
            peticion = json.loads(data)
            comando = peticion['comando']
            nombre_usuario = user_data['nombre'] if user_data else "No registrado"

            if comando == "registrar_usuario":
                user_data = {'nombre': peticion['nombre_usuario'], 'conn': conn, 'addr': addr}
                print(f"Usuario {user_data['nombre']} registrado desde {addr}")
                conn.sendall(json.dumps({"status": "ok", "mensaje": f"¡Bienvenido, {user_data['nombre']}!"}).encode('utf-8'))
            
            elif comando == "crear_sala" and user_data:
                modo = int(peticion['modo'])
                num_preguntas = int(peticion['num_preguntas'])
                sala_id = f"sala_{int(time.time())}"
                with lock_salas:
                    salas[sala_id] = {
                        'jugadores': {nombre_usuario: conn},
                        'modo': modo, 'estado': 'esperando',
                        'num_preguntas': num_preguntas,
                        'puntajes': {nombre_usuario: 0}
                    }
                print(f"Sala {sala_id} creada por {nombre_usuario}.")
                conn.sendall(json.dumps({"status": "ok", "mensaje": f"Sala {sala_id} creada. Esperando jugadores...", "sala_id": sala_id}).encode('utf-8'))
                
                # Si el modo es 1 (un jugador), inicia el juego inmediatamente
                if modo == 1:
                    threading.Thread(target=jugar_sala, args=(sala_id,), daemon=True).start()

            elif comando == "unirse_sala" and user_data:
                sala_id = peticion['sala_id']
                with lock_salas:
                    if sala_id in salas and len(salas[sala_id]['jugadores']) < salas[sala_id]['modo']:
                        salas[sala_id]['jugadores'][nombre_usuario] = conn
                        salas[sala_id]['puntajes'][nombre_usuario] = 0
                        print(f"Jugador {nombre_usuario} se unió a la sala {sala_id}")
                        conn.sendall(json.dumps({"status": "ok", "mensaje": f"Te uniste a la sala {sala_id}", "sala_id": sala_id}).encode('utf-8'))
                        # Si la sala alcanza el número de jugadores necesario, inicia el juego
                        if len(salas[sala_id]['jugadores']) == salas[sala_id]['modo']:
                            threading.Thread(target=jugar_sala, args=(sala_id,), daemon=True).start()
                    else:
                        conn.sendall(json.dumps({"status": "error", "mensaje": "Sala no encontrada o está llena."}).encode('utf-8'))

            elif comando == "ver_rankings":
                with lock_ranking:
                    ranking_ordenado = sorted(ranking_global.items(), key=lambda item: item[1], reverse=True)
                    conn.sendall(json.dumps({"status": "ok", "rankings": ranking_ordenado}).encode('utf-8'))
            
            elif comando == "enviar_respuesta" and user_data:
                sala_id = peticion['sala_id']
                with lock_salas:
                    sala = salas.get(sala_id)
                    if not sala or sala.get('estado') != 'jugando':
                        continue
                    
                    # Evita que un jugador responda más de una vez por pregunta
                    if nombre_usuario in sala.get('pregunta_actual', {}).get('respuestas_recibidas', set()):
                        continue
                    
                    sala['pregunta_actual']['respuestas_recibidas'].add(nombre_usuario)
                    
                    pregunta_info = sala['pregunta_actual']
                    if pregunta_info['pregunta']['respuesta'].lower() == peticion['respuesta'].lower():
                        # Solo el primer jugador que responda correctamente gana puntos
                        if not pregunta_info.get('primera_respuesta_correcta', False):
                            sala['pregunta_actual']['primera_respuesta_correcta'] = True
                            # El puntaje depende de la rapidez de la respuesta
                            puntos = max(1, 100 - int((peticion['timestamp'] - pregunta_info['timestamp_envio']) * 10))
                            sala['puntajes'][nombre_usuario] += puntos
                            
                            # Notifica a todos los jugadores de la sala
                            msg = {"status": "respuesta_correcta", "jugador": nombre_usuario, "puntos": puntos, "marcador": sala['puntajes']}
                            for c in sala['jugadores'].values():
                                c.sendall(json.dumps(msg).encode('utf-8'))
    
    except (json.JSONDecodeError, ConnectionResetError, BrokenPipeError) as e:
        print(f"Error o desconexión del cliente {addr}: {e}")
    finally:
        # Lógica de limpieza: elimina al jugador de las salas si se desconecta
        if user_data:
            nombre_usuario = user_data['nombre']
            print(f"Limpiando sesión para {nombre_usuario}.")
            with lock_salas:
                for sala_id, sala in list(salas.items()):
                    if nombre_usuario in sala.get('jugadores', {}):
                        del sala['jugadores'][nombre_usuario]
                        if nombre_usuario in sala.get('puntajes', {}):
                            del sala['puntajes'][nombre_usuario]
                        if not sala['jugadores']:
                            print(f"Sala {sala_id} vacía, eliminando.")
                            del salas[sala_id]

def jugar_sala(sala_id):
    """
    Función que gestiona el juego en una sala específica.
    Se ejecuta en un hilo separado por cada partida.
    """
    with lock_salas:
        if sala_id not in salas: return
        sala = salas[sala_id]
        sala['estado'] = 'jugando'
        num_preguntas = sala['num_preguntas']
        print(f"Iniciando juego en sala {sala_id}")

    # Selecciona preguntas aleatorias para la ronda
    preguntas_ronda = random.sample(preguntas['general'], k=num_preguntas)

    for i, pregunta in enumerate(preguntas_ronda):
        with lock_salas:
            if sala_id not in salas or not salas[sala_id]['jugadores']:
                print(f"Juego en {sala_id} cancelado por falta de jugadores.")
                if sala_id in salas: del salas[sala_id]
                return
            
            sala = salas[sala_id]
            sala['pregunta_actual'] = {
                'pregunta': pregunta, 'timestamp_envio': time.time(),
                'primera_respuesta_correcta': False, 'respuestas_recibidas': set()
            }
            jugadores_actuales = list(sala['jugadores'].values())

        msg_pregunta = json.dumps({"status": "pregunta", "pregunta": pregunta, "ronda_actual": i + 1, "rondas_totales": num_preguntas}).encode('utf-8')
        for conn in jugadores_actuales:
            try:
                conn.sendall(msg_pregunta)
            except socket.error: pass

        # Espera un máximo de 30 segundos para las respuestas
        start_time = time.time()
        tiempo_terminado = True
        while time.time() - start_time < 30:
            with lock_salas:
                if sala_id not in salas: return
                sala = salas[sala_id]
                if len(sala['pregunta_actual']['respuestas_recibidas']) >= len(sala['jugadores']):
                    tiempo_terminado = False
                    break
            time.sleep(0.5)

        # Si el tiempo se acabó, notifica a los jugadores
        if tiempo_terminado:
            print(f"Tiempo agotado en sala {sala_id}, ronda {i+1}.")
            msg_timeout = json.dumps({"status": "tiempo_agotado"}).encode('utf-8')
            for conn in jugadores_actuales:
                try:
                    conn.sendall(msg_timeout)
                except socket.error: pass
        
        # Pausa antes de la siguiente pregunta
        time.sleep(3)

    # Fin del juego
    with lock_salas:
        if sala_id not in salas: return
        sala = salas[sala_id]
        puntajes = sala['puntajes']
        ganador = max(puntajes, key=puntajes.get) if puntajes else "Nadie"
        
        # Envía el resultado final a todos los jugadores
        msg_final = {"status": "fin_juego", "marcador_final": puntajes, "ganador": ganador, "ganador_puntos": puntajes.get(ganador, 0)}
        for conn in sala['jugadores'].values():
            try:
                conn.sendall(json.dumps(msg_final).encode('utf-8'))
            except socket.error: pass
        
        print(f"Juego terminado en sala {sala_id}. Ganador: {ganador}")
        
        # Actualiza el ranking global con los puntajes de la partida
        with lock_ranking:
            for jugador, puntaje in puntajes.items():
                ranking_global[jugador] = ranking_global.get(jugador, 0) + puntaje
        guardar_rankings()

        # Elimina la sala al finalizar el juego
        del salas[sala_id]

def iniciar_servidor():
    """
    Función principal que inicia el servidor.
    Carga los rankings existentes y escucha nuevas conexiones de clientes.
    """
    cargar_rankings()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"Servidor escuchando en {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            # Crea un hilo nuevo para manejar cada cliente de forma concurrente
            threading.Thread(target=manejar_cliente, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    iniciar_servidor()