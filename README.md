# Flappy Bird em Python

Recriação independente da mecânica de Flappy Bird, com pixel art própria inspirada no visual clássico. Não utiliza imagens ou arquivos do jogo original. Feito com Python e Tkinter, sem dependências externas.

## Jogar no Windows

Abra **Jogar.bat** com um duplo clique.

O inicializador encontra a instalação Python 3.14 deste computador e também aceita o launcher `py`. Para executar manualmente no PowerShell:

```powershell
& 'C:\Users\isaque\AppData\Local\Programs\Python\Python314\python.exe' game.py
```

Requer Python 3.10 ou superior com Tcl/Tk disponível.

## Controles

- **Espaço, seta para cima ou clique:** começar e bater as asas.
- **P ou Esc:** pausar/continuar.
- **R:** voltar à tela inicial.
- **Espaço ou botão Jogar de novo:** reiniciar após a colisão.

O jogo pausa ao perder o foco. O recorde é salvo em `data/record.json`, criado automaticamente no primeiro recorde. Essa pasta não entra no futuro repositório Git.

## Recursos

- Pássaro animado com inclinação durante o voo.
- Canos com alturas aleatórias e colisão circular.
- Cenário em camadas, chão em movimento e placar em pixel art.
- Tela inicial, pausa, resultado, recorde e medalhas (prata aos 10 pontos, ouro aos 20).
- Física baseada no tempo, com passos pequenos para verificar colisões.

Esta primeira versão não inclui áudio.

## Verificação

```powershell
python -m unittest discover -s tests -v
python game.py --smoke-test
```

Se `python` ainda apontar para o atalho da Microsoft Store, use o caminho completo mostrado acima. O teste de interface abre uma janela por alguns instantes e verifica as telas automaticamente, sem alterar o recorde.
