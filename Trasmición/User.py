import socket
import cv2
import numpy as np
import pyaudio
import threading

# Constantes de conexión y configuración
HOST = '10.21.49.46'      # Dirección IP del servidor
VIDEO_PORT = 5000        # Puerto para el flujo de video
AUDIO_PORT = 5001        # Puerto para el flujo de audio
CHUNK = 1024             # Tamaño del fragmento de audio
WINDOW_NAME = 'Video'    # Nombre de la ventana de visualización de video

def recvall(sock, n):
    """
    Función auxiliar para asegurar la recepción de 'n' bytes completos desde un socket.
    Evita que los datos se reciban de forma parcial.
    """
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None  # Retorna None si la conexión se cierra
        data += packet
    return data

def receive_audio(stop_event):
    """
    Maneja la recepción y reproducción del flujo de audio en un hilo separado.
    - Se conecta al puerto de audio del servidor.
    - Utiliza PyAudio para reproducir los fragmentos de audio recibidos.
    - El 'stop_event' detiene la reproducción cuando el video termina o el usuario lo solicita.
    """
    audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        audio_socket.connect((HOST, AUDIO_PORT))
        p = pyaudio.PyAudio()
        # Abre un stream de audio con la misma configuración que el servidor
        stream = p.open(format=pyaudio.paInt16, channels=2, rate=44100, output=True, frames_per_buffer=CHUNK)
        
        while not stop_event.is_set():
            data = audio_socket.recv(CHUNK)
            if not data:
                break  # Fin de la transmisión de audio
            stream.write(data)
    except Exception as e:
        print(f"Error en el hilo de audio: {e}")
    finally:
        # Cierra los recursos de audio de forma segura
        if 'stream' in locals() and stream.is_active():
            stream.stop_stream()
            stream.close()
        if 'p' in locals():
            p.terminate()
        audio_socket.close()

def watch_video(video_socket):
    """
    Gestiona la recepción y visualización del flujo de video.
    - Inicia un hilo para la reproducción de audio.
    - Muestra los fotogramas de video recibidos en una ventana de OpenCV.
    - Detecta las pulsaciones de teclas ('m' para menú, 'q' para salir).
    - El bucle termina cuando el video se completa, se presiona una tecla o la conexión se pierde.
    """
    stop_event = threading.Event()
    audio_thread = threading.Thread(target=receive_audio, args=(stop_event,))
    audio_thread.start()
    
    return_status = 'menu'
    
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    
    print("Iniciando video.")
    print("Presiona 'm' para ir al menú o 'q' para desconectarte.")
    try:
        while True:
            # Recibe el tamaño del fotograma (4 bytes)
            size_data = recvall(video_socket, 4)
            if not size_data:
                return_status = 'exit'
                break
            
            size = int.from_bytes(size_data, byteorder='big')
            
            # Si el tamaño es 0, significa que el servidor ha terminado de enviar el video
            if size == 0:
                print("El video ha terminado.")
                video_socket.sendall(b'STOP') 
                return_status = 'menu'
                break

            # Recibe los datos completos del fotograma
            image_data = recvall(video_socket, size)
            if not image_data:
                return_status = 'exit'
                break
                
            # Decodifica la imagen JPEG en un fotograma de OpenCV
            frame = cv2.imdecode(np.frombuffer(image_data, dtype=np.uint8), cv2.IMREAD_COLOR)

            if frame is not None:
                # Muestra el fotograma en la ventana
                cv2.imshow(WINDOW_NAME, frame)
                # Espera 1ms y captura las pulsaciones de teclas
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    video_socket.sendall(b'EXIT')
                    return_status = 'exit'
                    break
                elif key == ord('m'):
                    video_socket.sendall(b'STOP')
                    return_status = 'menu'
                    break
    finally:
        # Asegura que el hilo de audio se detenga y se cierre la ventana de OpenCV
        stop_event.set()
        audio_thread.join()
        if cv2.getWindowProperty(WINDOW_NAME, 0) >= 0:
            cv2.destroyWindow(WINDOW_NAME)

    return return_status

def main():
    """
    Función principal para gestionar la conexión y la interacción con el usuario.
    - Se conecta al socket de video del servidor.
    - Maneja el menú de videos y los comandos del usuario.
    - Llama a `watch_video` cuando se inicia una transmisión.
    """
    video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        video_socket.connect((HOST, VIDEO_PORT))
        print("Conectado al servidor")
    except Exception as e:
        print(f"Error al conectar: {e}")
        return

    while True:
        try:
            # Recibe la respuesta del servidor (menú, error, o inicio de stream)
            response = video_socket.recv(4096).decode('utf-8')
            if not response:
                print("El servidor cerró la conexión.")
                break

            if response.startswith("MENU"):
                print("\n--- Menú de Videos ---")
                print(response[5:])
                choice = input("Elige un video o escribe 'q' para desconectarte: ")
                if choice.lower() == 'q':
                    video_socket.sendall(b'EXIT')
                    break
                video_socket.sendall(f'PLAY {choice}'.encode('utf-8'))
            
            elif response.startswith("START_STREAM"):
                # Si el servidor indica que el stream va a empezar, llama a la función para ver el video
                result = watch_video(video_socket)
                if result == 'exit':
                    break
            
            elif response.startswith("ERROR"):
                print(f"Error del servidor: {response}")
        except ConnectionResetError:
            print("Se ha perdido la conexión con el servidor.")
            break

    video_socket.close()
    cv2.destroyAllWindows() 
    print("Desconectado.")

if __name__ == '__main__':
    main()