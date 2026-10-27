import re
from urllib.parse import quote
import pandas as pd

REQUIRED_COLUMNS = ["id", "created_at", "business_name", "category", "contact_person", "phone", "email", "city", "source_url", "status", "priority", "consent_to_marketing", "next_follow_up", "notes", "service_interest", "budget", "project_timeline", "preferred_language"]

def make_whatsapp_url(phone, business_name=""):
    digits = re.sub(r"\D", "", str(phone or ""))
    if digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = "92" + digits[1:]
    elif digits.startswith("3") and len(digits) == 10:
        digits = "92" + digits
    if not digits.isdigit() or not 10 <= len(digits) <= 15:
        return None
    msg = "Assalam-o-Alaikum! We are contacting you from ASF Digital Solutions."
    if business_name:
        msg += f" Regarding {business_name}."
    msg += " Please let us know a convenient time to discuss your requirements."
    return f"https://wa.me/{digits}?text={quote(msg)}"

def normalize_import_frame(frame):
    df = frame.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    aliases = {"business":"business_name", "company":"business_name", "name":"business_name", "mobile":"phone", "whatsapp":"phone", "location":"city", "website":"source_url", "service":"service_interest", "language":"preferred_language"}
    df = df.rename(columns={c: aliases[c] for c in df.columns if c in aliases})
    if "business_name" not in df.columns:
        raise ValueError("CSV must include business_name, business, company, or name.")
    cols = ["business_name", "category", "contact_person", "phone", "email", "city", "source_url", "status", "priority", "consent_to_marketing", "next_follow_up", "notes", "service_interest", "budget", "project_timeline", "preferred_language"]
    for col in cols:
        if col not in df.columns:
            df[col] = None
    df = df[cols]
    df["business_name"] = df["business_name"].fillna("").astype(str).str.strip()
    df = df[df["business_name"] != ""]
    df["category"] = df["category"].fillna("Other")
    df["status"] = df["status"].fillna("New")
    df["priority"] = df["priority"].fillna("Warm")
    df["consent_to_marketing"] = df["consent_to_marketing"].fillna(False).astype(bool)
    return df
