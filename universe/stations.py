from __future__ import annotations

from typing import Dict, List


_STATIONS: List[Dict[str, object]] = [
    {
        "id": "vehicle-transfer-cz",
        "slug": "vehicle-transfer-cz",
        "title": "Vehicle Transfer (CZ)",
        "summary": "Transfer vehicle ownership in the Czech Republic.",
        "mount": "/stations/vehicle-transfer-cz",
        "country": "CZ",
        "region": "Czech Republic",
        "status": "live",
        "last_verified": "2026-01-04",
        "sections": [
            {
                "kind": "what",
                "title": "What you're solving",
                "text": "You need to transfer vehicle ownership after a sale, gift, or inheritance in the Czech Republic within 10 working days.",
            },
            {
                "kind": "need",
                "title": "What you need",
                "items": [
                    "Application form for change of owner (official form).",
                    "Valid ID (ID card or passport).",
                    "Vehicle registration certificate (both parts, if issued).",
                    "Proof of ownership (purchase contract, gift deed, inheritance).",
                    "Proof of insurance (green card) for the new owner.",
                    "Valid technical inspection (STK) or evidence inspection record, if required.",
                    "Power of attorney if only one party or a representative attends.",
                ],
            },
            {
                "kind": "where",
                "title": "Where to go / what to open",
                "items": [
                    "Municipal office with extended powers (ORP) — vehicle register desk.",
                    "You can start online via the state portal, but the office often requires an in-person visit.",
                    "Book an appointment if your office supports it.",
                ],
            },
            {
                "kind": "fill",
                "title": "What to fill",
                "items": [
                    "Application for a change of owner/operator in the vehicle register.",
                    "Buyer and seller signatures (or legal representatives).",
                    "Vehicle plate and VIN exactly as registered.",
                ],
            },
            {
                "kind": "cost",
                "title": "How much it costs",
                "items": [
                    "Administrative fee (around CZK 800 for passenger cars).",
                    "Possible lower fee for online submission (around CZK 640).",
                    "Optional new plates or export plates if requested.",
                    "Notary/legalization fees if a power of attorney requires it.",
                ],
            },
            {
                "kind": "mistakes",
                "title": "Common mistakes",
                "items": [
                    "Missing signatures on the transfer agreement.",
                    "Expired or missing insurance.",
                    "VIN or plate mismatch between documents.",
                    "Expired technical inspection (STK).",
                    "Missing power of attorney when a representative submits.",
                    "Missing the 10 working day deadline (risk of a fine up to CZK 50,000).",
                    "Expecting plates to change automatically.",
                ],
            },
            {
                "kind": "sources",
                "title": "Official sources",
                "sources": [
                    {
                        "label": "Ministry of Transport — change of owner",
                        "url": "https://md.gov.cz/Zivotni-situace/Registr-vozidel/zmena-vlastnika",
                    },
                    {
                        "label": "GOV.CZ service page",
                        "url": "https://portal.gov.cz/sluzby-vs/zapis-zmeny-vlastnika-vozidla-v-registru-silnicnich-vozidel-S8478",
                    },
                    {
                        "label": "Official vehicle registry forms",
                        "url": "https://md.gov.cz/Dokumenty/Silnicni-doprava/Elektronicke-formulare-%281%29/",
                    },
                ],
            },
            {"kind": "last_verified", "title": "Last verified", "text": "2026-01-04"},
        ],
        "pro": [
            "Downloadable checklist (PDF).",
            "Monthly alerts on procedure changes.",
            "Regional variant (CZ + DE-BY).",
        ],
        "pro_title": "Pro (optional)",
        "translations": {
            "cs": {
                "title": "Přepis vozidla (CZ)",
                "summary": "Změna vlastníka vozidla v České republice.",
                "country": "CZ",
                "region": "Česká republika",
                "last_verified": "2026-01-04",
                "sections": [
                    {
                        "kind": "what",
                        "title": "Co řešíš",
                        "text": "Přepis vlastníka vozidla po prodeji, darování nebo dědictví v ČR do 10 pracovních dnů.",
                    },
                    {
                        "kind": "need",
                        "title": "Co potřebuješ",
                        "items": [
                            "Žádost o zápis změny vlastníka (tiskopis úřadu).",
                            "Platný doklad totožnosti (OP nebo pas).",
                            "Technický průkaz vozidla (velký i malý, pokud byly vydány).",
                            "Doklad o nabytí vozidla (kupní smlouva, darovací smlouva, dědictví).",
                            "Zelená karta (povinné ručení) nového vlastníka.",
                            "Platná technická / evidenční kontrola, pokud je vyžadována.",
                            "Plná moc, pokud jedná jen jedna strana nebo zástupce.",
                        ],
                    },
                    {
                        "kind": "where",
                        "title": "Kam jít / co otevřít",
                        "items": [
                            "Úřad obce s rozšířenou působností (ORP) — registr vozidel.",
                            "Část žádosti lze zahájit online, ale úřad často vyžaduje osobní návštěvu.",
                            "Objednej se, pokud to úřad umožňuje.",
                        ],
                    },
                    {
                        "kind": "fill",
                        "title": "Co vyplnit",
                        "items": [
                            "Žádost o změnu vlastníka/provozovatele v registru.",
                            "Podpisy prodávajícího i kupujícího (nebo zástupců).",
                            "SPZ a VIN přesně podle registru.",
                        ],
                    },
                    {
                        "kind": "cost",
                        "title": "Kolik to stojí",
                        "items": [
                            "Správní poplatek (cca 800 Kč u osobních aut).",
                            "Možná nižší poplatek při online podání (cca 640 Kč).",
                            "Poplatek za nové značky nebo exportní značky, pokud je požaduješ.",
                            "Ověření podpisů / notářské poplatky u plné moci.",
                        ],
                    },
                    {
                        "kind": "mistakes",
                        "title": "Časté chyby",
                        "items": [
                            "Chybějící podpisy na smlouvě.",
                            "Neplatné nebo chybějící pojištění.",
                            "Nesoulad VIN nebo SPZ v dokumentech.",
                            "Propadlá technická kontrola (STK).",
                            "Chybějící plná moc při zastupování.",
                            "Nedodržení lhůty 10 pracovních dnů (riziko pokuty až 50 000 Kč).",
                            "Očekávání, že se SPZ změní automaticky.",
                        ],
                    },
                    {
                        "kind": "sources",
                        "title": "Oficiální zdroje",
                        "sources": [
                            {
                                "label": "Ministerstvo dopravy — změna vlastníka",
                                "url": "https://md.gov.cz/Zivotni-situace/Registr-vozidel/zmena-vlastnika",
                            },
                            {
                                "label": "Portál GOV.CZ — služba",
                                "url": "https://portal.gov.cz/sluzby-vs/zapis-zmeny-vlastnika-vozidla-v-registru-silnicnich-vozidel-S8478",
                            },
                            {
                                "label": "Formuláře registru vozidel",
                                "url": "https://md.gov.cz/Dokumenty/Silnicni-doprava/Elektronicke-formulare-%281%29/",
                            },
                        ],
                    },
                    {"kind": "last_verified", "title": "Naposledy ověřeno", "text": "2026-01-04"},
                ],
                "pro": [
                    "Checklist ke stažení (PDF).",
                    "Měsíční upozornění na změny postupu.",
                    "Regionální varianta (CZ + DE-BY).",
                ],
                "pro_title": "Pro (volitelné)",
            }
        },
    },
    {
        "id": "business-formation-cz",
        "slug": "business-formation-cz",
        "title": "Business Formation (CZ) · OSVČ / s.r.o. / a.s.",
        "summary": "Choose and set up a Czech sole trader, limited company, or joint-stock company.",
        "mount": "/stations/business-formation-cz",
        "country": "CZ",
        "region": "Czech Republic",
        "status": "live",
        "last_verified": "2026-01-04",
        "sections": [
            {
                "kind": "what",
                "title": "What you're solving",
                "text": "You need to set up a legal business form in the Czech Republic: OSVČ, s.r.o., or a.s.",
            },
            {
                "kind": "need",
                "title": "What you need",
                "items": [
                    "OSVČ: unified registration form, valid ID, trade fee (around CZK 1,000; CZK 800 online).",
                    "OSVČ: professional qualification documents for regulated trades (if required).",
                    "s.r.o.: company name + registered office consent, founders’ deed (notarial).",
                    "s.r.o.: capital deposit confirmation (even symbolic).",
                    "a.s.: statutes (notarial), higher capital (min. CZK 2,000,000 or EUR equivalent).",
                    "a.s.: documents for board members and supervisory bodies (signatures, extracts).",
                ],
            },
            {
                "kind": "where",
                "title": "Where to go / what to open",
                "items": [
                    "OSVČ: Trade Licensing Office or online via the state portal / data box.",
                    "s.r.o. / a.s.: Notary for the deed and Commercial Register filing.",
                    "Commercial Register: filing is typically handled by the notary.",
                ],
            },
            {
                "kind": "fill",
                "title": "What to fill",
                "items": [
                    "OSVČ: unified registration form for trade licensing and tax/social/health registration.",
                    "s.r.o.: founders’ deed or articles of association.",
                    "a.s.: statutes and corporate body appointments.",
                ],
            },
            {
                "kind": "cost",
                "title": "How much it costs",
                "items": [
                    "OSVČ: approx. CZK 1,000 (CZK 800 online).",
                    "s.r.o.: notary fees + register filing fee (varies by case).",
                    "a.s.: notary fees + higher capital requirements + register filing fee.",
                ],
            },
            {
                "kind": "mistakes",
                "title": "Common mistakes",
                "items": [
                    "Missing registered office consent or incorrect address.",
                    "Starting a regulated trade without required qualification.",
                    "Not registering with social/health insurance in time (OSVČ: within 8 days).",
                    "Incorrect or missing signatures on founders’ documents.",
                ],
            },
            {
                "kind": "sources",
                "title": "Official sources",
                "sources": [
                    {
                        "label": "State portal (services and forms)",
                        "url": "https://portal.gov.cz",
                    },
                    {
                        "label": "Ministry of Industry and Trade (trade licensing)",
                        "url": "https://www.mpo.cz",
                    },
                    {
                        "label": "Commercial Register (Justice.cz)",
                        "url": "https://or.justice.cz",
                    },
                ],
            },
            {"kind": "last_verified", "title": "Last verified", "text": "2026-01-04"},
        ],
        "pro": [
            "Downloadable checklist (PDF).",
            "Monthly alerts on procedure changes.",
            "Template founders’ documents.",
        ],
        "pro_title": "Pro (optional)",
        "translations": {
            "cs": {
                "title": "Založení podnikání (CZ) · OSVČ / s.r.o. / a.s.",
                "summary": "Výběr a založení OSVČ, s.r.o. nebo a.s. v České republice.",
                "country": "CZ",
                "region": "Česká republika",
                "last_verified": "2026-01-04",
                "sections": [
                    {
                        "kind": "what",
                        "title": "Co řešíš",
                        "text": "Potřebuješ založit podnikání v ČR jako OSVČ, s.r.o. nebo a.s.",
                    },
                    {
                        "kind": "need",
                        "title": "Co potřebuješ",
                        "items": [
                            "OSVČ: jednotný registrační formulář, platný doklad totožnosti, správní poplatek (cca 1 000 Kč; 800 Kč online).",
                            "OSVČ: odborná způsobilost u řemeslných/vázaných živností (pokud je vyžadována).",
                            "s.r.o.: název firmy + sídlo a souhlas vlastníka nemovitosti.",
                            "s.r.o.: společenská smlouva / zakladatelská listina (notářsky ověřená).",
                            "s.r.o.: vklad základního kapitálu (i symbolicky).",
                            "a.s.: stanovy (notářsky ověřené) a základní kapitál min. 2 000 000 Kč nebo EUR ekvivalent.",
                            "a.s.: doklady členů orgánů (podpisové vzory, výpisy).",
                        ],
                    },
                    {
                        "kind": "where",
                        "title": "Kam jít / co otevřít",
                        "items": [
                            "OSVČ: živnostenský úřad nebo online přes Portál občana / datovou schránku.",
                            "s.r.o. / a.s.: notář pro zakladatelské dokumenty a podání do obchodního rejstříku.",
                            "Obchodní rejstřík: zápis obvykle zajišťuje notář.",
                        ],
                    },
                    {
                        "kind": "fill",
                        "title": "Co vyplnit",
                        "items": [
                            "OSVČ: jednotný registrační formulář pro živnost, daň, OSSZ a ZP.",
                            "s.r.o.: společenská smlouva / zakladatelská listina.",
                            "a.s.: stanovy a jmenování orgánů společnosti.",
                        ],
                    },
                    {
                        "kind": "cost",
                        "title": "Kolik to stojí",
                        "items": [
                            "OSVČ: cca 1 000 Kč (800 Kč online).",
                            "s.r.o.: notářské poplatky + poplatek za zápis do rejstříku (dle případu).",
                            "a.s.: notářské poplatky + vyšší kapitál + poplatek za zápis.",
                        ],
                    },
                    {
                        "kind": "mistakes",
                        "title": "Časté chyby",
                        "items": [
                            "Chybějící souhlas vlastníka se sídlem nebo špatná adresa.",
                            "Založení vázané živnosti bez požadované kvalifikace.",
                            "Pozdní registrace OSSZ a ZP (OSVČ: do 8 dnů).",
                            "Neúplné nebo nesprávné podpisy zakladatelských dokumentů.",
                        ],
                    },
                    {
                        "kind": "sources",
                        "title": "Oficiální zdroje",
                        "sources": [
                            {
                                "label": "Portál veřejné správy (služby a formuláře)",
                                "url": "https://portal.gov.cz",
                            },
                            {
                                "label": "MPO — živnostenské podnikání",
                                "url": "https://www.mpo.cz",
                            },
                            {
                                "label": "Obchodní rejstřík (Justice.cz)",
                                "url": "https://or.justice.cz",
                            },
                        ],
                    },
                    {"kind": "last_verified", "title": "Naposledy ověřeno", "text": "2026-01-04"},
                ],
                "pro": [
                    "Checklist ke stažení (PDF).",
                    "Měsíční upozornění na změny postupu.",
                    "Šablony zakladatelských dokumentů.",
                ],
                "pro_title": "Pro (volitelné)",
            }
        },
    },
]


def list_stations() -> List[Dict[str, object]]:
    return list(_STATIONS)


def get_station(slug: str) -> Dict[str, object] | None:
    for station in _STATIONS:
        if station.get("slug") == slug:
            return station
    return None
