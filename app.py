"""BEI Paper 2 reproducible visualisation dashboard v1.1.
Read-only: displays model-locked results, never re-estimates or chooses a specification.
"""
import csv
import io
import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
from analysis import read_csv, filtered_pairs, counts, group_counts, followup_counts

st.set_page_config(page_title="BEI • Profit–Loss Transitions", page_icon="📊", layout="wide")
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
TEAL, CORAL, NAVY, GREY = "#0F8B76", "#D57545", "#19395C", "#7B8794"

@st.cache_data(show_spinner=False)
def load_data():
    o={
        "pairs": read_csv("Paper2_TahapA_v0_3_Pasangan.csv"),
        "followup": read_csv("Paper2_TahapA_v0_3_Followup.csv"),
        "sens": read_csv("Paper2_TahapA_v0_3_Sensitivitas.csv"),
        "flags": read_csv("Paper2_TahapA_v0_3_FlagRingkas.csv"),
        "or": read_csv("Table_Regression_Core_All.csv"),
        "ame": read_csv("Table_Average_Marginal_Effects.csv"),
        "diagnostics": read_csv("Table_Model_Diagnostics_and_Robustness.csv"),
    }
    with (DATA / "Independent_Descriptive_and_QA.json").open(encoding="utf-8") as f:
        o["qa"]=json.load(f)
    with (DATA / "Paper2_TahapA_v0_3_Ringkasan.json").open(encoding="utf-8") as f:
        o["audit"]=json.load(f)
    return o


def percent(x):
    return "—" if x is None else f"{100*x:.2f}%"

def fmt_n(x):
    return f"{x:,}".replace(",", ".")

def graph_layout(fig,height=425):
    fig.update_layout(height=height,margin=dict(l=12,r=10,t=50,b=30),
                      paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Arial",size=12),legend=dict(orientation="h",y=-0.22),
                      hovermode="closest")
    return fig

