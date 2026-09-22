r"""Analisador léxico Spotify para a atividade da faculdade.

Tabela de tokens documentada

| TOKEN | Descrição | Regex | Exemplo | Prioridade |
| --- | --- | --- | --- | --- |
| PLAYLIST | Comando para iniciar/definir a playlist | /playlist\b/i | PLAYLIST "Treino" | 5 |
| ADICIONAR | Adiciona música à playlist | /adicionar\b/i | ADICIONAR "Believer" | 5 |
| REMOVER | Remove uma faixa da playlist | /remover\b/i | REMOVER "Believer" | 5 |
| REPRODUZIR | Inicia reprodução da faixa | /reproduzir\b/i | REPRODUZIR "Believer" | 5 |
| PAUSAR | Pausa a reprodução | /pausar\b/i | PAUSAR | 5 |
| TOCAR | Inicia ou continua a reprodução | /tocar\b/i | TOCAR | 5 |
| DURACAO | Palavra-chave de duração | /duracao\b/i | DURACAO 03:20 | 5 |
| GENERO | Palavra-chave de gênero musical | /genero\b/i | GENERO pop | 5 |
| ORDENAR | Palavra-chave de ordenação | /ordenar\b/i | ORDENAR popularidade | 5 |
| ARTISTA | Palavra-chave de artista | /artista\b/i | ARTISTA "Imagine Dragons" | 5 |
| ALBUM | Palavra-chave de álbum | /album\b/i | ALBUM "Evolve" | 5 |
| ALEATORIO | Palavra-chave de reprodução aleatória | /aleatorio\b/i | ALEATORIO | 5 |
| CRITERIO_ORDENACAO | Critério de ordenação do domínio | /\b(popularidade|artista|genero|duracao|aleatorio)\b/i | popularidade | 4 |
| TEXTO | String literal entre aspas | /"[^"\n]*"/ | "Treino" | 3 |
| DURACAO_VALOR | Duração em formato MM:SS | /\d{2}:\d{2}/ | 03:20 | 3 |
| NUMERO | Número inteiro | /\d+/ | 42 | 2 |
| IDENTIFICADOR | Palavra genérica do domínio | /\b[a-zA-Z_][a-zA-Z0-9_]*\b/ | rock | 1 |

Diário de Ambiguidade

Durante a implementação, surgiu um conflito real entre CRITERIO_ORDENACAO e IDENTIFICADOR.
A expressão "popularidade" poderia ser aceita por um identificador genérico, mas ela também era
um critério de ordenação do domínio Spotify. O token genérico era mais amplo e o token específico
era mais restritivo; como o aluno precisa resolver isso com prioridade, o critério específico recebeu
prioridade maior. Isso elimina o conflito porque a palavra "popularidade" é tratada como um
valor de domínio e não como um identificador livre. O resultado é estável e coerente com o conteúdo
esperado do problema.
"""

from __future__ import annotations

import html
from typing import List, Dict, Any

from lark import Lark
from lark.exceptions import UnexpectedCharacters

# ---------------------------------------------------------------------------
# Conflito real de prioridade
# ---------------------------------------------------------------------------
# O token mais genérico e mais amplo é IDENTIFICADOR, que aceita qualquer
# palavra iniciada por letra. O token CRITERIO_ORDENACAO é mais específico,
# porque apenas reconhece palavras válidas do domínio Spotify, como
# popularidade, artista, genero, duracao e aleatorio.
#
# Exemplo: na entrada ORDENAR popularidade, "popularidade" poderia ser
# reconhecida tanto por IDENTIFICADOR quanto por CRITERIO_ORDENACAO.
# O Lark escolhe o token com maior prioridade (número menor = menos prioritário
# para a regra interna do lexer em "basic" em conjunto com a ordem de definição).
# Assim, CRITERIO_ORDENACAO recebe prioridade maior e ganha antes do
# IDENTIFICADOR genérico. Isso é o mesmo tipo de conflito tratado no PDF:
# um padrão geral pode começar exatamente no mesmo lugar do padrão específico.
# Nosso ajuste é usar prioridade explícita na regra específica e deixar o token
# genérico em nível inferior.
# ---------------------------------------------------------------------------

