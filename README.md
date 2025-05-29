# VideoConferência SD

## Descrição

Este projeto implementa um sistema de videoconferência **peer-to-peer (P2P)** com **comunicação em tempo real por texto, vídeo e áudio**, utilizando **ZeroMQ**, **OpenCV** e **SoundDevice**. Foi desenvolvido como parte da disciplina **Sistemas Distribuídos**.

## Funcionalidades

- Envio e recebimento de mensagens de texto entre múltiplos nós
- Transmissão de vídeo em tempo real via webcam
- Transmissão de áudio em tempo real com reprodução nos peers
- Conexão dinâmica e mútua entre nós, sem servidor central

## Tecnologias Utilizadas

- Python 3
- ZeroMQ – Comunicação entre processos
- OpenCV – Captura e exibição de vídeo
- SoundDevice – Captura e reprodução de áudio
- Threading – Execução concorrente das tarefas
- NumPy – Processamento de sinais

## Requisitos

Crie um ambiente virtual e instale as dependências:

```bash
python -m venv venv
source venv/bin/activate     # Linux/macOS
venv\Scripts\activate.bat  # Windows

pip install -r requirements.txt
```

**Arquivo `requirements.txt`:**

```
pyzmq
opencv-python
numpy
sounddevice
```

## Como Executar

1. No terminal de cada máquina (ou em duas abas diferentes para testes locais), execute:

    python main.py <porta>

    Exemplo:

    python main.py 5000

2. No terminal interativo do programa, use os comandos disponíveis:

    - Para conectar a outro peer:

        /connect <ip> <porta>

    - Para listar os peers conectados:

        /peers

    - Para enviar mensagem de texto:

        Basta digitar e pressionar Enter.

**Nota:** Ao conectar a outro peer, o sistema estabelece automaticamente uma conexão recíproca (ex: peer A conecta a B → B conecta de volta a A).

## Teste Local (em uma só máquina)

Abra dois terminais:

    # Terminal 1
    python main.py 5000

    # Terminal 2
    python main.py 5001

No terminal 2:

    /connect 127.0.0.1 5000

## Observações

- O sistema foi testado em Linux e Windows.
- Para melhor qualidade de áudio, recomenda-se usar fones de ouvido com microfone.
- O áudio pode apresentar artefatos se o buffer estiver sobrecarregado. Isso será ajustado em versões futuras.
