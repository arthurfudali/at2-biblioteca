from datetime import date


def hoje() -> date:
    # Existe só para ser substituída nos testes com mocker.patch: sem ela,
    # testar a multa exigiria esperar o prazo de 14 dias passar de verdade.
    return date.today()
