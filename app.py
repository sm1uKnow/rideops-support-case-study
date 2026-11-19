import hashlib
import sqlite3
import streamlit as st
from triage import ROOT, candidates, draft, evaluate, load, reports

st.set_page_config(page_title="RideOps · Report support", layout="wide")
r = reports(load())
st.title("Report support")
from trial import practice

mode = st.sidebar.radio("Workspace", ["Agent desk", "Timed practice"])
if mode == "Timed practice":
    practice(r)
    st.stop()

pool = r[r.final_closed_at.isna()].sort_values(["priority", "created_at"])
st.caption("Open report-export tickets at 30 September. Earlier reports are replayed as of each ticket’s arrival.")
with sqlite3.connect(ROOT / "workspace.sqlite3") as db:
    db.execute("CREATE TABLE IF NOT EXISTS reviews(ticket TEXT PRIMARY KEY, reference TEXT, reply TEXT)")
    reviewed = {row[0] for row in db.execute("SELECT ticket FROM reviews")}
if st.checkbox("Only tickets needing a first draft"):
    pool = pool[~pool.ticket_id.isin(reviewed)]
if "saved_notice" in st.session_state:
    st.success("Saved reviewed draft for " + st.session_state.pop("saved_notice"))
if pool.empty:
    st.success("All open tickets have a saved first draft.")
    st.stop()
ticket = st.selectbox("Choose an open ticket",pool.ticket_id.tolist(),
                      format_func=lambda t: f"{t} · {pool.loc[t,'description']} · {'Reviewed' if t in reviewed else 'Needs draft'}")
case = r.loc[ticket]
hits = candidates(r,case)
st.subheader(case.description)
st.caption(f"{case.client_name} · {case.created_at:%d %b %Y, %H:%M} IST · {case.priority}")
left,right = st.columns(2)
with left:
    st.markdown("### Earlier reports")
    if hits.empty:
        st.write("No earlier report with this symptom.")
    for h in hits.to_dict("records"):
        with st.container(border=True):
            st.markdown(f"**{h['ticket_id']}** · {h['created_at']:%d %b, %H:%M}")
            st.write(h["description"])
            st.caption(f"{h['client_name']} · {h['Known outcome']} · {h['Engineering reference']}")
with right:
    st.markdown("### Suggested reply")
    reply = st.text_area("Add client detail to refine the draft",key="context_"+ticket)
    proposed,missing = draft(case,reply)
    st.caption("Details to confirm: " + ", ".join(missing) if missing else "Requested details detected.")
    version = hashlib.sha256(proposed.encode()).hexdigest()[:12]
    edited = st.text_area("Review and edit",value=proposed,key=f"draft_{ticket}_{version}",height=135)
    st.code(edited,language=None,wrap_lines=True)
    choice = st.selectbox("Reference to keep with the draft",["None"]+hits.ticket_id.tolist(),key="ref_"+ticket)
    with sqlite3.connect(ROOT / "workspace.sqlite3") as db:
        db.execute("CREATE TABLE IF NOT EXISTS reviews(ticket TEXT PRIMARY KEY, reference TEXT, reply TEXT)")
        if st.button("Save reviewed draft",disabled=not edited.strip()):
            db.execute("INSERT OR REPLACE INTO reviews VALUES (?,?,?)",(ticket,choice,edited))
            st.session_state["saved_notice"] = ticket
            st.rerun()
        saved = db.execute("SELECT reference,reply FROM reviews WHERE ticket=?",(ticket,)).fetchone()
    if saved:
        with st.expander("Last saved review"):
            st.write("Reference: "+saved[0])
            st.code(saved[1],language=None,wrap_lines=True)