TABELA_TOKENS = [
    {"TOKEN": "PLAYLIST", "DESCRICAO": "Comando para iniciar ou definir a playlist", "REGEX": "/playlist\\b/i", "EXEMPLO": "PLAYLIST \"Treino\"", "PRIORIDADE": 5},
    {"TOKEN": "ADICIONAR", "DESCRICAO": "Comando para adicionar música", "REGEX": "/adicionar\\b/i", "EXEMPLO": "ADICIONAR \"Believer\"", "PRIORIDADE": 5},
    {"TOKEN": "REMOVER", "DESCRICAO": "Comando para remover faixa", "REGEX": "/remover\\b/i", "EXEMPLO": "REMOVER \"Believer\"", "PRIORIDADE": 5},
    {"TOKEN": "REPRODUZIR", "DESCRICAO": "Comando para tocar uma faixa", "REGEX": "/reproduzir\\b/i", "EXEMPLO": "REPRODUZIR \"Believer\"", "PRIORIDADE": 5},
    {"TOKEN": "PAUSAR", "DESCRICAO": "Comando para pausar a reprodução", "REGEX": "/pausar\\b/i", "EXEMPLO": "PAUSAR", "PRIORIDADE": 5},
    {"TOKEN": "TOCAR", "DESCRICAO": "Comando para tocar", "REGEX": "/tocar\\b/i", "EXEMPLO": "TOCAR", "PRIORIDADE": 5},
    {"TOKEN": "DURACAO", "DESCRICAO": "Palavra-chave de duração", "REGEX": "/duracao\\b/i", "EXEMPLO": "DURACAO 03:20", "PRIORIDADE": 5},
    {"TOKEN": "GENERO", "DESCRICAO": "Palavra-chave de gênero musical", "REGEX": "/genero\\b/i", "EXEMPLO": "GENERO rock", "PRIORIDADE": 5},
    {"TOKEN": "ORDENAR", "DESCRICAO": "Palavra-chave de ordenação", "REGEX": "/ordenar\\b/i", "EXEMPLO": "ORDENAR popularidade", "PRIORIDADE": 5},
    {"TOKEN": "ARTISTA", "DESCRICAO": "Palavra-chave de artista", "REGEX": "/artista\\b/i", "EXEMPLO": "ARTISTA \"Imagine Dragons\"", "PRIORIDADE": 5},
    {"TOKEN": "ALBUM", "DESCRICAO": "Palavra-chave de álbum", "REGEX": "/album\\b/i", "EXEMPLO": "ALBUM \"Evolve\"", "PRIORIDADE": 5},
    {"TOKEN": "ALEATORIO", "DESCRICAO": "Palavra-chave de reprodução aleatória", "REGEX": "/aleatorio\\b/i", "EXEMPLO": "ALEATORIO", "PRIORIDADE": 5},
    {"TOKEN": "CRITERIO_ORDENACAO", "DESCRICAO": "Critério válido de ordenação do domínio", "REGEX": "/\\b(popularidade|artista|genero|duracao|aleatorio)\\b/i", "EXEMPLO": "popularidade", "PRIORIDADE": 4},
    {"TOKEN": "TEXTO", "DESCRICAO": "Literal contendo texto entre aspas", "REGEX": "/\"[^\"\\n]*\"/", "EXEMPLO": "\"Treino\"", "PRIORIDADE": 3},
    {"TOKEN": "DURACAO_VALOR", "DESCRICAO": "Valor de duração em MM:SS", "REGEX": "/\\d{2}:\\d{2}/", "EXEMPLO": "03:20", "PRIORIDADE": 3},
    {"TOKEN": "NUMERO", "DESCRICAO": "Valor numérico genérico", "REGEX": "/\\d+/", "EXEMPLO": "42", "PRIORIDADE": 2},
    {"TOKEN": "IDENTIFICADOR", "DESCRICAO": "Palavra genérica para nomes e valores livres", "REGEX": "/\\b[a-zA-Z_][a-zA-Z0-9_]*\\b/", "EXEMPLO": "rock", "PRIORIDADE": 1},
]

GRAMATICA_DESAFIO = r'''
    start: item*
    item: token

    ?token: PLAYLIST
         | ADICIONAR
         | REMOVER
         | REPRODUZIR
         | PAUSAR
         | TOCAR
         | DURACAO
         | GENERO
         | ORDENAR
         | ARTISTA
         | ALBUM
         | ALEATORIO
         | TEXTO
         | DURACAO_VALOR
         | NUMERO
         | CRITERIO_ORDENACAO
         | IDENTIFICADOR

    PLAYLIST.5: /playlist\b/i
    ADICIONAR.5: /adicionar\b/i
    REMOVER.5: /remover\b/i
    REPRODUZIR.5: /reproduzir\b/i
    PAUSAR.5: /pausar\b/i
    TOCAR.5: /tocar\b/i
    DURACAO.5: /duracao\b/i
    GENERO.5: /genero\b/i
    ORDENAR.5: /ordenar\b/i
    ARTISTA.5: /artista\b/i
    ALBUM.5: /album\b/i
    ALEATORIO.5: /aleatorio\b/i

    CRITERIO_ORDENACAO.4: /\b(popularidade|artista|genero|duracao|aleatorio)\b/i
    TEXTO.3: /"[^"\n]*"/
    DURACAO_VALOR.3: /\d{2}:\d{2}/
    NUMERO.2: /\d+/
    IDENTIFICADOR.1: /\b[a-zA-Z_][a-zA-Z0-9_]*\b/

    COMENTARIO: /#[^\n]*/
    %ignore /[ \t\r\n]+/
    %ignore COMENTARIO
'''

