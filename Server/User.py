import socket
import cv2
import numpy as np
import pyaudio
import threading

HOST = '127.0.0.1'
VIDEO_PORT = 5000
AUDIO_PORT = 5001
CHUNK = 1024

def recvall(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet: return None
        data += packet
    return data

def receive_audio(stop_event):
    audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    audio_socket.connect((HOST, AUDIO_PORT))
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=2, rate=44100, output=True, frames_per_buffer=CHUNK)
    
    while not stop_event.is_set():
        try:
            data = audio_socket.recv(CHUNK)
            if not data: break
            stream.write(data)
        except:
            break
    stream.stop_stream()
    stream.close()
    p.terminate()
    audio_socket.close()

def watch_video(video_socket):
    stop_event = threading.Event()
    audio_thread = threading.Thread(target=receive_audio, args=(stop_event,))
    audio_thread.start()
    
    print("Iniciando video... 'm' para menú, 'q' para salir.")
    while True:
        size_data = recvall(video_socket, 4)
        if not size_data: break
        size = int.from_bytes(size_data, byteorder='big')
        if size == 0:
            print("Video terminado.")
            break

        image_data = recvall(video_socket, size)
        if not image_data: break
        frame = cv2.imdecode(np.frombuffer(image_data, dtype=np.uint8), cv2.IMREAD_COLOR)

        if frame is not None:
            cv2.imshow('Video con Audio', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                video_socket.sendall(b'EXIT')
                stop_event.set()
                return 'exit'
            elif key == ord('m'):
                video_socket.sendall(b'STOP')
                stop_event.set()
                return 'menu'
                
    stop_event.set()
    audio_thread.join()
    return 'menu'

def main():
    video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        video_socket.connect((HOST, VIDEO_PORT))
        print("Conectado al servidor.")
    except Exception as e:
        print(f"Error al conectar: {e}")
        return

    while True:
        response = video_socket.recv(4096).decode('utf-8')
        if response.startswith("MENU"):
            print("\n--- Menú de Videos ---")
            print(response[5:])
            choice = input("Elige un video o escribe 'exit': ")
            if choice.lower() == 'exit':
                video_socket.sendall(b'EXIT')
                break
            video_socket.sendall(f'PLAY {choice}'.encode('utf-8'))
        
        elif response.startswith("START_STREAM"):
            result = watch_video(video_socket)
            if result == 'exit':
                break
        
        elif response.startswith("ERROR"):
            print(f"Error del servidor: {response}")

    video_socket.close()
    cv2.destroyAllWindows()
    print("Desconectado.")

if __name__ == '__main__':
    main()