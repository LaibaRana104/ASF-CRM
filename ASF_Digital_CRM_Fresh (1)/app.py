import os
from datetime import date
import io
import pandas as pd
import streamlit as st
from supabase import create_client
from lead_logic import make_whatsapp_url, normalize_import_frame

st.set_page_config(page_title="ASF Digital Solutions CRM", page_icon="💼", layout="wide")
NAVY, GOLD = "#071B36", "#F2B632"

def secret(key, default=""):
    try:
        v = st.secrets.get(key, default)
        if v: return str(v)
    except Exception: pass
    return os.getenv(key, default)

def theme_css(mode):
    if mode == "Dark":
        bg, panel, fg, muted, border, fields = "#0B1220", "#111C2E", "#F3F6FC", "#B8C4D8", "#334155", "#172338"
    else:
        bg, panel, fg, muted, border, fields = "#F5F7FB", "#FFFFFF", "#172033", "#526079", "#D7DFEA", "#FFFFFF"
    st.markdown(f"""<style>
    .stApp {{background:{bg};color:{fg}}} [data-testid="stHeader"]{{background:{bg}}}
    [data-testid="stSidebar"]{{background:{panel};border-right:1px solid {border}}}
    [data-testid="stSidebar"] *{{color:{fg}!important}}
    h1,h2,h3,h4,p,label,span,[data-testid="stMetricLabel"],[data-testid="stMetricValue"]{{color:{fg}}}
    [data-testid="stMetric"]{{background:{panel};border:1px solid {border};padding:14px;border-radius:12px}}
    div[data-baseweb="input"]>div,div[data-baseweb="select"]>div,textarea{{background:{fields}!important;color:{fg}!important;border-color:{border}!important}}
    input,textarea{{color:{fg}!important;-webkit-text-fill-color:{fg}!important}}
    [data-baseweb="select"] *{{color:{fg}!important}}
    .stButton>button,.stDownloadButton>button{{background:{GOLD}!important;color:{NAVY}!important;border:1px solid {GOLD}!important;border-radius:9px;font-weight:700}}
    .asf-banner{{background:{NAVY};color:white;padding:1.1rem 1.3rem;border-radius:14px;border-left:6px solid {GOLD};margin-bottom:1rem}}
    .asf-banner h1{{color:white!important;margin:0}} .asf-banner p{{color:#E5ECF6!important;margin:.3rem 0 0}}
    .wa-button{{display:inline-block;background:#25D366;color:#052E16!important;font-weight:700;padding:.65rem 1rem;border-radius:9px;text-decoration:none!important;margin:.25rem 0}}
    </style>""", unsafe_allow_html=True)

def db_client():
    url, key = secret("SUPABASE_URL"), secret("SUPABASE_KEY")
    if not url or not key: return None, "SUPABASE_URL or SUPABASE_KEY is missing in Streamlit Secrets."
    try: return create_client(url, key), None
    except Exception as e: return None, str(e)

def text(v):
    return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).strip()

with st.sidebar:
    st.markdown(f"<h2 style='color:{GOLD};margin-bottom:0'>ASF CRM</h2><p>Digital Solutions</p>", unsafe_allow_html=True)
    mode = st.radio("Appearance", ["Light", "Dark"], horizontal=True)
theme_css(mode)
password = secret("APP_PASSWORD")
if not password:
    st.error("APP_PASSWORD is missing. Add it in Streamlit Cloud → Settings → Secrets.")
    st.stop()
if not st.session_state.get("logged_in"):
    st.markdown(f"<div class='asf-banner'><h1>ASF Digital Solutions</h1><p>Lead Management & Customer Relationship Dashboard</p></div>", unsafe_allow_html=True)
    with st.form("login"):
        entered = st.text_input("App password", type="password")
        submitted = st.form_submit_button("Log in", use_container_width=True)
    if submitted:
        if entered == password:
            st.session_state.logged_in = True
            st.rerun()
        st.error("Incorrect password.")
    st.stop()