lexer_desafio = Lark(GRAMATICA_DESAFIO, parser="lalr", lexer="basic")

CORES = {
    "PLAYLIST": "#1565c0",
    "ADICIONAR": "#1565c0",
    "REMOVER": "#1565c0",
    "REPRODUZIR": "#1565c0",
    "PAUSAR": "#1565c0",
    "TOCAR": "#1565c0",
    "DURACAO": "#1565c0",
    "GENERO": "#1565c0",
    "ORDENAR": "#1565c0",
    "ARTISTA": "#1565c0",
    "ALBUM": "#1565c0",
    "ALEATORIO": "#1565c0",
    "CRITERIO_ORDENACAO": "#7b1fa2",
    "TEXTO": "#ef6c00",
    "DURACAO_VALOR": "#2e7d32",
    "NUMERO": "#00838f",
    "IDENTIFICADOR": "#546e7a",
}


class LexicalError(Exception):
    def __init__(self, line: int, column: int, char: str, dica: str):
        self.line = line
        self.column = column
        self.char = char
        self.dica = dica
        super().__init__(
            f"Linha {line}, coluna {column}: caractere inesperado '{char}'. Dica: {dica}"
        )


def _dica_lexica(char: str) -> str:
    if char in {"@", "."}:
        return "Verifique se o texto ou a chave do domínio está em formato válido. Em Spotify, nomes de músicas e playlists devem estar entre aspas."
    if char == ":":
        return "Use o formato MM:SS para duração, por exemplo 03:45."
    if char in {'"', "'"}:
        return "Nomes de playlists, músicas e artistas precisam estar entre aspas."
    if char in {"$", "#"}:
        return "Esse caractere não é esperado neste domínio. Revise comandos como PLAYLIST, ADICIONAR e GENERO."
    return "Confira o comando e os valores esperados: PLAYLIST, ADICIONAR, DURACAO, GENERO, ORDENAR, REMOVER ou REPRODUZIR."


def _token_para_dict(token: Any) -> Dict[str, Any]:
    return {
        "type": token.type,
        "value": token.value,
        "line": getattr(token, "line", 1),
        "column": getattr(token, "column", 1),
        "start_pos": getattr(token, "start_pos", 0),
        "end_pos": getattr(token, "end_pos", 0),
    }


def tokenizar_desafio(texto: str) -> List[Dict[str, Any]]:
    try:
        tokens = []
        for token in lexer_desafio.lex(texto):
            tokens.append(_token_para_dict(token))
        return tokens
    except UnexpectedCharacters as exc:
        char = exc.char if getattr(exc, "char", None) is not None else "\n"
        line = getattr(exc, "line", 1)
        column = getattr(exc, "column", 1)
        dica = _dica_lexica(char)
        raise LexicalError(line, column, char, dica) from exc


def cor_do_token(tipo: str) -> str:
    return CORES.get(tipo, "#455a64")


def tabela_tokens_html(tokens: List[Dict[str, Any]], titulo: str = "Tabela de Tokens") -> str:
    linhas = [
        "<h3 style='margin: 0 0 12px 0; color: #1f2937;'>%s</h3>" % html.escape(titulo),
        "<table style='border-collapse: collapse; width: 100%; font-family: sans-serif; font-size: 13px;'>",
        "<thead><tr style='background:#eef2ff; color:#111827;'><th style='border:1px solid #d1d5db; padding:8px;'>#</th><th style='border:1px solid #d1d5db; padding:8px;'>TOKEN</th><th style='border:1px solid #d1d5db; padding:8px;'>LEXEMA</th><th style='border:1px solid #d1d5db; padding:8px;'>LINHA</th><th style='border:1px solid #d1d5db; padding:8px;'>COLUNA</th></tr></thead>",
        "<tbody>"
    ]

    for i, token in enumerate(tokens, start=1):
        cor = cor_do_token(str(token["type"]))
        linhas.append(
            "<tr>"
            f"<td style='border:1px solid #d1d5db; padding:8px;'>{i}</td>"
            f"<td style='border:1px solid #d1d5db; padding:8px; color:{cor}; font-weight:600;'>{html.escape(str(token['type']))}</td>"
            f"<td style='border:1px solid #d1d5db; padding:8px;'>{html.escape(str(token['value']))}</td>"
            f"<td style='border:1px solid #d1d5db; padding:8px;'>{token['line']}</td>"
            f"<td style='border:1px solid #d1d5db; padding:8px;'>{token['column']}</td>"
            "</tr>"
        )

    linhas.append("</tbody></table>")
    return "".join(linhas)


