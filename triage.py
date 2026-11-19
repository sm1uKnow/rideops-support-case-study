"""Local search and reply drafting for the five report symptoms in the case data."""
from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent
CATEGORY = "Report export failing"
DATE = r"(?:\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/.-]\d{1,2}(?:[/.-]\d{2,4})?|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*)"
TIME = r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b|\b(?:1[0-2]|0?[1-9])\s*[ap]m\b"
QUESTIONS = {
    "range": "Which start and end dates did you select?",
    "time": "Around what time did this happen?",
    "recipient": "Which mailbox or distribution list should receive the report?",
    "trip": "Could you share one affected trip reference?",
    "name": "Which report were you exporting?",
}
FIELDS = {"Download stuck": ["range","time"], "Missing trips": ["name","range","trip"],
          "Scheduled email missing": ["recipient","time"], "Blank spreadsheet": ["range","time"],
          "Date range failure": ["name","range"], "Other report issue": ["name","time"]}


def load():
    return pd.read_csv(ROOT / "data/rideops_support_tickets.csv", parse_dates=["created_at","final_closed_at"])


def symptom(text):
    text = text.lower()
    for words, label in [(("stuck","loading"),"Download stuck"), (("missing","trips"),"Missing trips"),
                         (("scheduled","email"),"Scheduled email missing"), (("excel","blank"),"Blank spreadsheet"),
                         (("date range","fails"),"Date range failure")]:
        if all(word in text for word in words):
            return label
    return "Other report issue"


def reports(d):
    r = d[d.category.eq(CATEGORY)].sort_values(["created_at","ticket_id"]).copy()
    r["symptom"] = r.description.map(symptom)
    return r.set_index("ticket_id",drop=False)


def candidates(r, case):
    previous = r[(r.created_at < case.created_at) & r.symptom.eq(case.symptom)].copy()
    if case.symptom == "Other report issue":
        previous = previous[previous.description.str.casefold().eq(case.description.casefold())]
    previous["same_client"] = previous.client_id.eq(case.client_id)
    previous = previous.sort_values(["same_client","created_at"],ascending=False).head(3)
    closed = previous.final_closed_at.lt(case.created_at)
    previous["Known outcome"] = previous.eng_outcome.fillna("Closed by L1").where(closed,"Unavailable at arrival")
    previous["Engineering reference"] = previous.eng_ticket_id.fillna("—").where(closed,"—")
    return previous


def draft(case, reply=""):
    text = (case.description + " " + reply).lower()
    present = {"range": len(re.findall(DATE,text)) >= 2,
               "time": bool(re.search(TIME,text)),
               "recipient": bool(re.search(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}",text)),
               "trip": bool(re.search(r"\btrip[- #]+[a-z]*\d+\b",text)),
               "name": bool(re.search(r"\b(billing|monthly trip|daily trip|attendance|invoice|compliance) report\b",text))}
    missing = [key for key in FIELDS[case.symptom] if not present[key]]
    if missing:
        return "Thanks for reporting this. " + " ".join(QUESTIONS[key] for key in missing), missing
    return "Thanks for the details. We’ll use them to investigate the report issue and follow up here.", []


def evaluate(r):
    rows = []
    for case in r.itertuples(index=False):
        hits = candidates(r,case)
        rows.append({"ticket_id":case.ticket_id, "created_at":case.created_at,
                     "later_duplicate":case.eng_outcome == "Duplicate of known issue",
                     "candidate_count":len(hits), "suggestions":", ".join(hits.ticket_id)})
    return pd.DataFrame(rows)
