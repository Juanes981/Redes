import socket
import threading
import cv2
import time
import os
from moviepy import VideoFileClip
import wave

# Define las constantes para la configuración del servidor y la gestión de archivos
VIDEO_FOLDER = 'videos'  # Carpeta donde se guardan los archivos de video
HOST = '10.21.49.46'      # Dirección IP del servidor
VIDEO_PORT = 5000        # Puerto para la comunicación de datos de video
AUDIO_PORT = 5001        # Puerto para la comunicación de datos de audio
CHUNK_SIZE = 1024        # Tamaño de los fragmentos de datos de audio a enviar

def get_video_list():
    """
    Obtiene una lista de los archivos de video MP4 de la carpeta especificada.
    Crea la carpeta si no existe.
    """
    if not os.path.exists(VIDEO_FOLDER):
        os.makedirs(VIDEO_FOLDER)
    return [f for f in os.listdir(VIDEO_FOLDER) if f.endswith('.mp4')]

def send_video(client_socket, video_path, stop_event):
    """
    Transmite los fotogramas de video a un cliente a través de un socket.
    - Lee los fotogramas del video usando OpenCV.
    - Redimensiona y codifica cada fotograma como una imagen JPEG para reducir el tamaño de los datos.
    - Envía primero el tamaño de los datos del fotograma (4 bytes), seguido de los datos del fotograma en sí.
    - Utiliza un 'stop_event' para detener la transmisión de forma segura.
    """
    videoCapture = cv2.VideoCapture(video_path)
    if not videoCapture.isOpened():
        print(f"Error: No se pudo abrir el archivo de video en {video_path}")
        return

    # Obtiene las propiedades del video para calcular el retraso entre fotogramas
    fps = videoCapture.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 30  # Valor por defecto si no se encuentra el FPS
    intervalo = 1 / fps  # Tiempo de espera entre fotogramas para mantener la velocidad original

    print(f"Transmitiendo video: {os.path.basename(video_path)}")
    while not stop_event.is_set():
        ret, frame = videoCapture.read()
        if not ret:
            break  # Fin del archivo de video

        # Redimensiona el fotograma al 75% de su tamaño original para reducir la carga de la red
        frame_reducido = cv2.resize(frame, (0, 0), fx=0.75, fy=0.75)
        
        # Codifica el fotograma como una imagen JPEG con una calidad del 60%
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
        _, buffer = cv2.imencode('.jpg', frame_reducido, encode_param)
        data = buffer.tobytes()
        
        try:
            # Envía el tamaño de los datos del fotograma y luego los datos
            client_socket.sendall(len(data).to_bytes(4, byteorder='big'))
            client_socket.sendall(data)
        except:
            # Si el envío falla, se asume que el cliente se desconectó y se detiene el stream
            stop_event.set()
            break
        
        # Pausa por el intervalo calculado para mantener el FPS original del video
        time.sleep(intervalo)
    
    videoCapture.release()
    # Señala el final de la transmisión de video enviando un fotograma de tamaño cero
    if not stop_event.is_set():
        try:
            client_socket.sendall((0).to_bytes(4, byteorder='big'))
        except:
            pass
    print("Transmisión de video finalizada.")

def send_audio(client_socket, audio_path, stop_event):
    """
    Transmite los datos de audio de un archivo WAV a un cliente.
    - Lee los datos de audio en fragmentos.
    - Envía cada fragmento a través del socket.
    - Utiliza un 'stop_event' para detener la transmisión de forma segura.
    """
    try:
        wf = wave.open(audio_path, 'rb')
    except wave.Error as e:
        print(f"Error al abrir el archivo de audio: {e}")
        stop_event.set()
        return

    print(f"Transmitiendo audio: {os.path.basename(audio_path)}")
    while not stop_event.is_set():
        data = wf.readframes(CHUNK_SIZE)
        if not data:
            break  # Fin del archivo de audio
        
        try:
            client_socket.sendall(data)
        except:
            # Si el envío falla, se asume que el cliente se desconectó
            stop_event.set()
            break
    
    wf.close()
    print("Transmisión de audio finalizada.")
    try:
        client_socket.close()
    except:
        pass

