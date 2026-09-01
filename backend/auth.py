import bcrypt


def criar_hash(senha: str) -> str:
    """
    Gera hash bcrypt da senha.
    bcrypt só aceita até 72 bytes → truncamos.
    """
    if not senha:
        senha = ""

    senha_bytes = senha.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(senha_bytes, salt)
    return hash_bytes.decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    """
    Verifica se a senha confere com o hash salvo.
    """
    if not senha or not senha_hash:
        return False

    try:
        senha_bytes = senha.encode("utf-8")[:72]
        hash_bytes = senha_hash.encode("utf-8")
        return bcrypt.checkpw(senha_bytes, hash_bytes)
    except Exception:
        return False
