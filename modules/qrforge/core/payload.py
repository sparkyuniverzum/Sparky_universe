from typing import Dict


def build_identity_payload(
    public_id: str,
    name: str | None = None,
    supplier: str | None = None,
    supplier_sku: str | None = None,
) -> Dict[str, str]:
    """
    Builds a minimal identity payload.
    Carries no business meaning by itself.
    """
    payload = {
        "public_id": public_id,
    }

    if name:
        payload["name"] = name
    if supplier:
        payload["supplier"] = supplier
    if supplier_sku:
        payload["supplier_sku"] = supplier_sku

    return payload
