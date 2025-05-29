import zmq
import threading
import time
import sys
import re
import cv2
import numpy as np
import socket
from collections import deque
import sounddevice as sd

class MediaChatNode:
    def __init__(self, my_port):
        self.my_port = my_port
        self.peers = set()
        self.running = True

        self.video_capture = cv2.VideoCapture(0)
        if not self.video_capture.isOpened():
            print("[ERRO] Câmera não foi acessada corretamente.")
        else:
            print("Câmera acessada com sucesso")

        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        self.video_capture.set(cv2.CAP_PROP_FPS, 15)

        self.context = zmq.Context()

        self.text_pub = self.context.socket(zmq.PUB)
        self.text_pub.bind(f"tcp://*:{my_port}")

        self.text_sub = self.context.socket(zmq.SUB)
        self.text_sub.setsockopt_string(zmq.SUBSCRIBE, "")

        self.video_pub = self.context.socket(zmq.PUSH)
        self.video_pub.bind(f"tcp://*:{my_port + 1}")

        self.video_sub = self.context.socket(zmq.PULL)

        self.audio_pub = self.context.socket(zmq.PUSH)
        self.audio_pub.bind(f"tcp://*:{my_port + 3}")

        self.audio_sub = self.context.socket(zmq.PULL)

        self.control_socket = self.context.socket(zmq.REP)
        self.control_socket.bind(f"tcp://*:{my_port + 2}")

        self.video_buffer = deque(maxlen=10)
        self.audio_buffer = deque(maxlen=10)

        self.threads = [
            threading.Thread(target=self.receive_text),
            threading.Thread(target=self.receive_video),
            threading.Thread(target=self.receive_audio),
            threading.Thread(target=self.handle_control),
            threading.Thread(target=self.capture_video),
            threading.Thread(target=self.capture_audio),
            threading.Thread(target=self.display_media)
        ]

        for t in self.threads:
            t.daemon = True
            t.start()

    def add_peer(self, peer_ip, peer_port):
        if (peer_ip, peer_port) not in self.peers and peer_port != self.my_port:
            try:
                self.text_sub.connect(f"tcp://{peer_ip}:{peer_port}")
                self.video_sub.connect(f"tcp://{peer_ip}:{peer_port + 1}")
                self.audio_sub.connect(f"tcp://{peer_ip}:{peer_port + 3}")

                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                my_ip = s.getsockname()[0]
                s.close()

                control_socket = self.context.socket(zmq.REQ)
                control_socket.connect(f"tcp://{peer_ip}:{peer_port + 2}")
                control_socket.send_string(f"CONNECT {self.my_port} {my_ip}")

                response = control_socket.recv_string()
                control_socket.close()

                if response == "OK":
                    self.peers.add((peer_ip, peer_port))
                    print(f"Conexão estabelecida com {peer_ip}:{peer_port}")
                    return True
                else:
                    print(f"Falha na conexão com {peer_ip}:{peer_port}")
                    return False
            except Exception as e:
                print(f"Erro ao conectar com {peer_ip}:{peer_port} - {e}")
                return False
        else:
            print(f"Já conectado ou tentando conectar a si mesmo ({peer_ip}:{peer_port})")
            return False

    def handle_control(self):
        while self.running:
            try:
                if self.control_socket.poll(100):
                    msg = self.control_socket.recv_string()
                    if msg.startswith("CONNECT"):
                        _, port, sender_ip = msg.split()
                        port = int(port)
                        print(f"Conectando automaticamente de volta a {sender_ip}:{port}...")
                        threading.Thread(target=self.add_peer, args=(sender_ip, port), daemon=True).start()
                        self.control_socket.send_string("OK")
            except zmq.ZMQError as e:
                if self.running:
                    print(f"Erro no socket de controle: {e}")
                break

    def capture_video(self):
        if self.video_capture.isOpened():
            print("Iniciando envio de vídeo...")
        while self.running and self.video_capture.isOpened():
            ret, frame = self.video_capture.read()
            if ret:
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                for peer_ip, peer_port in self.peers:
                    try:
                        self.video_pub.send(buffer.tobytes(), zmq.NOBLOCK)
                    except zmq.ZMQError:
                        continue

    def capture_audio(self):
        def callback(indata, frames, time_info, status):
            if status and str(status) != 'input overflow':
                print(f"[AUDIO STATUS] {status}")
            try:
                self.audio_pub.send(indata.tobytes(), zmq.NOBLOCK)
            except zmq.ZMQError:
                pass

        with sd.InputStream(samplerate=44100, channels=1, dtype='int16',
                            callback=callback, blocksize=1024, latency='low'):
            while self.running:
                pass

    def receive_audio(self):
        def callback(outdata, frames, time_info, status):
            if self.audio_buffer:
                outdata[:] = self.audio_buffer.popleft()
            else:
                outdata.fill(0)

        with sd.OutputStream(samplerate=44100, channels=1, dtype='int16',
                             callback=callback, blocksize=1024, latency='low'):
            while self.running:
                try:
                    audio_data = self.audio_sub.recv(zmq.NOBLOCK)
                    self.audio_buffer.append(np.frombuffer(audio_data, dtype='int16').reshape(-1, 1))
                except zmq.Again:
                    time.sleep(0.005)

    def receive_text(self):
        while self.running:
            try:
                msg = self.text_sub.recv_string(zmq.NOBLOCK)
                print(f"\n[TEXTO] {msg}\nVocê: ", end="", flush=True)
            except zmq.Again:
                time.sleep(0.1)

    def receive_video(self):
        while self.running:
            try:
                frame_data = self.video_sub.recv(zmq.NOBLOCK)
                frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    self.video_buffer.append(frame)
            except zmq.Again:
                time.sleep(0.01)

    def display_media(self):
        while self.running:
            if self.video_buffer:
                frame = self.video_buffer[-1]
                cv2.imshow('Video Recebido', frame)

            key = cv2.waitKey(1)
            if key == 27:
                self.running = False

    def send_text(self, message):
        full_message = f"[{self.my_port}]: {message}"
        self.text_pub.send_string(full_message)

    def stop(self):
        self.running = False
        for t in self.threads:
            t.join(timeout=1)
        self.video_capture.release()
        cv2.destroyAllWindows()
        self.text_pub.close()
        self.text_sub.close()
        self.video_pub.close()
        self.video_sub.close()
        self.audio_pub.close()
        self.audio_sub.close()
        self.control_socket.close()
        self.context.term()


def parse_connect_command(cmd):
    match = re.match(r'^/connect\s+(\S+)\s+(\d+)$', cmd)
    if not match:
        return None
    return match.group(1), int(match.group(2))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python main.py <porta>")
        sys.exit(1)

    my_port = int(sys.argv[1])
    node = MediaChatNode(my_port)

    try:
        print(f"Chat de mídia rodando na porta {my_port}")
        print("Comandos disponíveis:")
        print("/connect <ip> <porta> - Conectar a outro nó")
        print("/peers - Listar peers conectados")
        print("Digite mensagens de texto (Ctrl+C para sair):")

        while node.running:
            user_input = input("Você: ")

            if user_input.startswith('/connect'):
                result = parse_connect_command(user_input)
                if result:
                    ip, port = result
                    node.add_peer(ip, port)
                else:
                    print("Formato inválido. Use: /connect <ip> <porta>")

            elif user_input == '/peers':
                print("Peers conectados:", ", ".join(f"{ip}:{port}" for ip, port in node.peers))

            elif user_input.startswith('/'):
                print("Comando desconhecido")

            else:
                node.send_text(user_input)

    except KeyboardInterrupt:
        print("\nSaindo...")
    finally:
        node.stop()
