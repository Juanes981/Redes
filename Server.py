import socket
import threading
import cv2
import time
import os
from moviepy import VideoFileClip
import wave

VIDEO_FOLDER = 'videos'
HOST = '192.168.1.65'
VIDEO_PORT = 5000
AUDIO_PORT = 5001
CHUNK_SIZE = 1024

def get_video_list():
    if not os.path.exists(VIDEO_FOLDER): os.makedirs(VIDEO_FOLDER)
    return [f for f in os.listdir(VIDEO_FOLDER) if f.endswith('.mp4')]

def send_video(client_socket, video_path, stop_event):
    videoCapture = cv2.VideoCapture(video_path)
    if not videoCapture.isOpened(): return

    fps = videoCapture.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 30
    intervalo = 1 / fps

    print(f"Transmitiendo video: {os.path.basename(video_path)}")
    while not stop_event.is_set():
        ret, frame = videoCapture.read()
        if not ret: break

        frame_reducido = cv2.resize(frame, (0, 0), fx=0.75, fy=0.75)
        
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
        _, buffer = cv2.imencode('.jpg', frame_reducido, encode_param)
        data = buffer.tobytes()
        
        try:
            client_socket.sendall(len(data).to_bytes(4, byteorder='big'))
            client_socket.sendall(data)
        except:
            stop_event.set()
            break
        time.sleep(intervalo)
    
    videoCapture.release()
    if not stop_event.is_set():
        try:
            client_socket.sendall((0).to_bytes(4, byteorder='big'))
        except: pass
    print("Transmisión de video finalizada.")

def send_audio(client_socket, audio_path, stop_event):
    wf = wave.open(audio_path, 'rb')
    print(f"Transmitiendo audio: {os.path.basename(audio_path)}")
    while not stop_event.is_set():
        data = wf.readframes(CHUNK_SIZE)
        if not data: break
        try:
            client_socket.sendall(data)
        except:
            stop_event.set()
            break
    print("Transmisión de audio finalizada.")
    client_socket.close()

def handle_client(video_conn, addr):
    print(f"Cliente {addr} conectado al puerto de video.")
    video_list = get_video_list()
    video_sender_thread, audio_sender_thread = None, None
    stop_event = threading.Event()

    try:
        menu_str = "MENU\n" + "\n".join(f"{i+1}. {name}" for i, name in enumerate(video_list))
        video_conn.sendall(menu_str.encode('utf-8'))

        while True:
            command_data = video_conn.recv(1024)
            if not command_data: break
            command = command_data.decode('utf-8').strip().upper()
            print(f"Comando de {addr}: '{command}'")

            if video_sender_thread and video_sender_thread.is_alive():
                stop_event.set()
                video_sender_thread.join()
                audio_sender_thread.join()
            stop_event.clear()

            if command.startswith('PLAY'):
                try:
                    video_index = int(command.split()[1]) - 1
                    if 0 <= video_index < len(video_list):
                        video_path = os.path.join(VIDEO_FOLDER, video_list[video_index])
                        audio_path = f"temp_{addr[1]}.wav"
                        
                        print(f"Extrayendo audio de {video_list[video_index]}...")
                        video_clip = VideoFileClip(video_path)
                        video_clip.audio.write_audiofile(audio_path, codec='pcm_s16le')
                        
                        video_conn.sendall(b'START_STREAM')
                        
                        audio_conn, _ = audio_server_socket.accept()
                        
                        video_sender_thread = threading.Thread(target=send_video, args=(video_conn, video_path, stop_event))
                        audio_sender_thread = threading.Thread(target=send_audio, args=(audio_conn, audio_path, stop_event))
                        
                        video_sender_thread.start()
                        audio_sender_thread.start()
                    else:
                        raise IndexError
                except (IndexError, ValueError):
                    video_conn.sendall("ERROR\nÍndice inválido".encode('utf-8'))
                    video_conn.sendall(menu_str.encode('utf-8'))

            elif command == 'STOP':
                 video_conn.sendall(menu_str.encode('utf-8'))
            elif command == 'EXIT':
                break
    finally:
        stop_event.set()
        if video_sender_thread and video_sender_thread.is_alive(): video_sender_thread.join()
        if audio_sender_thread and audio_sender_thread.is_alive(): audio_sender_thread.join()
        video_conn.close()
        print(f"Sesión con {addr} terminada.")

def main():
    global audio_server_socket
    video_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    video_server_socket.bind((HOST, VIDEO_PORT))
    video_server_socket.listen(5)

    audio_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    audio_server_socket.bind((HOST, AUDIO_PORT))
    audio_server_socket.listen(5)
    
    print(f"Conectado en {HOST} esperando conexión del usuario...")
    while True:
        video_conn, addr = video_server_socket.accept()
        threading.Thread(target=handle_client, args=(video_conn, addr)).start()

if __name__ == '__main__':
    main()