with st.sidebar:
    page = st.radio("Navigation", ["Dashboard", "Add Lead", "Manage Leads", "Import / Export", "Setup Guide"])
    if st.button("Log out", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
st.markdown("<div class='asf-banner'><h1>ASF Digital Solutions</h1><p>Lead Management & Customer Relationship Dashboard</p></div>", unsafe_allow_html=True)
client, err = db_client()
if err:
    st.error(err); st.stop()
try:
    rows = client.table("leads").select("*").order("created_at", desc=True).execute().data or []
    leads = pd.DataFrame(rows)
except Exception as e:
    st.error("Could not load public.leads. Run supabase_setup.sql in the new Supabase project's SQL Editor and check the server-side key.")
    st.code(str(e)); st.stop()

def add_record(payload):
    client.table("leads").insert(payload).execute()

if page == "Dashboard":
    st.subheader("Dashboard")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total leads", len(leads))
    c2.metric("New leads", int((leads.get("status", pd.Series(dtype=str)).fillna("New")=="New").sum()))
    c3.metric("Hot leads", int((leads.get("priority", pd.Series(dtype=str)).fillna("Warm")=="Hot").sum()))
    c4.metric("Follow-ups", int(leads.get("next_follow_up", pd.Series(dtype=object)).notna().sum()))
    st.markdown("### Recent leads")
    if leads.empty: st.info("No leads yet. Use Add Lead to create your first record.")
    else: st.dataframe(leads.head(10), use_container_width=True, hide_index=True)

elif page == "Add Lead":
    st.subheader("Add a new lead")
    with st.form("add_lead", clear_on_submit=True):
        a,b = st.columns(2)
        name = a.text_input("Business / organization name *")
        category = b.selectbox("Category", ["Schools","Colleges","E-commerce","Real Estate","Restaurants","Software","Other"])
        contact = a.text_input("Contact person")
        phone = b.text_input("Phone / WhatsApp (country code if possible)")
        email = a.text_input("Email")
        city = b.text_input("City / location")
        source = a.text_input("Source URL")
        service = b.selectbox("Service interest", ["Not specified","Website development","Software development","School management software","Social media marketing","AI chatbot","Mobile app","E-commerce","Lead generation","Other"])
        budget = a.selectbox("Budget", ["Not specified","Under PKR 25,000","PKR 25,000–50,000","PKR 50,000–100,000","PKR 100,000+","Need to discuss"])
        timeline = b.selectbox("Project timeline", ["Not specified","Immediately","Within 2 weeks","Within 1 month","1–3 months","Flexible"])
        language = a.selectbox("Preferred language", ["English","Urdu","Roman Urdu","Arabic","Chinese","French","Spanish","Punjabi","Bengali","Russian","Portuguese","German","Turkish","Hindi","Persian","Other"])
        status = b.selectbox("Status", ["New","Contacted","Interested","Follow-up","Converted","Not Interested"])
        priority = a.selectbox("Priority", ["Hot","Warm","Cold"], index=1)
        follow = b.date_input("Next follow-up date", value=None)
        consent = st.checkbox("Consent / appropriate basis for marketing contact confirmed")
        notes = st.text_area("Notes")
        save = st.form_submit_button("Save lead", use_container_width=True)
    if save:
        if not name.strip(): st.error("Business name is required.")
        else:
            payload = {"business_name":name.strip(),"category":category,"contact_person":contact.strip() or None,"phone":phone.strip() or None,"email":email.strip() or None,"city":city.strip() or None,"source_url":source.strip() or None,"service_interest":None if service=="Not specified" else service,"budget":None if budget=="Not specified" else budget,"project_timeline":None if timeline=="Not specified" else timeline,"preferred_language":language,"status":status,"priority":priority,"next_follow_up":follow.isoformat() if isinstance(follow,date) else None,"consent_to_marketing":consent,"notes":notes.strip() or None}
            try: add_record(payload); st.success("Lead saved."); st.rerun()
            except Exception as e: st.error(f"Could not save lead: {e}")

elif page == "Manage Leads":
    st.subheader("Search and update leads")
    if leads.empty: st.info("No leads yet. Use Add Lead or import a CSV file.")
    else:
        q=st.text_input("Search business, contact, phone, email, or city")
        c1,c2,c3=st.columns(3)
        cats=["All"]+sorted(leads.get("category",pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
        cat=c1.selectbox("Category",cats); stat=c2.selectbox("Status",["All","New","Contacted","Interested","Follow-up","Converted","Not Interested"]); pri=c3.selectbox("Priority",["All","Hot","Warm","Cold"])
        view=leads.copy()
        if q:
            mask=pd.Series(False,index=view.index)
            for col in ["business_name","contact_person","phone","email","city"]:
                if col in view: mask |= view[col].fillna("").astype(str).str.contains(q,case=False,regex=False)
            view=view[mask]
        if cat!="All": view=view[view.category==cat]
        if stat!="All": view=view[view.status.fillna("New")==stat]
        if pri!="All": view=view[view.priority.fillna("Warm")==pri]
        st.dataframe(view, use_container_width=True, hide_index=True)
        if not view.empty:
            selected=st.selectbox("Select lead",view.id.tolist(),format_func=lambda i:f"#{i} — {text(view.loc[view.id==i,'business_name'].iloc[0])}")
            item=view[view.id==selected].iloc[0].to_dict()
            st.markdown("### WhatsApp contact")
            url=make_whatsapp_url(item.get("phone"),item.get("business_name"))
            if url: st.markdown(f'<a class="wa-button" href="{url}" target="_blank" rel="noopener noreferrer">💬 Open WhatsApp Chat</a>',unsafe_allow_html=True); st.caption("Review the pre-filled message and send it manually.")
            else: st.warning("No valid phone number. Update the phone field to enable WhatsApp chat.")
            with st.form("edit_lead"):
                a,b=st.columns(2)
                name=a.text_input("Business name *",text(item.get("business_name")))
                category=b.selectbox("Category",["Schools","Colleges","E-commerce","Real Estate","Restaurants","Software","Other"],index=["Schools","Colleges","E-commerce","Real Estate","Restaurants","Software","Other"].index(item.get("category")) if item.get("category") in ["Schools","Colleges","E-commerce","Real Estate","Restaurants","Software","Other"] else 6)
                contact=a.text_input("Contact person",text(item.get("contact_person"))); phone=b.text_input("Phone / WhatsApp",text(item.get("phone")))
                email=a.text_input("Email",text(item.get("email"))); city=b.text_input("City",text(item.get("city")))
                source=a.text_input("Source URL",text(item.get("source_url"))); service=b.text_input("Service interest",text(item.get("service_interest")))
                budget=a.text_input("Budget",text(item.get("budget"))); timeline=b.text_input("Project timeline",text(item.get("project_timeline")))
                language=a.text_input("Preferred language",text(item.get("preferred_language")))
                statuses=["New","Contacted","Interested","Follow-up","Converted","Not Interested"]; oldstat=text(item.get("status")) or "New"
                status=b.selectbox("Status",statuses,index=statuses.index(oldstat) if oldstat in statuses else 0)
                priorities=["Hot","Warm","Cold"]; oldpri=text(item.get("priority")) or "Warm"
                priority=a.selectbox("Priority",priorities,index=priorities.index(oldpri) if oldpri in priorities else 1)
                olddate=item.get("next_follow_up")
                try: follow_default=date.fromisoformat(str(olddate)[:10]) if olddate else None
                except Exception: follow_default=None
                follow=b.date_input("Next follow-up",value=follow_default)
                consent=a.checkbox("Consent / appropriate basis for marketing contact confirmed",value=bool(item.get("consent_to_marketing")))
                notes=st.text_area("Notes",text(item.get("notes")))
                save=st.form_submit_button("Save changes",use_container_width=True)
            if save:
                try:
                    updates={"business_name":name.strip(),"category":category,"contact_person":contact.strip() or None,"phone":phone.strip() or None,"email":email.strip() or None,"city":city.strip() or None,"source_url":source.strip() or None,"service_interest":service.strip() or None,"budget":budget.strip() or None,"project_timeline":timeline.strip() or None,"preferred_language":language.strip() or None,"status":status,"priority":priority,"next_follow_up":follow.isoformat() if isinstance(follow,date) else None,"consent_to_marketing":consent,"notes":notes.strip() or None}
                    client.table("leads").update(updates).eq("id",selected).execute(); st.success("Lead updated."); st.rerun()
                except Exception as e: st.error(f"Could not update lead: {e}")
            with st.expander("Delete selected lead"):
                confirm=st.checkbox("I understand deletion is permanent",key=f"confirm_{selected}")
                if st.button("Delete lead",disabled=not confirm,key=f"delete_{selected}"):
                    try: client.table("leads").delete().eq("id",selected).execute(); st.success("Lead deleted."); st.rerun()
                    except Exception as e: st.error(f"Could not delete lead: {e}")

elif page == "Import / Export":
    st.subheader("Import / Export")
    if not leads.empty:
        st.download_button("Download CSV",leads.to_csv(index=False).encode("utf-8-sig"),file_name="asf_leads.csv",mime="text/csv",use_container_width=True)
        buf=io.BytesIO()
        with pd.ExcelWriter(buf,engine="openpyxl") as writer: leads.to_excel(writer,index=False,sheet_name="Leads")
        st.download_button("Download Excel",buf.getvalue(),file_name="asf_leads.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
    else: st.info("No leads to export yet.")
    upload=st.file_uploader("Import a CSV file",type=["csv"])
    if upload:
        try:
            imported=normalize_import_frame(pd.read_csv(upload)); st.dataframe(imported.head(20),use_container_width=True,hide_index=True)
            if st.button(f"Import {len(imported)} rows"):
                records=imported.astype(object).where(pd.notna(imported),None).to_dict("records")
                if records: client.table("leads").insert(records).execute()
                st.success(f"Imported {len(records)} leads."); st.rerun()
        except Exception as e: st.error(f"CSV import failed: {e}")

else:
    st.subheader("Setup Guide")
    st.markdown("1. Run `supabase_setup.sql` in the new Supabase project's SQL Editor.\n2. Deploy this repository to Streamlit Cloud using `app.py`.\n3. Add credentials in Streamlit Secrets.\n4. Test adding a lead, both themes, WhatsApp, and exports.")
    st.code('APP_PASSWORD = "choose-a-strong-password"\nSUPABASE_URL = "https://YOUR-PROJECT.supabase.co"\nSUPABASE_KEY = "YOUR_SERVER_SIDE_KEY"',language="toml")
    st.warning("Never commit credentials or customer exports. WhatsApp is click-to-chat only; official automation requires Meta WhatsApp Cloud API and a webhook.")
