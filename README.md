# Projects & Study Labs

A collection of my hands-on work as a B.Tech CSE (Cyber Security & Digital Forensics) student at VIT Bhopal University: applied AI and deep learning, security and networking tools, legal-tech prototypes, and daily coding practice for exams.

Most items are single files (a Jupyter notebook, a Java program or a Python script), so each one can be opened and run on its own.

---

## What is in this repository

| Area | Files | One-line summary |
|---|---|---|
| **AI / Deep Learning** | `JanVision_1.ipynb`, `data.yaml` | Keratoconus (eye disease) detection with YOLO |
| **Retrieval-Augmented Generation (RAG)** | `modi_toxicology_rag (4).ipynb`, `app (3).py` | Search and Q&A over a medical jurisprudence textbook |
| **Cyber Law & Digital Forensics** | `CyberLex.ipynb` | Tamper-evident evidence toolkit for advocates |
| **Legal Operations** | `LegalOps-Lite.ipynb`, `LegalOps-Lite_dashboard.html`, `dashboard_latest.html` | Legal workflow prototype with a browser dashboard |
| **Networking & Security** | `netsec_audit_v3 (2).py`, `network_build_checker.ipynb`, `CCNA 200-301 Vol 1 ...` | Network audit and build-check tools, plus CCNA study material |
| **Knowledge Graphs** | `Semantic_Knowledge_Graph_Skill...` | Skill-gap analysis using a knowledge graph and vector profiles |
| **Exam practice: GATE 2027 CSE** | `Day01` to `Day12` Java files, `GATE_2027_CSE_Python_Daily_Pr...` | One small program per GATE topic |
| **Exam practice: RBI Grade A** | `RBI_GradeA_Python_Daily_Project...` | One practical Python project per day |

---

## Projects in detail

### JanVision: keratoconus detection (`JanVision_1.ipynb`, `data.yaml`)
Detects keratoconus from corneal images using a YOLOv11n model. The model reached **95.29% test accuracy** and **99.3% mAP50**. JanVision was an **INNOVIT 2026 Grand Finalist**. `data.yaml` holds the dataset configuration used for training.

**Tech:** Python, PyTorch, Ultralytics YOLO, OpenCV

### Medical Jurisprudence & Toxicology RAG Explorer (`modi_toxicology_rag (4).ipynb`, `app (3).py`)
A study tool that lets you browse a textbook by chapter and ask questions about it. Text is split by book headings, then found again using **BM25 keyword search combined with embedding search**, so answers point back to the right part of the book.

- The notebook builds the index.
- `app (3).py` is the web front end.
- The textbook itself is **not included** in this repository (it is a copyrighted book). Add your own PDF to run it.

**Tech:** Python, PyMuPDF, sentence-transformers, BM25, Streamlit/Gradio

### CyberLex: digital evidence & cyber-law toolkit (`CyberLex.ipynb`)
Built for advocates and law firms handling digital evidence in India.

- **Chain of custody:** a hash-chained log, so any edit to an earlier record is detected.
- **Evidence vault:** stores files with fingerprints.
- **Statute mapper:** links an incident to relevant sections of the BNS, BSA, BNSS and IT Act.
- **Admissibility checklist** and an automatic **case report**.
- Includes tamper-detection demo cells.

**Tech:** Python 3.13, Jupyter (VS Code)

> This is a learning and prototype tool. It is not legal advice, and the statute mappings should be checked by a practising advocate.

### LegalOps-Lite (`LegalOps-Lite.ipynb`, `LegalOps-Lite_dashboard.html`, `dashboard_latest.html`)
A lightweight legal-operations prototype. The notebook produces the data and the HTML files are the dashboard you open in a browser. Open the `.html` file directly, no server needed.

### Network tools (`netsec_audit_v3 (2).py`, `network_build_checker.ipynb`)
Scripts for checking network setups and auditing basic security settings. Use them only on networks you own or have permission to test.

### Skill-Gap Analysis (`Semantic_Knowledge_Graph_Skill...`)
"Semantic Knowledge Graph and Vector-Space Profiling for Automated Industry Skill Gap Analysis". It compares a person's skills with what industry roles ask for and shows the gaps.

---

## Daily practice series

### GATE 2027 CSE, Java (`Day01` to `Day12`)
One short program per core GATE topic, written to see the idea working rather than just read about it.

| Day | Topic | Day | Topic |
|---|---|---|---|
| 01 | Discrete Mathematics | 07 | Algorithms Lab |
| 02 | Linear Algebra & Probability | 08 | OS Scheduling |
| 03 | Digital Logic | 09 | Database Algebra |
| 04 | Data Structures | 10 | Networks |
| 05 | Trees & Heaps | 11 | Theory of Computation |
| 06 | Sorting & Searching | 12 | Compiler / Parser |

### GATE 2027 CSE, Python (`GATE_2027_CSE_Python_Daily_Pr...`)
The same idea in a single Python notebook.

### RBI Grade A, Python (`RBI_GradeA_Python_Daily_Project...`)
One practical Python project per day, following *Python: The Complete Reference*, in preparation for RBI Grade A (September 2027).

---

## How to run

**Notebooks (`.ipynb`)**
```bash
pip install jupyter
jupyter notebook
```
Open the notebook and run the cells from top to bottom. Each notebook lists its own extra libraries in its first cell.

**Python scripts (`.py`)**
```bash
python "netsec_audit_v3 (2).py"
```
For Streamlit apps: `streamlit run "app (3).py"`

**Java programs**
```bash
javac Day01_DiscreteMath.java
java Day01_DiscreteMath
```
Requires JDK 17 or newer.

**Dashboards (`.html`)**
Double-click the file to open it in your browser.

---

## Author

**Praharsh Srivastava**
B.Tech CSE (Cyber Security & Digital Forensics), VIT Bhopal University, expected May 2027

- LinkedIn: [linkedin.com/in/praharsh-srivastava-8a544b28a](https://linkedin.com/in/praharsh-srivastava-8a544b28a)
- GitHub: [github.com/praharshsrivastava18](https://github.com/praharshsrivastava18)
- Email: praharshsrivastava18@gmail.com
