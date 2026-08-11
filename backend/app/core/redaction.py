"""Field-level redaction for roles below clinic owner.

Applied in the API layer and in the assistant's toolbox — never in the
repositories, which stay role-blind so there is exactly one definition of
"what a non-owner may not see".

This exists because the restriction used to live only in the assistant's
system prompt, which asked the *model* not to disclose patient contact
details or dentist commissions. A prompt is not an access control: the model
can be talked out of it, and the same rows were one unguarded REST call away
regardless of what the prompt said. Redacting the payload means a non-owner
cannot see the field however they reach it.

Aggregates are deliberately left intact. A receptionist should still see that
twelve patients need a recall call and what they are collectively worth; what
they should not see is which twelve, and on what phone number.
"""

OWNER_ROLE = "مدیر"

# Shown in place of a redacted value, so the column still lines up and the
# caller can tell the field was withheld rather than missing from the data.
PLACEHOLDER = "—"

# Direct patient identifiers.
PATIENT_CONTACT = ("name", "patient", "phone", "national_code")

# What each dentist personally earns, and what the clinic keeps after paying
# them — commercially sensitive between colleagues, not just externally.
COMMISSION = ("commission", "commission_rate", "commission_rate_pct", "margin",
              "clinic_margin")


def is_owner(claims: dict) -> bool:
    return claims.get("role") == OWNER_ROLE


def scrub(rows: list[dict], fields: tuple[str, ...]) -> list[dict]:
    """Copy of `rows` with the named keys replaced by the placeholder.

    Copies rather than mutating: these dicts come straight from a repository
    and may be shared with another caller in the same request.
    """
    return [
        {k: (PLACEHOLDER if k in fields else v) for k, v in row.items()}
        for row in rows
    ]
