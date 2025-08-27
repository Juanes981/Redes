import socket
import json
import time
import os
import threading
import sys

# Constantes de conexión para el cliente.
HOST = '127.0.0.1'
PORT = 65432

# threading.Event se utiliza como una bandera global para controlar el flujo de los hilos.
# Si `juego_en_curso` está activo (set), los hilos de juego continúan.
# Si está inactivo (clear), se detienen.
juego_en_curso = threading.Event()

def clear_screen():
    """
    Función de utilidad para limpiar la pantalla de la consola.
    Detecta el sistema operativo y usa el comando apropiado.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

def manejar_input(s, sala_id):
    """
    Hilo dedicado a leer la entrada del usuario para las respuestas del juego.
    
    Esta función se ejecuta en un hilo separado para que el cliente pueda
    leer del teclado y, al mismo tiempo, recibir mensajes del servidor
    sin bloquearse. Utiliza `sys.stdin.readline()` porque permite
    una gestión más limpia de la entrada en un hilo que `input()`.
    """
    while juego_en_curso.is_set():
        try:
            # Lee una línea de la entrada estándar y elimina espacios en blanco.
            respuesta_usuario = sys.stdin.readline().strip()
            # Si el juego sigue activo y se ha ingresado una respuesta, la envía.
            if juego_en_curso.is_set() and respuesta_usuario:
                peticion = {
                    "comando": "enviar_respuesta",
                    "sala_id": sala_id,
                    "respuesta": respuesta_usuario,
                    "timestamp": time.time()  # Envía el momento exacto para calcular la puntuación por velocidad
                }
                s.sendall(json.dumps(peticion).encode('utf-8'))
        except (IOError, ValueError):
            # Si se produce un error de E/S, el juego ha terminado.
            break
    
def jugar_sala(s, sala_id):
    """
    Gestiona el ciclo de vida de una partida de juego.
    
    Esta función se encarga de recibir los mensajes del servidor, como
    nuevas preguntas, resultados de respuestas y el fin del juego.
    """
    # Activa la bandera global para indicar que el juego está en curso.
    juego_en_curso.set()
    
    # Inicia el hilo secundario para manejar la entrada del usuario.
    input_thread = threading.Thread(target=manejar_input, args=(s, sala_id), daemon=True)
    input_thread.start()

    while juego_en_curso.is_set():
        try:
            # Recibe datos del servidor.
            data = s.recv(2048).decode('utf-8')
            if not data:
                print("\nConexión perdida con el servidor.")
                break

            # El servidor puede enviar varios mensajes en un solo paquete,
            # por lo que se dividen y procesan individualmente.
            mensajes = data.strip().split('\n')
            for msg_str in mensajes:
                if not msg_str: continue
                mensaje = json.loads(msg_str)
                status = mensaje.get('status')

                if status == "pregunta":
                    # Muestra una nueva pregunta del servidor.
                    clear_screen()
                    pregunta_info = mensaje['pregunta']
                    print(f"--- Ronda {mensaje['ronda_actual']}/{mensaje['rondas_totales']} ---")
                    print(f"\nPregunta: {pregunta_info['pregunta']}")
                    print("\n".join([f"{i+1}. {op}" for i, op in enumerate(pregunta_info['opciones'])]))
                    print("\nTu respuesta (número): ", end='', flush=True)

                elif status == "respuesta_correcta":
                    # Muestra la confirmación de una respuesta correcta y el marcador.
                    print(f"\n\n¡Correcto! {mensaje['jugador']} gana {mensaje['puntos']} puntos.")
                    print(f"Marcador: {mensaje['marcador']}")
                    time.sleep(2) # Pausa para que el usuario pueda leer el mensaje

                elif status == "tiempo_agotado":
                    # Mensaje de tiempo agotado para la pregunta actual.
                    print("\n\n¡Se acabó el tiempo para esta pregunta!")
                    time.sleep(2)

                elif status == "fin_juego":
                    # Muestra el marcador final y el ganador al terminar la partida.
                    clear_screen()
                    print("\n--- ¡Fin del juego! ---")
                    print("Marcador final:", mensaje['marcador_final'])
                    print(f"El ganador es {mensaje['ganador']} con {mensaje['ganador_puntos']} puntos.")
                    input("\nPresiona Enter para volver al menú principal...")
                    juego_en_curso.clear() # Desactiva la bandera, deteniendo el hilo de entrada y el bucle.
                    return # Sale de la función para volver al menú.

                elif status == "error":
                    # Muestra un mensaje de error del servidor.
                    print(f"\nError del servidor: {mensaje['mensaje']}")
                    input("Presiona Enter para continuar...")
                    juego_en_curso.clear()
                    return

        except (socket.error, json.JSONDecodeError, ConnectionAbortedError) as e:
            print(f"\nError de conexión durante el juego: {e}")
            juego_en_curso.clear()
            break

def menu_principal(s, nombre_usuario):
    """
    Presenta el menú principal al usuario y maneja las opciones seleccionadas.
    Permite crear una sala, unirse a una, ver rankings o salir del juego.
    """
    while True:
        # No muestra el menú si el juego está activo, solo espera su fin.
        if juego_en_curso.is_set():
            time.sleep(1)
            continue
            
        clear_screen()
        print(f"--- Trivia Asimétrica - Jugador: {nombre_usuario} ---")
        print("1. Crear Sala")
        print("2. Unirse a Sala")
        print("3. Ver Rankings")
        print("4. Salir")
        opcion = input("Elige una opción: ")

        try:
            if opcion == '1':
                modo = input("Elige el modo (1 o 2 jugadores): ")
                num_preguntas = input("¿Cuántas preguntas (5, 10, 20)? ")
                if modo in ['1', '2'] and num_preguntas in ['5', '10', '20']:
                    peticion = {"comando": "crear_sala", "modo": modo, "num_preguntas": num_preguntas}
                    s.sendall(json.dumps(peticion).encode('utf-8'))
                    respuesta = json.loads(s.recv(1024).decode('utf-8'))
                    print(respuesta['mensaje'])
                    if respuesta['status'] == 'ok':
                        jugar_sala(s, respuesta['sala_id'])
                else:
                    print("Valores no válidos.")
                    input("Presiona Enter...")

            elif opcion == '2':
                sala_id = input("Ingresa el ID de la sala: ")
                peticion = {"comando": "unirse_sala", "sala_id": sala_id}
                s.sendall(json.dumps(peticion).encode('utf-8'))
                respuesta = json.loads(s.recv(1024).decode('utf-8'))
                print(respuesta['mensaje'])
                if respuesta['status'] == 'ok':
                    jugar_sala(s, respuesta['sala_id'])
                else:
                    input("Presiona Enter para continuar...")

            elif opcion == '3':
                peticion = {"comando": "ver_rankings"}
                s.sendall(json.dumps(peticion).encode('utf-8'))
                respuesta = json.loads(s.recv(1024).decode('utf-8'))
                clear_screen()
                print("\n--- Rankings Globales ---")
                if respuesta.get('rankings'):
                    for i, (jugador, puntaje) in enumerate(respuesta['rankings']):
                        print(f"{i+1}. {jugador}: {puntaje} puntos")
                else:
                    print("No hay rankings disponibles.")
                input("\nPresiona Enter para continuar...")

            elif opcion == '4':
                print("Saliendo...")
                break
        except (socket.error, json.JSONDecodeError):
            print("Error de comunicación con el servidor. Volviendo al menú.")
            return

if __name__ == "__main__":
    """Punto de entrada principal del script."""
    # Crea un socket y se conecta al servidor.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            # Pide el nombre de usuario y lo registra en el servidor.
            nombre_usuario = input("Ingresa tu nombre de usuario: ")
            peticion = {"comando": "registrar_usuario", "nombre_usuario": nombre_usuario}
            s.sendall(json.dumps(peticion).encode('utf-8'))
            respuesta = json.loads(s.recv(1024).decode('utf-8'))
            print(respuesta['mensaje'])
            if respuesta['status'] == "ok":
                # Si el registro es exitoso, muestra el menú principal.
                menu_principal(s, nombre_usuario)
        except (ConnectionRefusedError, ConnectionResetError):
            print("No se pudo conectar al servidor. Asegúrate de que está en ejecución.")
        except KeyboardInterrupt:
            print("\nCerrando cliente.")
        finally:
            # Cierra el socket al terminar, asegurando la limpieza de recursos.
            s.close()