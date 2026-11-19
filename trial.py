from time import monotonic
from uuid import uuid4
import sqlite3
import pandas as pd
import streamlit as st
from triage import ROOT, candidates, draft


def practice(reports):
    st.header("Timed first-reply practice")
    st.write("Complete two different cases with the same symptom. For each, prepare a usable first reply and decide whether to keep an earlier ticket reference. Timing starts when you reveal the case.")
    with sqlite3.connect(ROOT / "workspace.sqlite3") as db:
        db.execute("""CREATE TABLE IF NOT EXISTS trials (
            pair TEXT, mode TEXT, ticket TEXT, seconds REAL, reply TEXT, reference TEXT,
            PRIMARY KEY(pair, mode))""")
        results = pd.read_sql_query("SELECT * FROM trials",db)
    if not results.empty:
        times = results.pivot(index="pair",columns="mode",values="seconds").reindex(columns=["Manual","Assisted"]).dropna()
        if len(times):
            st.metric("Median paired practice saving",f"{(times.Manual-times.Assisted).median():.1f} seconds")
        st.download_button("Download practice timings",results.to_csv(index=False),"practice_timings.csv","text/csv")
    state = st.session_state
    if "pairinfo" not in state:
        if st.button("Begin a practice pair"):
            # Rotate order and case assignment independently over consecutive pairs.
            i = results.pair.nunique() if len(results) else 0
            groups = list(reports.groupby("symptom"))
            group = groups[i % len(groups)][1]
            ids = group.ticket_id.tolist()
            offset = 2 + (2*(i//len(groups))) % (len(ids)-3)
            cases = ids[offset:offset+2]
            modes = ["Manual","Assisted"] if i%2 == 0 else ["Assisted","Manual"]
            state.pairinfo = (uuid4().hex, list(zip(cases,modes)),0)
            st.rerun()
        return
    pair, tasks, step = state.pairinfo
    ticket, mode = tasks[step]
    st.subheader(f"Task {step+1} of 2 · {mode}")
    if "clock" not in state:
        if st.button("Reveal case and start timer"):
            state.clock = monotonic()
            st.rerun()
        return
    case = reports.loc[ticket]
    st.write(f"{ticket} · {case.description}")
    if mode == "Manual":
        history = reports[reports.created_at < case.created_at].sort_values("created_at",ascending=False)
        term = st.text_input("Search earlier descriptions",key=pair+ticket+"search")
        hits = history[history.description.str.contains(term,case=False,regex=False)]
        st.dataframe(hits[["ticket_id","description","client_name"]],hide_index=True)
        proposed = ""
    else:
        hits = candidates(reports,case)
        st.dataframe(hits[["ticket_id","description","client_name"]],hide_index=True)
        proposed = draft(case)[0]
    ref = st.selectbox("Reference decision",["Select a decision","No confirmed reference"]+hits.ticket_id.tolist(),key=pair+ticket+"ref")
    reply = st.text_area("First reply",value=proposed,key=pair+ticket+"reply")
    if st.button("Finish and record time",disabled=not reply.strip() or ref=="Select a decision"):
        elapsed = round(monotonic()-state.clock,2)
        with sqlite3.connect(ROOT / "workspace.sqlite3") as db:
            db.execute("INSERT OR IGNORE INTO trials VALUES(?,?,?,?,?,?)",(pair,mode,ticket,elapsed,reply,ref))
        del state.clock
        if step==0:
            state.pairinfo = (pair,tasks,1)
        else:
            del state.pairinfo
        st.rerun()
