def normalizar_isbn(texto: str) -> str:
    """Remove hífens e espaços: '978-85-359-0277-8' vira '9788535902778'."""
    return texto.replace("-", "").replace(" ", "")


def isbn13_valido(isbn: str) -> bool:
    """Confere o tamanho e o dígito verificador de um ISBN-13 já normalizado.

    Regra do ISBN-13: os 12 primeiros dígitos são multiplicados, alternadamente,
    por 1 e por 3. O dígito verificador é o que falta para a soma chegar ao
    próximo múltiplo de 10.
    """
    if len(isbn) != 13 or not isbn.isdigit():
        return False

    soma = 0
    for posicao, caractere in enumerate(isbn[:12]):
        peso = 1 if posicao % 2 == 0 else 3
        soma += int(caractere) * peso

    digito_esperado = (10 - soma % 10) % 10
    return int(isbn[12]) == digito_esperado
