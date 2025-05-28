import zmq
import threading
import time
import sys
import re
import cv2
import numpy as np
from collections import deque

class MediaChatNode:
    def __init__(self, my_port):
        self.my_port = my_port
        self.peers = set()
        self.running = True
        
        # Configurações de mídia
        self.video_capture = cv2.VideoCapture(0)
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        self.video_capture.set(cv2.CAP_PROP_FPS, 15)
        
        self.audio_settings = {
            'channels': 1,
            'rate': 44100,
            'blocksize': 1024,
            'dtype': 'float32'
        }
        
        # Contexto ZeroMQ
        self.context = zmq.Context()
        
        # Sockets para texto
        self.text_pub = self.context.socket(zmq.PUB)
        self.text_pub.bind(f"tcp://*:{my_port}")
        
        self.text_sub = self.context.socket(zmq.SUB)
        self.text_sub.setsockopt_string(zmq.SUBSCRIBE, "")
        
        # Sockets para vídeo (PUSH/PULL)
        self.video_pub = self.context.socket(zmq.PUSH)
        self.video_pub.bind(f"tcp://*:{my_port + 1}")
        
        self.video_sub = self.context.socket(zmq.PULL)

        # Sockets para controle
        self.control_socket = self.context.socket(zmq.REP)
        self.control_socket.bind(f"tcp://*:{my_port + 2}")
        
        # Buffer para frames de vídeo
        self.video_buffer = deque(maxlen=10)
        
        # Threads
        self.threads = [
            threading.Thread(target=self.receive_text),
            threading.Thread(target=self.receive_video),
            threading.Thread(target=self.handle_control),
            threading.Thread(target=self.capture_video),
            threading.Thread(target=self.display_media)
        ]
        
        for t in self.threads:
            t.daemon = True
            t.start()
    
    def add_peer(self, peer_port):
        if peer_port not in self.peers and peer_port != self.my_port:
            try:
                # Conecta todos os sockets ao peer
                self.text_sub.connect(f"tcp://localhost:{peer_port}")
                self.video_sub.connect(f"tcp://localhost:{peer_port + 1}")
                
                # Envia solicitação de conexão
                control_socket = self.context.socket(zmq.REQ)
                control_socket.connect(f"tcp://localhost:{peer_port + 2}")
                control_socket.send_string(f"CONNECT {self.my_port}")
                
                response = control_socket.recv_string()
                control_socket.close()
                
                if response == "OK":
                    self.peers.add(peer_port)
                    print(f"Conexão estabelecida com {peer_port}")
                    return True
                else:
                    print(f"Falha na conexão com {peer_port}")
                    return False
            except Exception as e:
                print(f"Erro ao conectar com {peer_port}: {e}")
                return False
        else:
            print(f"Já conectado ou tentando conectar a si mesmo (porta {peer_port})")
            return False
    
    def handle_control(self):
        while self.running:
            try:
                if self.control_socket.poll(100):
                    msg = self.control_socket.recv_string()
                    if msg.startswith("CONNECT"):
                        _, port = msg.split()
                        port = int(port)
                        
                        # Aceita a conexão
                        self.text_sub.connect(f"tcp://localhost:{port}")
                        self.video_sub.connect(f"tcp://localhost:{port + 1}")
                        
                        self.peers.add(port)
                        self.control_socket.send_string("OK")
            except zmq.ZMQError as e:
                if self.running:
                    print(f"Erro no socket de controle: {e}")
                break
    
    def capture_video(self):
        while self.running and self.video_capture.isOpened():
            ret, frame = self.video_capture.read()
            if ret:
                # Comprime o frame (apenas vídeo ainda usa compressão)
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                
                # Envia para todos os peers
                for peer in self.peers:
                    try:
                        self.video_pub.send(buffer.tobytes(), zmq.NOBLOCK)
                    except zmq.ZMQError:
                        continue
    
    def receive_text(self):
        while self.running:
            try:
                msg = self.text_sub.recv_string(zmq.NOBLOCK)
                print(f"\n[TEXTO] {msg}\nVocê: ", end="", flush=True)
            except zmq.Again:
                time.sleep(0.1)
            except zmq.ZMQError as e:
                if self.running:
                    print(f"Erro ao receber texto: {e}")
                break
    
    def receive_video(self):
        while self.running:
            try:
                frame_data = self.video_sub.recv(zmq.NOBLOCK)
                frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    self.video_buffer.append(frame)
            except zmq.Again:
                time.sleep(0.01)
            except Exception as e:
                if self.running:
                    print(f"Erro ao receber vídeo: {e}")
                continue
    
    def display_media(self):
        while self.running:
            if self.video_buffer:
                frame = self.video_buffer[-1]
                cv2.imshow('Video Recebido', frame)
            
            key = cv2.waitKey(1)
            if key == 27:  # ESC
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
        self.control_socket.close()
        self.context.term()

def parse_connect_command(cmd):
    match = re.match(r'^/connect\s+(\d+)$', cmd)
    if not match:
        return None
    return 'localhost', int(match.group(1))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python media_chat.py <porta>")
        sys.exit(1)
    
    my_port = int(sys.argv[1])
    node = MediaChatNode(my_port)
    
    try:
        print(f"Chat de mídia rodando na porta {my_port}")
        print("Comandos disponíveis:")
        print("/connect <porta> - Conectar a outro nó")
        print("/peers - Listar peers conectados")
        print("Digite mensagens de texto (Ctrl+C para sair):")
        
        while node.running:
            user_input = input("Você: ")
            
            if user_input.startswith('/connect'):
                result = parse_connect_command(user_input)
                if result:
                    ip, port = result
                    if ip == 'localhost':
                        node.add_peer(port)
                else:
                    print("Formato inválido. Use: /connect <porta>")
            
            elif user_input == '/peers':
                print("Peers conectados:", ", ".join(map(str, node.peers)))
            
            elif user_input.startswith('/'):
                print("Comando desconhecido")
            
            else:
                node.send_text(user_input)
                
    except KeyboardInterrupt:
        print("\nSaindo...")
    finally:
        node.stop()