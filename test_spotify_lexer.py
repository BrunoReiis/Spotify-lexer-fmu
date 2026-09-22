from spotify_lexer import tokenizar_desafio

VALIDOS = [
    '''
    PLAYLIST "Treino"
    ADICIONAR "Blinding Lights"
    ARTISTA "The Weeknd"
    DURACAO 03:20
    GENERO pop
    ORDENAR popularidade
    ''',
    '''
    PLAYLIST "Roadtrip"
    ADICIONAR "Believer"
    ARTISTA "Imagine Dragons"
    DURACAO 03:24
    GENERO rock
    REPRODUZIR "Believer"
    ''',
    '''
    PLAYLIST "MIX"
    ADICIONAR "Bohemian Rhapsody"
    DURACAO 05:55
    GENERO classic
    REMOVER "Bohemian Rhapsody"
    ORDENAR artista
    '''
]

INVALIDOS = [
    'PLAYLIST "Treino\nADICIONAR "Blinding Lights"\nDURACAO 3:4',
    'PLAYLIST "Treino"\nGENERO @rock',
]

for idx, texto in enumerate(VALIDOS, 1):
    toks = tokenizar_desafio(texto)
    assert toks, f'Caso válido {idx} não gerou tokens'
    assert any(t['type'] == 'PLAYLIST' for t in toks), f'Caso válido {idx} não contém PLAYLIST'

for idx, texto in enumerate(INVALIDOS, 1):
    try:
        tokenizar_desafio(texto)
    except Exception:
        pass
    else:
        raise AssertionError(f'Caso inválido {idx} deveria falhar')

print('testes ok')
