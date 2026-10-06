"""Como os testes acham arquivos que vivem fora da pasta backend/.

Vários testes de guarda leem arquivos do resto do repositório: a configuração
do Nginx, o docker-compose de produção, as rotas do Angular, a pasta docs/.
Para achá-los, sobem pelas pastas acima de si até encontrar o nome procurado.

O detalhe que custou caro: o Docker monta esses arquivos para dentro de /app,
que é a própria pasta backend/. Ao montar, ele cria no disco um arquivo **vazio**
no lugar, e alguns desses vazios chegaram a ser commitados.

No computador da autora nada aparecia, porque o Docker monta o arquivo de
verdade por cima do vazio. No CI, onde não há montagem, a busca encontrava o
vazio primeiro (ele está mais perto, dentro de backend/) e o teste quebrava com
"NoneType object is not subscriptable", que não diz nada sobre a causa.

O CI ficou vermelho cinco envios seguidos por causa disso.

Daí a regra aqui: arquivo vazio não conta como achado. Se o único candidato for
vazio, é melhor não achar nada (e o teste pular, avisando) do que achar um
arquivo que mente.
"""
from pathlib import Path


def achar(*partes: str) -> Path | None:
    """O primeiro arquivo com este caminho, subindo a partir desta pasta.

    Pula arquivos vazios: eles são restos de montagem do Docker, não conteúdo.
    Devolve None quando não existe nenhum candidato com conteúdo.
    """
    for pasta in Path(__file__).resolve().parents:
        candidato = pasta.joinpath(*partes)
        if candidato.is_file() and candidato.stat().st_size > 0:
            return candidato
    return None


def achar_pasta(*partes: str) -> Path | None:
    """A primeira pasta com este caminho, subindo a partir desta pasta.

    Pula pastas vazias, pelo mesmo motivo: o Docker também cria pasta vazia
    quando monta uma pasta de fora para dentro de backend/.
    """
    for pasta in Path(__file__).resolve().parents:
        candidato = pasta.joinpath(*partes)
        if candidato.is_dir() and any(candidato.iterdir()):
            return candidato
    return None