def handle_client(video_conn, addr):
    """
    Maneja una conexión de cliente individual.
    - Gestiona todo el ciclo de interacción con el cliente.
    - Envía un menú de videos disponibles.
    - Espera los comandos 'PLAY', 'STOP' o 'EXIT'.
    - Extrae el audio del video seleccionado y lanza hilos separados para la transmisión de video y audio.
    """
    print(f"Cliente {addr} conectado al puerto de video.")
    video_list = get_video_list()
    video_sender_thread, audio_sender_thread = None, None
    stop_event = threading.Event()  # Evento para señalar a los hilos que se detengan

    try:
        # Prepara y envía el menú de videos al cliente
        menu_str = "MENU\n" + "\n".join(f"{i+1}. {name}" for i, name in enumerate(video_list))
        video_conn.sendall(menu_str.encode('utf-8'))

        while True:
            # Espera un comando del cliente
            command_data = video_conn.recv(1024)
            if not command_data:
                break  # Cliente desconectado
            
            command = command_data.decode('utf-8').strip().upper()
            print(f"Comando de {addr}: '{command}'")

            # Si ya hay una transmisión activa, la detiene antes de iniciar una nueva
            if video_sender_thread and video_sender_thread.is_alive():
                stop_event.set()  # Señala a los hilos para que paren
                video_sender_thread.join()
                audio_sender_thread.join()
            
            stop_event.clear()  # Limpia el evento de parada para la siguiente transmisión

            if command.startswith('PLAY'):
                try:
                    video_index = int(command.split()[1]) - 1
                    if 0 <= video_index < len(video_list):
                        video_path = os.path.join(VIDEO_FOLDER, video_list[video_index])
                        audio_path = f"temp_{addr[1]}.wav"
                        
                        # Usa moviepy para extraer el audio del archivo de video
                        print(f"Extrayendo audio de {video_list[video_index]}...")
                        video_clip = VideoFileClip(video_path)
                        video_clip.audio.write_audiofile(audio_path, codec='pcm_s16le')
                        
                        video_conn.sendall(b'START_STREAM')  # Informa al cliente que se prepare para el stream
                        
                        # Espera a que el cliente se conecte al puerto de audio
                        audio_conn, _ = audio_server_socket.accept()
                        
                        # Inicia hilos separados para la transmisión de video y audio
                        video_sender_thread = threading.Thread(target=send_video, args=(video_conn, video_path, stop_event))
                        audio_sender_thread = threading.Thread(target=send_audio, args=(audio_conn, audio_path, stop_event))
                        
                        video_sender_thread.start()
                        audio_sender_thread.start()
                    else:
                        raise IndexError
                except (IndexError, ValueError):
                    # Maneja comandos 'PLAY' inválidos
                    video_conn.sendall("ERROR\nÍndice inválido".encode('utf-8'))
                    video_conn.sendall(menu_str.encode('utf-8'))
            
            elif command == 'STOP':
                # El comando 'STOP' ya es manejado al principio del bucle, así que solo reenvía el menú
                video_conn.sendall(menu_str.encode('utf-8'))
            
            elif command == 'EXIT':
                break  # Sale del bucle para cerrar la conexión

    finally:
        # Limpia los recursos cuando el cliente se desconecta o ocurre un error
        stop_event.set()
        if video_sender_thread and video_sender_thread.is_alive():
            video_sender_thread.join()
        if audio_sender_thread and audio_sender_thread.is_alive():
            audio_sender_thread.join()
        
        video_conn.close()
        print(f"Sesión con {addr} terminada.")
        
        # Elimina el archivo de audio temporal
        audio_path = f"temp_{addr[1]}.wav"
        if os.path.exists(audio_path):
            os.remove(audio_path)

def main():
    """
    Función principal para iniciar y ejecutar el servidor.
    - Crea y enlaza dos sockets: uno para video y otro para audio.
    - Entra en un bucle infinito para aceptar nuevas conexiones de clientes.
    - Inicia un nuevo hilo para cada cliente para manejar sus solicitudes.
    """
    global audio_server_socket
    
    # Crea y configura el socket del servidor de video
    video_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    video_server_socket.bind((HOST, VIDEO_PORT))
    video_server_socket.listen(5)

    # Crea y configura el socket del servidor de audio
    audio_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    audio_server_socket.bind((HOST, AUDIO_PORT))
    audio_server_socket.listen(5)
    
    print(f"Conectado en {HOST} esperando conexión del usuario...")
    
    # Bucle principal para aceptar nuevas conexiones
    while True:
        video_conn, addr = video_server_socket.accept()
        # Inicia un nuevo hilo para manejar la conexión de video del cliente
        threading.Thread(target=handle_client, args=(video_conn, addr)).start()

if __name__ == '__main__':
    main()