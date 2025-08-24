import socket
import threading
import cv2
import numpy as np

def handle_client(client_socket, videoCapture):
    while True:
        try:
            ret, frame = videoCapture.read()
            if not ret:
                break

            _, buffer = cv2.imencode('.jpg', frame)
            data = buffer.tobytes()
            
            # Enviar el tamaño de la imagen (4 bytes en formato big-endian)
            client_socket.sendall(len(data).to_bytes(4, byteorder='big'))
            
            # Enviar los datos de la imagen
            client_socket.sendall(data)

        except Exception as e:
            print(f"Client Disconnected: {e}")
            client_socket.close()
            break

def show(videoCapture):
    while True:
        ret, frame = videoCapture.read()
        if ret:
            cv2.imshow('Frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cv2.destroyAllWindows()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 5000))
    server.listen(5)
    print("Server started, waiting for connection...")

    videoCapture = cv2.VideoCapture(0)

    show_camera = threading.Thread(target=show, args=(videoCapture,))
    show_camera.start()

    while True:
        client_socket, addr = server.accept()
        print(f"Connection from {addr} has been established!")
        client_handler = threading.Thread(target=handle_client, args=(client_socket, videoCapture))
        client_handler.start()

if __name__ == '__main__':
    main()
