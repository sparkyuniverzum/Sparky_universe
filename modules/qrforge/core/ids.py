import uuid


def generate_public_id(prefix: str = "QR") -> str:
    """
    Generates a public, human-safe identifier.
    This identifier carries no meaning by itself.
    """
    return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"
