# VideoConferência SD

## Descrição
Este projeto implementa um sistema de videoconferência distribuído utilizando a arquitetura peer-to-peer (P2P). Desenvolvido como parte da disciplina **Sistemas Distribuídos**, o sistema permite comunicação em tempo real com troca de mensagens de texto e vídeo entre múltiplos nós na rede.

## Funcionalidades
- Comunicação por texto em tempo real.
- Transmissão de vídeo entre os participantes.
- Conexão dinâmica entre nós sem servidor centralizado.

## Tecnologias Utilizadas
- **Python**: Linguagem principal do projeto.
- **ZeroMQ**: Biblioteca para comunicação entre processos.
- **OpenCV**: Manipulação de vídeo.
- **Threading**: Gerenciamento de tarefas simultâneas.

## Como Executar
1. Certifique-se de ter o Python instalado.
2. Instale as dependências necessárias:
   ```bash
   pip install pyzmq opencv-python numpy
   ```
3. Execute o programa informando a porta desejada:
   ```bash
   python videoconferencia.py <porta>
   ```
4. Utilize os comandos disponíveis:
   - `/connect <porta>`: Conectar a outro nó.
   - `/peers`: Listar nós conectados.
5. Digite mensagens para enviar texto.

## Observação
Este projeto foi desenvolvido para fins acadêmicos e demonstra conceitos de sistemas distribuídos.