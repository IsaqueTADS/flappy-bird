# Flappy Bird · 0.2.0

Recriação independente de Flappy Bird com pixel art própria, física baseada no tempo e áudio procedural. O cenário usa Tkinter; o mixer do pygame-ce reproduz a música e os efeitos. Não utiliza imagens, músicas ou efeitos do jogo original.

## Jogar no Windows

O executável é gerado em **dist/FlappyBird.exe**. Ele inclui o Python e as bibliotecas necessárias. A build é para Windows x64 e não abre uma janela de terminal.

**Validação nesta máquina:** a geração do arquivo foi concluída, mas o Windows bloqueou sua execução com a mensagem “Uma política de Controle de Aplicativo bloqueou este arquivo”, inclusive no teste fora do ambiente restrito. A build não tem assinatura digital e ainda não foi validada em execução. Nenhuma política de segurança foi alterada. A versão pelo código-fonte foi testada com sucesso, incluindo a inicialização do dispositivo real de áudio do Windows.

Para jogar pelo código-fonte neste computador, abra **Jogar.bat**. Ele prioriza o ambiente virtual `.venv` e aceita a instalação local do Python como alternativa. Sem a dependência de áudio, o jogo continua funcionando e informa que o áudio está indisponível.

## Controles

| Ação | Controle |
| --- | --- |
| Começar / bater asas | Espaço, seta para cima ou clique |
| Pausar / continuar | P ou Esc |
| Voltar à tela inicial | R |
| Reiniciar após a colisão | Espaço ou botão Jogar de novo |
| Ligar / desligar música | M ou botão MÚSICA |
| Ligar / desligar efeitos | E ou botão EFEITOS |

O jogo pausa ao perder o foco, incluindo o áudio. Música e efeitos têm controles independentes, disponíveis também na pausa e na tela inicial. As preferências são salvas.

## Música e efeitos

`audio.py` sintetiza o áudio diretamente em amostras PCM de 16 bits, a 22050 Hz, sem arquivos sonoros externos:

- Música original de oito compassos com melodia, arpejo, baixo e percussão, em loop.
- Efeitos de bater asas, marcar ponto e colisão, com uma sequência de fim de jogo.
- Envelopes de volume para evitar estalos e canais separados para música e efeitos.
- Reprodução em segundo plano. Uma falha no dispositivo de áudio não impede jogar.

## Recorde e preferências

Os arquivos `record.json` e `settings.json` ficam em **%LOCALAPPDATA%/FlappyBird**, fora do executável e da pasta temporária de extração da build. Isso preserva os dados ao trocar ou atualizar o `.exe`.

O recorde da versão inicial em `data/record.json` é importado automaticamente ao executar o novo código-fonte, preservando o maior valor. Para importar pelo executável, coloque a pasta antiga `data` ao lado do `.exe` na primeira execução. O arquivo antigo permanece intacto.

## Desenvolvimento

Use Python 3.14 x64 com Tcl/Tk no Windows. No PowerShell, dentro desta pasta:

```powershell
& 'C:\Users\isaque\AppData\Local\Programs\Python\Python314\python.exe' -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe game.py
```

`requirements.txt` contém apenas a dependência necessária para jogar com som. `requirements-build.txt` também inclui o PyInstaller.

## Gerar o executável

Abra **GerarBuild.bat**, ou execute:

```powershell
.\.venv\Scripts\python.exe build_windows.py
```

O script executa os testes e gera `dist/FlappyBird.exe` com ícone próprio, metadados de versão e as bibliotecas necessárias. O ícone é criado a partir do sprite do pássaro. `build`, `dist`, arquivos temporários, ambiente virtual e dados locais são ignorados pelo Git.

## Verificação

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe game.py --smoke-test --smoke-report build/source-smoke.json
.\dist\FlappyBird.exe --smoke-test --smoke-report build/exe-smoke.json
```

Os testes cobrem física, colisões, pontuação, síntese de áudio, canais simultâneos, ausência de dispositivo de som, persistência e importação do recorde. O teste de interface abre e fecha o jogo automaticamente, verifica as telas e usa dados temporários, sem alterar o recorde do jogador. O relatório informa se o mixer conseguiu abrir o dispositivo de áudio.

Opções adicionais: `--no-audio` executa sem som e `--data-dir CAMINHO` usa um diretório alternativo para os dados. Ao executar pelo terminal com um caminho que contém espaços, use aspas.
