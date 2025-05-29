# VideoConferência SD

## Membros

 - Gabriel Andreazi Bertho, 790780
 - Lucas de Oliveira Rodrigues Alves, 811943
 - Jonas Gabriel dos Santos Costa Fagundes, 790901

## Descrição

Este projeto implementa um sistema de videoconferência distribuído utilizando a arquitetura peer-to-peer (P2P). Desenvolvido como parte da disciplina **Sistemas Distribuídos**, o sistema permite comunicação em tempo real com troca de mensagens de texto, vídeo e áudio entre múltiplos nós na rede.

## Funcionalidades

- Comunicação por texto em tempo real
- Transmissão de vídeo ponto a ponto
- Transmissão de áudio ponto a ponto
- Conexão automática bilateral entre nós sem servidor centralizado
- Suporte a múltiplos peers simultâneos

## Tecnologias Utilizadas

- **Python**: Linguagem principal do projeto
- **ZeroMQ (pyzmq)**: Biblioteca para comunicação assíncrona
- **OpenCV**: Captura e exibição de vídeo
- **SoundDevice**: Captura e reprodução de áudio
- **Threading**: Execução concorrente

## Clonando o Repositório

Clone este repositório em sua máquina local com o comando:

```bash
git clone https://github.com/Lusquiinha/videoconferenciaSD.git
cd videoconferenciaSD
```

## Como Executar

1. **Crie um ambiente virtual (opcional, mas recomendado)**

```bash
python -m venv venv
source venv/bin/activate     # Linux/macOS
venv\Scripts\activate.bat  # Windows
```

2. **Instale as dependências**

```bash
pip install -r requirements.txt
```

3. **Execute o programa em dois terminais diferentes, ou em duas máquinas distintas (Linux e/ou Windows):**

```bash
python main.py <porta>
```

> Exemplo:
>
> Em um terminal (usuário 1):
> ```bash
> python main.py 5000
> ```
>
> Em outro terminal (usuário 2):
> ```bash
> python main.py 5001
> ```

4. **Conecte os peers**

No terminal do primeiro usuário, digite:

```bash
/connect <ip_do_segundo_usuario> <porta>
```

Exemplo:

```bash
/connect 192.168.1.100 5001
```

O outro nó será automaticamente conectado de volta.

## Comandos Disponíveis

- `/connect <ip> <porta>`: Conectar a outro peer
- `/peers`: Listar peers conectados
- Digite qualquer texto e pressione Enter para enviar uma mensagem

## Requisitos

- Python 3.8 ou superior
- Webcam e microfone funcionando
- Sistema operacional compatível com ZeroMQ e sounddevice

