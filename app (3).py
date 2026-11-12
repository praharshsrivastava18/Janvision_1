import os, re, io, pickle, hashlib
from pathlib import Path
import numpy as np
import streamlit as st
import fitz
from rank_bm25 import BM25Okapi
from section2_data import CHAPTERS, POISONS, SECTION_LABELS

st.set_page_config(page_title="Modi Section 2 Explorer", page_icon="☠️", layout="wide")
EMOJI = {"1":"⚖️","2":"🧪","3":"☣️","4":"🔩","5":"🌿","6":"🍃","7":"🐍","8":"💤","9":"🍺","10":"🌀","11":"💨","12":"🍄","A1":"📎"}
CACHE = Path("index_store"); CACHE.mkdir(exist_ok=True)
LABEL_RE = re.compile(r"^\s*(" + "|".join(re.escape(l) for l in sorted(SECTION_LABELS, key=len, reverse=True)) + r")\s*[:.\-]?\s*$", re.I)

# ---------------- sidebar ----------------
st.sidebar.title("Settings")
pdf_path = st.sidebar.text_input("Book PDF path (Section 2)", r"data/modi_section2.pdf")
offset = st.sidebar.number_input("PAGE_OFFSET (pdf page minus printed page)", value=0, step=1)
api_key = st.sidebar.text_input("Anthropic API key (optional)", type="password")
use_ocr = st.sidebar.checkbox("PDF is scanned (use OCR)", value=False)
build = st.sidebar.button("Build / load index", type="primary")
st.sidebar.caption("Without the PDF index you can still browse chapters and topics.")
st.sidebar.caption("Icons are generic emoji; no publisher logos are used.")

# ---------------- indexing ----------------
def page_text(doc, book_page, ocr):
    i = book_page + offset - 1
    if not (0 <= i < len(doc)): return ""
    t = doc[i].get_text("text")
    if (ocr or len(t.strip()) < 40):
        try:
            import pytesseract; from PIL import Image
            t = pytesseract.image_to_string(Image.open(io.BytesIO(doc[i].get_pixmap(dpi=250).tobytes("png"))))
        except Exception:
            pass
    return t

def find_poison(line, ch):
    l = line.strip().lower()
    if len(l) < 4 or len(l) > 140 or len(l.split()) > 14: return None
    for n in POISONS.get(ch, []):
        if n.lower() in l: return n
    return None

def make_chunks(doc, ocr, prog):
    chunks, total = [], sum(b-a+1 for a,b in (v["pages"] for v in CHAPTERS.values())); done = 0
    for ch, meta in CHAPTERS.items():
        a, b = meta["pages"]; poison, section, buf, pages = None, "General", [], set()
        def flush():
            nonlocal buf, pages
            text = " ".join(buf).strip()
            if len(text) > 80:
                for s in range(0, len(text), 1250):
                    chunks.append(dict(chapter=str(ch), title=meta["title"], poison=poison or "General",
                                       section=section, pages=sorted(pages), text=text[s:s+1400]))
            buf, pages = [], set()
        for p in range(a, b+1):
            for line in page_text(doc, p, ocr).splitlines():
                if not line.strip(): continue
                m = LABEL_RE.match(line)
                if m: flush(); section = m.group(1).title(); continue
                pn = find_poison(line, ch)
                if pn and pn != poison: flush(); poison, section = pn, "General"
                buf.append(line.strip()); pages.add(p)
            done += 1; prog.progress(done/total)
        flush()
    return chunks

@st.cache_resource
def get_embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("BAAI/bge-small-en-v1.5")

def build_index(path, ocr):
    doc = fitz.open(path); bar = st.sidebar.progress(0.0, text="Reading pages")
    chunks = make_chunks(doc, ocr, bar)
    texts = [f"{c['title']} | {c['poison']} | {c['section']}\n{c['text']}" for c in chunks]
    emb = get_embedder().encode(texts, batch_size=32, normalize_embeddings=True).astype("float32")
    pickle.dump((chunks, emb), open(CACHE/"s2.pkl", "wb")); return chunks, emb

if build:
    if not os.path.exists(pdf_path): st.sidebar.error("PDF not found")
    else:
        st.session_state["idx"] = build_index(pdf_path, use_ocr); st.sidebar.success(f"{len(st.session_state['idx'][0])} chunks indexed")
elif "idx" not in st.session_state and (CACHE/"s2.pkl").exists():
    st.session_state["idx"] = pickle.load(open(CACHE/"s2.pkl", "rb"))
IDX = st.session_state.get("idx")

tok = lambda s: re.findall(r"[a-z0-9]+", s.lower())
@st.cache_resource
def get_bm25(n, key): return BM25Okapi([tok(f"{c['poison']} {c['section']} {c['text']}") for c in IDX[0]])