def texto_colorido_html(texto: str, tokens: List[Dict[str, Any]]) -> str:
    if not texto:
        return "<p style='color: #6b7280;'>Nenhum texto informado.</p>"

    partes = []
    ultimo = 0
    for token in sorted(tokens, key=lambda t: t["start_pos"]):
        inicio = token["start_pos"]
        fim = token["end_pos"]
        if inicio > ultimo:
            partes.append(html.escape(texto[ultimo:inicio]))
        if inicio < fim:
            cor = cor_do_token(str(token["type"]))
            partes.append(
                f"<span style='background: {cor}; color: white; border-radius: 4px; padding: 1px 4px; font-weight: 600;'>"
                f"{html.escape(texto[inicio:fim])}</span>"
            )
        ultimo = fim

    if ultimo < len(texto):
        partes.append(html.escape(texto[ultimo:]))

    return "<pre style='background:#f8fafc; border:1px solid #e5e7eb; border-radius:8px; padding:12px; white-space:pre-wrap; word-break:break-word;'>" + "".join(partes) + "</pre>"


def erro_lexico_html(texto: str, line: int, column: int, char: str, dica: str) -> str:
    linhas = texto.splitlines() or [""]
    if 1 <= line <= len(linhas):
        linha_texto = linhas[line - 1]
    else:
        linha_texto = ""

    marker = " " * max(0, column - 1) + "^"
    return (
        "<div style='font-family: sans-serif; background:#fff1f2; border:1px solid #fecdd3; border-radius:8px; padding:12px; color:#7f1d1d;'>"
        "<strong>Erro léxico</strong><br>"
        f"Linha: {line} &nbsp; | &nbsp; Coluna: {column}<br>"
        f"Caractere: {html.escape(char)}<br>"
        f"Dica: {html.escape(dica)}<br><br>"
        f"<pre style='margin:0; white-space:pre-wrap;'>{html.escape(linha_texto)}</pre>"
        f"<pre style='margin:0; color:#b91c1c;'>{html.escape(marker)}</pre>"
        "</div>"
    )


def interface_lexer():
    import ipywidgets as widgets
    from IPython.display import display

    exemplos = {
        "Playlist básica": '''PLAYLIST "Treino"
ADICIONAR "Believer"
ARTISTA "Imagine Dragons"
DURACAO 03:24
GENERO rock
ORDENAR popularidade''',
        "Playlist com remover": '''PLAYLIST "Roadtrip"
ADICIONAR "Bohemian Rhapsody"
DURACAO 05:55
GENERO classic
REMOVER "Bohemian Rhapsody"
ORDENAR artista''',
        "Playlist de música pop": '''PLAYLIST "Noite"
ADICIONAR "Blinding Lights"
ARTISTA "The Weeknd"
DURACAO 03:20
GENERO pop
REPRODUZIR "Blinding Lights"''',
        "Caso inválido": '''PLAYLIST "Treino"
DURACAO 3:4
GENERO @rock''',
    }

    dropdown = widgets.Dropdown(options=list(exemplos.keys()), value="Playlist básica", description="Exemplo:")
    entrada = widgets.Textarea(value=exemplos[dropdown.value], layout=widgets.Layout(width="100%", height="220px"))
    botao = widgets.Button(description="Analisar")
    tabela = widgets.HTML(value="")
    destaque = widgets.HTML(value="")
    erro = widgets.HTML(value="")
    output = widgets.VBox([dropdown, entrada, botao, erro, destaque, tabela])

    def atualizar_exemplo(change):
        entrada.value = exemplos[change["new"]]

    def analisar(_):
        texto = entrada.value
        tabela.value = ""
        destaque.value = ""
        erro.value = ""
        try:
            tokens = tokenizar_desafio(texto)
            destaque.value = texto_colorido_html(texto, tokens)
            tabela.value = tabela_tokens_html(tokens)
        except LexicalError as exc:
            erro.value = erro_lexico_html(texto, exc.line, exc.column, exc.char, exc.dica)
        except Exception as exc:  # pragma: no cover
            erro.value = f"<div style='color:#7f1d1d;'><strong>Erro:</strong> {html.escape(str(exc))}</div>"

    dropdown.observe(atualizar_exemplo, names="value")
    botao.on_click(analisar)
    analisar(None)
    return output


if __name__ == "__main__":
    import ipywidgets as widgets
    from IPython.display import display

    display(interface_lexer())
