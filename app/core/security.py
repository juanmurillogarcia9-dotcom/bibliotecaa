from pwdlib import PasswordHash

# Inicializamos el gestor de contraseñas con el algoritmo moderno Argon2
password_hash = PasswordHash.recommended()

def verificar_password(password_plana: str, password_hash_guardado: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con su hash almacenado."""
    return password_hash.verify(password_plana, password_hash_guardado)

def obtener_password_hash(password_plana: str) -> str:
    """Genera el hash seguro de una contraseña usando Argon2."""
    return password_hash.hash(password_plana)