def search(q, k=6, ch=None, poison=None):
    chunks, emb = IDX; bm = get_bm25(len(chunks), hash(chunks[0]["text"]))
    dense = np.argsort(-(emb @ get_embedder().encode([q], normalize_embeddings=True)[0]))[:60]
    sparse = np.argsort(-bm.get_scores(tok(q)))[:60]
    sc = {}
    for r, i in enumerate(dense): sc[int(i)] = sc.get(int(i), 0) + 1/(60+r)
    for r, i in enumerate(sparse): sc[int(i)] = sc.get(int(i), 0) + 1/(60+r)
    out = []
    for i, _ in sorted(sc.items(), key=lambda x: -x[1]):
        c = chunks[i]
        if ch and c["chapter"] != ch: continue
        if poison and poison != c["poison"]: continue
        out.append(c)
        if len(out) == k: break
    return out

SYSTEM = ("Answer ONLY from the supplied excerpts of Modi's Medical Jurisprudence and Toxicology (Section 2), in plain English. "
          "Structure by Symptoms / Fatal Dose / Fatal Period / Treatment / Post-mortem Appearance / Medico-legal Points where relevant. "
          "Cite printed page numbers like (p. 320). If the excerpts lack the answer, say so. Study and forensic reference only, not clinical advice.")
def cite(c): return f"Ch {c['chapter']} · {c['poison']} · {c['section']} · pp. {c['pages'][0]}–{c['pages'][-1]}"

def answer(q, hits):
    if api_key or os.getenv("ANTHROPIC_API_KEY"):
        import anthropic
        ctx = "\n\n".join(f"[{cite(c)}]\n{c['text']}" for c in hits)
        r = anthropic.Anthropic(api_key=api_key or None).messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5"), max_tokens=1200, system=SYSTEM,
            messages=[{"role": "user", "content": f"Excerpts:\n{ctx}\n\nQuestion: {q}"}])
        return r.content[0].text
    return "\n\n".join(f"**{c['poison']} – {c['section']}** (pp. {c['pages'][0]}–{c['pages'][-1]})\n\n{c['text']}" for c in hits[:3])

# ---------------- main page ----------------
st.title("☠️ Medical Jurisprudence & Toxicology: Section 2 Explorer")
st.caption("Toxicology · Chapters 1–12 + Appendix 1 · for study and forensic reference only, not clinical advice. "
           "Poisoning emergency in India: AIIMS National Poisons Information Centre 1800-116-117.")
tab1, tab2 = st.tabs(["📚 Browse chapters", "💬 Ask the book"])

with tab1:
    st.subheader("Select a chapter")
    cols = st.columns(3)
    for n, (k, v) in enumerate(CHAPTERS.items()):
        label = f"{EMOJI.get(str(k),'📘')} {k}. {v['title']}" if k != "A1" else f"📎 {v['title']}"
        if cols[n % 3].button(label, key=f"ch{k}", use_container_width=True): st.session_state["ch"] = str(k)
    ck = st.session_state.get("ch")
    if ck:
        key = int(ck) if ck.isdigit() else ck; meta = CHAPTERS[key]
        st.divider(); st.header(f"{ck}. {meta['title']}"); st.caption(f"Printed pages {meta['pages'][0]}–{meta['pages'][1]}")
        names = POISONS.get(key, [])
        if IDX:
            found = sorted({c["poison"] for c in IDX[0] if c["chapter"] == ck})
            names = [n for n in found if n != "General"] or names
        pick = st.selectbox("Poison / topic", ["(all)"] + names)
        if IDX:
            for c in [c for c in IDX[0] if c["chapter"] == ck and (pick == "(all)" or c["poison"] == pick)][:40]:
                with st.expander(cite(c)): st.write(c["text"])
        else:
            st.info("Build the index in the sidebar to read the book text for this chapter.")
            st.write("Topics in this chapter: " + ", ".join(names))

with tab2:
    if not IDX:
        st.warning("Click 'Build / load index' in the sidebar first.")
    else:
        c1, c2 = st.columns(2)
        fch = c1.selectbox("Limit to chapter", ["(all)"] + [str(k) for k in CHAPTERS])
        fpo = c2.selectbox("Limit to poison", ["(all)"] + sorted({c["poison"] for c in IDX[0] if fch in ("(all)", c["chapter"])}))
        hist = st.session_state.setdefault("hist", [])
        for role, msg in hist: st.chat_message(role).markdown(msg)
        q = st.chat_input("e.g. Post-mortem appearance in aflatoxin poisoning")
        if q:
            st.chat_message("user").markdown(q)
            hits = search(q, 6, None if fch == "(all)" else fch, None if fpo == "(all)" else fpo)
            a = answer(q, hits) if hits else "No matching passage found. Try removing the filters."
            srcs = "\n".join(f"- {cite(c)}" for c in hits)
            full = a + ("\n\n**Sources**\n" + srcs if hits else "")
            st.chat_message("assistant").markdown(full); hist += [("user", q), ("assistant", full)]
