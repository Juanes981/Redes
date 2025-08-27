import socket
import json
import time
import os
import threading

HOST = '127.0.0.1'
PORT = 65432

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def menu_principal(s, nombre_usuario):
    while True:
        clear_screen()
        print(f"--- Trivia Asimétrica - Jugador: {nombre_usuario} ---")
        print("1. Crear Sala")
        print("2. Unirse a Sala")
        print("3. Ver Rankings")
        print("4. Salir")
        opcion = input("Elige una opción: ")

        if opcion == '1':
            modo = input("Elige el modo (1 o 2 jugadores): ")
            if modo in ['1', '2']:
                num_preguntas = input("¿Cuántas preguntas (5, 10, 20)? ")
                try:
                    num_preguntas = int(num_preguntas)
                    if num_preguntas not in [5, 10, 20]:
                        print("Número de preguntas no válido.")
                        input("Presiona Enter para continuar...")
                        continue
                    peticion = {"comando": "crear_sala", "modo": int(modo), "num_preguntas": num_preguntas}
                    s.sendall(json.dumps(peticion).encode('utf-8'))
                    respuesta = json.loads(s.recv(1024).decode('utf-8'))
                    print(respuesta['mensaje'])
                    if respuesta['status'] == 'ok':
                        jugar_sala(s, respuesta['sala_id'])
                        
                except (ValueError, json.JSONDecodeError):
                    print("Entrada o respuesta del servidor no válida.")
                    input("Presiona Enter para continuar...")
            else:
                print("Modo no válido.")
                input("Presiona Enter para continuar...")
        elif opcion == '2':
            sala_id = input("Ingresa el ID de la sala: ")
            peticion = {"comando": "unirse_sala", "sala_id": sala_id}
            s.sendall(json.dumps(peticion).encode('utf-8'))
            respuesta = json.loads(s.recv(1024).decode('utf-8'))
            print(respuesta['mensaje'])
            if respuesta['status'] == 'ok':
                jugar_sala(s, respuesta['sala_id'])
            input("Presiona Enter para continuar...")
        elif opcion == '3':
            peticion = {"comando": "ver_rankings"}
            s.sendall(json.dumps(peticion).encode('utf-8'))
            respuesta = json.loads(s.recv(1024).decode('utf-8'))
            clear_screen()
            print("\n--- Rankings Globales ---")
            if respuesta['rankings']:
                for i, (jugador, puntaje) in enumerate(respuesta['rankings']):
                    print(f"{i+1}. {jugador}: {puntaje} puntos")
            else:
                print("No hay rankings disponibles aún.")
            input("Presiona Enter para continuar...")
        elif opcion == '4':
            print("Saliendo...")
            break
        else:
            print("Opción inválida. Inténtalo de nuevo.")
            input("Presiona Enter para continuar...")

def jugar_sala(s, sala_id):
    while True:
        try:
            data = s.recv(2048).decode('utf-8')
            if not data:
                break
            
            mensaje = json.loads(data)
            status = mensaje['status']

            if status == "pregunta":
                pregunta_info = mensaje['pregunta']
                ronda_actual = mensaje['ronda_actual']
                rondas_totales = mensaje['rondas_totales']
                tiempo_limite = 30
                
                # Muestra la pregunta y el temporizador inicial
                clear_screen()
                print(f"Ronda {ronda_actual}/{rondas_totales}")
                print(f"\n Contesta solo con el numero de la Pregunta: {pregunta_info['pregunta']}")
                opciones_texto = "\n".join([f"{i+1}. {op}" for i, op in enumerate(pregunta_info['opciones'])])
                print(opciones_texto)
                print("\n")
                
                # El temporizador solo se muestra una vez al inicio
                print(f"Tienes {tiempo_limite} segundos para responder.")
                print("\n" * 1) 
                
                # Captura la respuesta del usuario
                start_time = time.time()
                respuesta_usuario = input("Tu respuesta: ")
                timestamp_envio_cliente = time.time()
                
                # Calcula el tiempo que tardó el usuario en responder
                tiempo_transcurrido = timestamp_envio_cliente - start_time
                if tiempo_transcurrido > tiempo_limite:
                    respuesta_usuario = "" # Si se excede el tiempo, se envía una respuesta vacía
                    
                peticion = {
                    "comando": "enviar_respuesta",
                    "sala_id": sala_id,
                    "respuesta": respuesta_usuario,
                    "timestamp": timestamp_envio_cliente
                }
                s.sendall(json.dumps(peticion).encode('utf-8'))

            elif status == "respuesta_correcta":
                print(f"¡Respuesta correcta! Jugador {mensaje['jugador']} ganó {mensaje['puntos']} puntos.")
                print("Marcador actual:", mensaje['marcador'])
                time.sleep(5)
            
            elif status == "fin_juego":
                clear_screen()
                print("\n--- Fin del juego ---")
                print("Marcador final:", mensaje['marcador_final'])
                print(f"¡El ganador es {mensaje['ganador']} con {mensaje['ganador_puntos']} puntos!")
                input("Presiona Enter para volver al menú principal...")
                break
            
            elif status == "error":
                print("Error del servidor:", mensaje['mensaje'])
                input("Presiona Enter para volver al menú principal...")
                break

        except (socket.error, json.JSONDecodeError) as e:
            print(f"Error de conexión: {e}")
            break

if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            nombre_usuario = input("Ingresa tu nombre de usuario: ")
            peticion = {"comando": "registrar_usuario", "nombre_usuario": nombre_usuario}
            s.sendall(json.dumps(peticion).encode('utf-8'))
            respuesta = json.loads(s.recv(1024).decode('utf-8'))
            print(respuesta['mensaje'])
            if respuesta['status'] == "ok":
                menu_principal(s, nombre_usuario)
            else:
                print("No se pudo registrar el usuario.")
        except ConnectionRefusedError:
            print("No se pudo conectar al servidor. Asegúrate de que está en ejecución.")