def csv_data(rows):
    if not rows: return b""
    sio=io.StringIO()
    writer=csv.DictWriter(sio,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    return ("\ufeff"+sio.getvalue()).encode("utf-8")

def select_model(rows,risk,scenario="entity_main"):
    return [r for r in rows if r["Risk"]==risk and r["Scenario"]==scenario]

def float_or_none(x):
    try: return float(x) if str(x).strip() else None
    except (ValueError,TypeError): return None

D=load_data()
source=D["pairs"]
pre=counts(source)
assert (pre["pairs"],pre["rec"],pre["onset"],pre["rr"],pre["lp"],pre["zero"]) == (4469,426,388,858,2790,7), "Tahap A audit incompatible"
entity=counts([p for p in source if p["Code"]!="GOTOM"])
assert (entity["pairs"],entity["firms"],entity["rec"],entity["rr"],entity["onset"],entity["lp"]) == (4463,761,425,855,388,2788), "Entity baseline incompatible"

sectors=sorted({r["Sector"] for r in source})
quarters=sorted({r["Quarter"] for r in source})
st.sidebar.title("Filter deskriptif")
sel_sectors=st.sidebar.multiselect("Sektor",sectors,default=sectors)
sel_quarters=st.sidebar.multiselect("Kuartal akhir transisi",quarters,default=quarters)
entity_mode=st.sidebar.checkbox("Unit emiten: kecualikan GOTOM",value=True,help="Model utama mengikuti definisi satu emiten ekonomi dan menyisihkan kelas saham GOTOM.")
selected=filtered_pairs(source,set(sel_sectors),set(sel_quarters),exclude_gotom=entity_mode)
C=counts(selected)
full_entity=(len(sel_sectors)==len(sectors) and len(sel_quarters)==len(quarters) and entity_mode)

st.sidebar.divider()
xlsx=DATA/"Paper2_Results_Tables_Printable_v1_0.xlsx"
st.sidebar.download_button("📗 Excel hasil model (baseline)",data=xlsx.read_bytes(),file_name=xlsx.name,
       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
st.sidebar.download_button("⬇️ CSV pasangan terfilter",data=csv_data(selected),file_name="Paper2_Pasangan_Terfilter.csv",
       mime="text/csv",disabled=not selected,use_container_width=True)
st.sidebar.download_button("⬇️ CSV koefisien lengkap",data=csv_data(D["or"]),file_name="Paper2_Semua_Koefisien.csv",
       mime="text/csv",use_container_width=True)
st.sidebar.caption("Excel hasil model adalah baseline terkunci dan TIDAK berubah ketika filter deskriptif diubah.")

st.title("Quarterly Profit–Loss Transition Dashboard")
st.caption("Paper ke-2 · BEI nonfinancial issuers · 2024Q3–2026Q3 source statements / 2025Q1–2026Q3 transition endpoints")
st.warning("POST-EXPLORATORY · P-value nominal, asosiasi nonkausal. Profit for Period diperlakukan sebagai YTD, tetapi konvensi sumber belum diverifikasi independen pada seluruh laporan.")
if not full_entity:
    st.info("Filter deskriptif atau unit ticker aktif. Model logit/AME dan CI baseline tidak dihitung ulang untuk subset ini; panel ekonometrika selalu menunjukkan hasil issuer-level Model Lock v1.0.")

if not selected:
    st.error("Tidak ada pasangan untuk filter saat ini. Pilih ulang sektor/kuartal.")
    st.stop()

T1,T2,T3,T4,T5=st.tabs(["🏠 Ringkasan","📊 Kuartal & sektor","🔁 Ketahanan recovery","🔎 Audit & sensitivitas","📐 Model ekonometrika"])
with T1:
    a,b,c,d=st.columns(4)
    a.metric("Pasangan teramati",fmt_n(C["pairs"]))
    b.metric("Emiten/kode teramati",fmt_n(C["firms"]))
    c.metric("Rugi → Laba",fmt_n(C["rec"]))
    d.metric("Laba → Rugi",fmt_n(C["onset"]))
    a,b=st.columns(2)
    a.metric("Recovery / dari risk set rugi",percent(C["rec_rate"]))
    a.caption(f"Penyebut={fmt_n(C['at_risk_loss'])}; outcome nol dikecualikan")
    b.metric("Loss onset / dari risk set laba",percent(C["onset_rate"]))
    b.caption(f"Penyebut={fmt_n(C['at_risk_profit'])}; outcome nol dikecualikan")
    f=go.Figure(go.Sankey(arrangement="snap",
        node=dict(label=["Rugi t−1","Laba t−1","Rugi t","Laba t"],pad=27,thickness=24,color=[CORAL,TEAL,CORAL,TEAL]),
        link=dict(source=[0,0,1,1],target=[2,3,2,3],value=[C["rr"],C["rec"],C["onset"],C["lp"]],
                  color=["rgba(213,117,69,.45)","rgba(15,139,118,.55)","rgba(213,117,69,.55)","rgba(15,139,118,.45)"],
                  label=["Tetap rugi","Pemulihan","Masuk rugi","Tetap laba"])))
    f.update_layout(title="Alur status laba akuntansi (bukan financial distress)")
    st.plotly_chart(graph_layout(f),use_container_width=True)
    st.caption(f"Terdapat {C['zero']} pasangan melibatkan laba nol; tidak ditampilkan dalam alur dua status.")
    if full_entity:
        bs=D["qa"]["bootstrap_entity"]
        st.info(f"Issuer-cluster bootstrap 95% CI baseline: recovery {percent(bs['CI95_recovery_rate'][0])}–{percent(bs['CI95_recovery_rate'][1])}; loss onset {percent(bs['CI95_onset_rate'][0])}–{percent(bs['CI95_onset_rate'][1])} (B=2.000).")

with T2:
    st.subheader("Dinamika antar-kuartal")
    q=group_counts(selected,"Quarter")
    qlabels=list(q)
    fig=go.Figure()
    for term,label,color in [("rec_rate","Rugi → Laba",TEAL),("onset_rate","Laba → Rugi",CORAL)]:
        fig.add_trace(go.Scatter(x=qlabels,y=[100*q[t][term] if q[t][term] is not None else None for t in qlabels],
                 mode="lines+markers",name=label,line=dict(width=3,color=color),marker=dict(size=9)))
    fig.update_layout(title="Probabilitas kondisional menurut kuartal",yaxis_title="Persen (%)")
    st.plotly_chart(graph_layout(fig),use_container_width=True)
    st.subheader("Perbandingan 10 sektor")
    sector=group_counts(selected,"Sector")
    names=list(sector)
    fig=go.Figure()
    for term,label,color in [("rec_rate","Recovery",TEAL),("onset_rate","Loss onset",CORAL)]:
        fig.add_trace(go.Bar(y=names,x=[100*sector[t][term] if sector[t][term] is not None else None for t in names],
                 name=label,orientation="h",marker_color=color))
    fig.update_layout(barmode="group",title="Tingkat transisi dan kelompok risiko berbeda",xaxis_title="Persen (%)",yaxis=dict(autorange="reversed"))
    st.plotly_chart(graph_layout(fig,560),use_container_width=True)
    st.caption("Perbandingan sektor bersifat deskriptif, bukan hasil tes bersama perbedaan kemiringan.")
    st.dataframe([{"Kuartal":k,"Pairs":v["pairs"],"Recovery":v["rec"],"Rate recovery":percent(v["rec_rate"]),
                   "Loss onset":v["onset"],"Rate onset":percent(v["onset_rate"])} for k,v in q.items()],hide_index=True,use_container_width=True)

with T3:
    st.subheader("Kelanjutan satu kuartal sesudah pemulihan")
    F=followup_counts(selected,D["followup"])
    a,b,c,d=st.columns(4)
    a.metric("Pemulihan",F["recovery"]);b.metric("Follow-up tersedia",F["observed"])
    c.metric("Tetap laba",F["still_profit"]);d.metric("Tanpa follow-up",F["missing"])
    fig=go.Figure(go.Bar(x=["Tetap laba","Kembali rugi","Nol","Tidak teramati"],
             y=[F["still_profit"],F["relapse"],F["zero"],F["missing"]],
             marker_color=[TEAL,CORAL,GREY,"#BEC7D0"],text=[F["still_profit"],F["relapse"],F["zero"],F["missing"]],textposition="outside"))
    fig.update_layout(title="Status pada kuartal berikutnya",yaxis_title="Kejadian",showlegend=False)
    st.plotly_chart(graph_layout(fig),use_container_width=True)
    if F["observed"]:
        st.info(f"Tetap laba di antara follow-up yang teramati: {percent(F['still_profit']/F['observed'])}. Tidak teramati tidak boleh diklasifikasikan sebagai gagal pulih.")
    st.caption("Statistik follow-up mengikuti filter pada kejadian pemulihan, bukan sekadar tanggal follow-up. Periode pengamatan pendek.")

with T4:
    st.subheader("Audit sumber dan variasi definisi deskriptif")
    st.caption("Grafik berikut merupakan sensitivitas ticker-level Tahap A v0.3, bukan estimasi model utama dan tidak mengikuti filter sidebar.")
    fig=go.Figure()
    vals=D["sens"]
    for key,label,color in [("Recovery_rate","Recovery",TEAL),("Loss_onset_rate","Loss onset",CORAL)]:
        fig.add_trace(go.Scatter(y=[z["Scenario"] for z in vals],x=[100*float_or_none(z[key]) if float_or_none(z[key]) is not None else None for z in vals],
                                 mode="markers",name=label,marker=dict(size=10,color=color)))
    fig.update_layout(title="Sensitivitas tingkat transisi terhadap pemilihan data",xaxis_title="Persen (%)",yaxis=dict(autorange="reversed"))
    st.plotly_chart(graph_layout(fig,600),use_container_width=True)
    st.dataframe([{"Flag":r["Flag"],"Baris":int(r["Flagged_Rows"]),"Ticker":int(r["Distinct_Tickers"])} for r in D["flags"]],
                 hide_index=True,use_container_width=True)
    st.warning("Audit menunjukkan perbedaan vintage, Q4 tahunan/interim, nilai dekat nol, dan laporan tidak lengkap. Flag adalah peringatan, bukan bukti angka sumber salah.")

with T5:
    st.subheader("Model Lock v1.0 — hasil estimasi issuer-level")
    st.info("Model di tab ini STANDALONE dan tidak merespons filter deskriptif. Standardisasi per risk set; logit dengan kontrol sektor/kuartal, SE cluster issuer. Jangan membandingkan OR dua risk set sebagai efek setara.")
    risk_label=st.radio("Risk set model",["Rugi → Laba (Recovery)","Laba → Rugi (Loss Onset)"],horizontal=True)
    risk="Recovery" if risk_label.startswith("Rugi") else "Loss_Onset"
    diag=select_model(D["diagnostics"],risk)
    base=[r for r in diag if r["Scenario"]=="entity_main"][0]
    a,b,c,d=st.columns(4)
    a.metric("Pasangan model",fmt_n(int(base["N"])))
    b.metric("Emiten",fmt_n(int(base["Firms"])))
    c.metric("Kejadian",fmt_n(int(base["Events"])))
    d.metric("McFadden pseudo-R²",f"{float(base['McFadden_Pseudo_R2']):.4f}")
    core_terms=["Loss_or_profit_intensity_z","Ln_assets_z","DTA_z"]
    labels={"Loss_or_profit_intensity_z":"Initial absolute profit/loss intensity","Ln_assets_z":"Firm size: ln(assets)","DTA_z":"Liabilities/assets"}
    R={r["Term"]:r for r in select_model(D["or"],risk) if r["Term"] in core_terms}
    A={r["Term"]:r for r in select_model(D["ame"],risk) if r["Term"] in core_terms}
    st.markdown("**Odds ratios — model utama**")
    st.dataframe([{"Kovariat t−1":labels[t],"OR":round(float(R[t]["Odds_Ratio"]),3),
                 "95% CI":f"[{float(R[t]['OR_CI95_lower']):.3f}, {float(R[t]['OR_CI95_upper']):.3f}]",
                 "p nominal":round(float(R[t]["P_value"]),5)} for t in core_terms],hide_index=True,use_container_width=True)
    vals=[100*float(A[t]["AME_per_1SD"]) for t in core_terms]
    los=[100*float(A[t]["CI95_lower"]) for t in core_terms]
    his=[100*float(A[t]["CI95_upper"]) for t in core_terms]
    ef=go.Figure(go.Scatter(x=vals,y=[labels[t] for t in core_terms],mode="markers",marker=dict(color=NAVY,size=12),
              error_x=dict(type="data",symmetric=False,array=[hi-x for x,hi in zip(vals,his)],arrayminus=[x-lo for x,lo in zip(vals,los)],thickness=2)))
    ef.add_vline(x=0,line_color=GREY,line_dash="dash")
    ef.update_layout(title="Average marginal effects (pp per 1 risk-set SD)",xaxis_title="Percentage points",yaxis=dict(autorange="reversed"))
    st.plotly_chart(graph_layout(ef,385),use_container_width=True)
    st.caption("95% CI: delta-method dengan covariance issuer-cluster. AME bukan efek kausal, dan interval mengasumsikan model sebagaimana dispesifikasikan.")
    st.markdown("**Seluruh spesifikasi sensitivitas (tanpa pemilihan berdasar p-value)**")
    scens=[r for r in diag if r["Scenario"]!="entity_main"]
    tbl=[]
    for row in scens:
        scenario=row["Scenario"]
        terms={r["Term"]:r for r in select_model(D["or"],risk,scenario) if r["Term"] in core_terms}
        if not terms:continue
        tbl.append({"Skenario":scenario,"N":int(row["N"]),"Events":int(row["Events"]),"Estimator":row["Estimator"],
                    "OR intensity":round(float(terms["Loss_or_profit_intensity_z"]["Odds_Ratio"]),3) if terms["Loss_or_profit_intensity_z"]["Odds_Ratio"] else "n/a (LPM)",
                    "p intensity":round(float(terms["Loss_or_profit_intensity_z"]["P_value"]),4),
                    "p size":round(float(terms["Ln_assets_z"]["P_value"]),4),
                    "p DTA":round(float(terms["DTA_z"]["P_value"]),4)})
    st.dataframe(tbl,hide_index=True,use_container_width=True)
    st.warning("Recovery-intensity tidak stabil bila Q4-adjacent/outlier/near-zero/2026Q3 diperlakukan berbeda. Pada loss onset, size lebih stabil; DTA dan intensity lemah tanpa winsor. Nilai p tetap eksploratori.")
    st.image(str(ROOT/"figures"/("AME_Recovery.png" if risk=="Recovery" else "AME_Loss_Onset.png")),
             caption="Grafik AME statis hasil replikasi asli, sebagai pembanding plotting interaktif.",use_container_width=True)

st.divider()
st.caption("Replikasi data: Tahap A v0.3; hasil model: Tahap C–E v1.0. Unit utama = economic issuer. Dashboard bersifat read-only dan tidak menjalankan regresi. Tidak ada unggahan data ke server eksternal.")
