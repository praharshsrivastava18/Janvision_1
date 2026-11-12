#!/usr/bin/env python3
"""
NetSec Audit v3: CCNA-aligned network security auditor with digital-forensics integrity.

Runs entirely on a virtual lab (no real devices needed). It:
  * compares a "running" lab state against an approved baseline design
  * runs CCNA-topic security checks (VLAN, trunk, port security, OSPF + auth, routes, ACL, VTY)
  * scores each finding (CVSS-style bands) and maps it to CIS Controls v8 / NIST CSF
  * records every step in a SHA-256 hash-chained evidence log (tamper-evident)
  * exports an HMAC-signed report with a chain-of-custody header

Usage:
  python3 netsec_audit_v3.py audit [--inject a,b] [--examiner NAME]
  python3 netsec_audit_v3.py verify-log
  python3 netsec_audit_v3.py verify-report reports/<file>.json
  python3 netsec_audit_v3.py tamper-demo
  python3 netsec_audit_v3.py list-faults
"""
import argparse, copy, hashlib, hmac, json, os, platform, getpass, sys
from datetime import datetime, timezone

LOG_FILE = "evidence_log.jsonl"
REPORT_DIR = "reports"
KEY_FILE = ".audit_key"
GENESIS = "0" * 64

# ----------------------------------------------------------------------------
# 1. Virtual lab: the approved baseline design
# ----------------------------------------------------------------------------
BASELINE = {
    "R1": {
        "type": "router",
        "ospf": {"area": 0, "auth": "md5", "neighbors": ["R2"]},
        "routes": ["10.10.0.0/24", "10.20.0.0/24", "10.30.0.0/24"],
        "acls": {"BLOCK_GUEST": ["deny 10.30.0.0/24 -> 10.10.0.0/24", "permit any -> any"]},
        "vty": {"transport": "ssh"},
    },
    "R2": {
        "type": "router",
        "ospf": {"area": 0, "auth": "md5", "neighbors": ["R1", "R3"]},
        "routes": ["10.10.0.0/24", "10.20.0.0/24", "10.30.0.0/24"],
        "acls": {},
        "vty": {"transport": "ssh"},
    },
    "R3": {
        "type": "router",
        "ospf": {"area": 0, "auth": "md5", "neighbors": ["R2"]},
        "routes": ["10.10.0.0/24", "10.20.0.0/24", "10.30.0.0/24"],
        "acls": {},
        "vty": {"transport": "ssh"},
    },
    "SW1": {
        "type": "switch",
        "vlans": {10: "STAFF", 20: "SERVERS", 30: "GUEST", 99: "NATIVE"},
        "trunks": {"Gi0/1": {"allowed": [10, 20, 30, 99], "native": 99}},
        "ports": {
            "Fa0/1": {"vlan": 10, "psec": {"enabled": True, "max": 2, "violation": "shutdown"}},
            "Fa0/2": {"vlan": 20, "psec": {"enabled": True, "max": 1, "violation": "shutdown"}},
            "Fa0/3": {"vlan": 30, "psec": {"enabled": True, "max": 1, "violation": "restrict"}},
        },
        "vty": {"transport": "ssh"},
    },
}

# ----------------------------------------------------------------------------
# 2. Fault injections (simulated misconfigurations / attacks)
# ----------------------------------------------------------------------------
def f_rogue_neighbor(s): s["R2"]["ospf"]["neighbors"].append("R-ROGUE")
def f_ospf_auth_off(s): s["R2"]["ospf"]["auth"] = "none"
def f_extra_vlan(s): s["SW1"]["vlans"][666] = "BACKDOOR"
def f_vlan_renamed(s): s["SW1"]["vlans"][20] = "SRV-TEMP"
def f_native_changed(s): s["SW1"]["trunks"]["Gi0/1"]["native"] = 1
def f_trunk_missing(s): s["SW1"]["trunks"]["Gi0/1"]["allowed"].remove(20)
def f_psec_off(s): s["SW1"]["ports"]["Fa0/2"]["psec"]["enabled"] = False
def f_acl_any(s): s["R1"]["acls"]["BLOCK_GUEST"] = ["permit any -> any"]
def f_route_inject(s): s["R3"]["routes"].append("0.0.0.0/0")
def f_route_lost(s): s["R3"]["routes"].remove("10.10.0.0/24")
def f_telnet(s): s["R1"]["vty"]["transport"] = "telnet"
def f_adjacency_down(s): s["R1"]["ospf"]["neighbors"].remove("R2")

FAULTS = {
    "rogue_neighbor": (f_rogue_neighbor, "Unapproved OSPF neighbor appears on R2"),
    "ospf_auth_off": (f_ospf_auth_off, "OSPF authentication disabled on R2"),
    "extra_vlan": (f_extra_vlan, "Unapproved VLAN 666 created on SW1"),
    "vlan_renamed": (f_vlan_renamed, "VLAN 20 renamed on SW1"),
    "native_changed": (f_native_changed, "Trunk native VLAN reset to 1 (VLAN hopping risk)"),
    "trunk_missing": (f_trunk_missing, "VLAN 20 pruned from trunk"),
    "psec_off": (f_psec_off, "Port security disabled on Fa0/2"),
    "acl_any": (f_acl_any, "Guest-isolation ACL replaced with permit any"),
    "route_inject": (f_route_inject, "Default route injected on R3"),
    "route_lost": (f_route_lost, "R3 loses route to 10.10.0.0/24"),
    "telnet": (f_telnet, "R1 VTY allows cleartext Telnet"),
    "adjacency_down": (f_adjacency_down, "R1-R2 OSPF adjacency down"),
}

# ----------------------------------------------------------------------------
# 3. Severity and framework mapping
# ----------------------------------------------------------------------------
# CVSS-style bands (heuristic scores, not official CVSS vectors).
SEVERITY_SCORE = {"CRITICAL": 9.0, "HIGH": 7.5, "MEDIUM": 5.0, "LOW": 2.5, "INFO": 0.0}

FRAMEWORK = {
    "VLAN": ("CIS 4.1 Secure Configuration", "NIST CSF PR.IP-1"),
    "TRUNK": ("CIS 4.1 Secure Configuration", "NIST CSF PR.PT-4"),
    "PSEC": ("CIS 1.2 Address Unauthorized Assets", "NIST CSF PR.AC-5"),
    "OSPF-NBR": ("CIS 1.2 Address Unauthorized Assets", "NIST CSF DE.CM-7"),
    "OSPF-AUTH": ("CIS 3.10 Encrypt Sensitive Data in Transit", "NIST CSF PR.DS-2"),
    "ROUTE": ("CIS 13.3 Network Intrusion Detection", "NIST CSF DE.AE-1"),
    "ACL": ("CIS 4.4 Implement Firewall on Servers / 13.4 Traffic Filtering", "NIST CSF PR.AC-5"),
    "VTY": ("CIS 4.6 Securely Manage Enterprise Assets", "NIST CSF PR.AC-3"),
    "CONN": ("CIS 12.2 Secure Network Architecture", "NIST CSF DE.CM-1"),
}

def finding(check, device, title, severity, detail, status="FAIL"):
    cis, nist = FRAMEWORK[check]
    return {"check": check, "device": device, "title": title, "status": status,
            "severity": severity, "score": SEVERITY_SCORE[severity],
            "detail": detail, "cis": cis, "nist": nist}

def ok(check, device, title):
    return finding(check, device, title, "INFO", "Matches approved design", "PASS")

# ----------------------------------------------------------------------------
# 4. Checks
# ----------------------------------------------------------------------------
def check_vlans(base, cur):
    out, b, c = [], base["SW1"]["vlans"], cur["SW1"]["vlans"]
    for vid, name in b.items():
        if vid not in c:
            out.append(finding("VLAN", "SW1", f"VLAN {vid} missing", "HIGH", f"Expected {name}"))
        elif c[vid] != name:
            out.append(finding("VLAN", "SW1", f"VLAN {vid} renamed", "LOW", f"{name} -> {c[vid]}"))
    for vid, name in c.items():
        if vid not in b:
            out.append(finding("VLAN", "SW1", f"Unapproved VLAN {vid}", "MEDIUM", f"'{name}' not in design"))
    return out or [ok("VLAN", "SW1", "VLAN database matches design")]

def check_trunks(base, cur):
    out = []
    for port, bt in base["SW1"]["trunks"].items():
        ct = cur["SW1"]["trunks"].get(port)
        if ct is None:
            out.append(finding("TRUNK", "SW1", f"Trunk {port} missing", "HIGH", "Trunk not present"))
            continue
        if ct["native"] != bt["native"]:
            out.append(finding("TRUNK", "SW1", f"Native VLAN changed on {port}", "MEDIUM",
                               f"{bt['native']} -> {ct['native']} (802.1Q double-tagging / VLAN hopping risk)"))
        miss = sorted(set(bt["allowed"]) - set(ct["allowed"]))
        if miss:
            out.append(finding("TRUNK", "SW1", f"VLANs pruned from {port}", "MEDIUM", f"Missing: {miss}"))
    return out or [ok("TRUNK", "SW1", "802.1Q trunks match design")]

def check_psec(base, cur):
    out = []
    for port, bp in base["SW1"]["ports"].items():
        cp = cur["SW1"]["ports"][port]["psec"]
        if not cp["enabled"]:
            out.append(finding("PSEC", "SW1", f"Port security off on {port}", "HIGH",
                               "MAC flooding / unauthorized device risk"))
        elif cp != bp["psec"]:
            out.append(finding("PSEC", "SW1", f"Port security drift on {port}", "MEDIUM",
                               f"{bp['psec']} -> {cp}"))
    return out or [ok("PSEC", "SW1", "Port security matches design")]

def check_ospf(base, cur):
    out = []
    for dev, bd in base.items():
        if bd["type"] != "router":
            continue
        bo, co = bd["ospf"], cur[dev]["ospf"]
        rogue = [n for n in co["neighbors"] if n not in bo["neighbors"]]
        down = [n for n in bo["neighbors"] if n not in co["neighbors"]]
        for n in rogue:
            out.append(finding("OSPF-NBR", dev, f"Rogue OSPF neighbor {n}", "CRITICAL",
                               "Unapproved router in area; possible route injection / MITM"))
        for n in down:
            out.append(finding("OSPF-NBR", dev, f"OSPF adjacency to {n} down", "HIGH", "Expected neighbor absent"))
        if co["auth"] != bo["auth"]:
            out.append(finding("OSPF-AUTH", dev, "OSPF authentication disabled", "HIGH",
                               f"Expected {bo['auth']}, found {co['auth']}; routing updates can be forged"))
    return out or [ok("OSPF-NBR", "ALL", "OSPF neighbors and authentication match design")]

def check_routes(base, cur):
    out = []
    for dev, bd in base.items():
        if bd["type"] != "router":
            continue
        b, c = set(bd["routes"]), set(cur[dev]["routes"])
        for r in sorted(c - b):
            sev = "CRITICAL" if r == "0.0.0.0/0" else "HIGH"
            out.append(finding("ROUTE", dev, f"Unexpected route {r}", sev, "Not in approved routing table"))
        for r in sorted(b - c):
            out.append(finding("ROUTE", dev, f"Missing route {r}", "MEDIUM", "Expected route absent"))
    return out or [ok("ROUTE", "ALL", "Routing tables match design")]

def check_acls(base, cur):
    out = []
    for dev, bd in base.items():
        for name, rules in bd.get("acls", {}).items():
            cr = cur[dev]["acls"].get(name)
            if cr is None:
                out.append(finding("ACL", dev, f"ACL {name} missing", "HIGH", "Filtering not applied"))
            elif cr != rules:
                bypass = "deny" not in " ".join(cr)
                out.append(finding("ACL", dev, f"ACL {name} modified",
                                   "CRITICAL" if bypass else "MEDIUM",
                                   "All deny rules removed (segmentation bypass)" if bypass else "Rules differ from design"))
    return out or [ok("ACL", "R1", "ACLs match design")]

def check_vty(base, cur):
    out = []
    for dev in base:
        if cur[dev]["vty"]["transport"] != base[dev]["vty"]["transport"]:
            out.append(finding("VTY", dev, "Cleartext management (Telnet) enabled", "HIGH",
                               "Credentials exposed on the wire; require SSH"))
    return out or [ok("VTY", "ALL", "Management access is SSH-only")]

def check_connectivity(base, cur):
    """Simulated reachability: a LAN is reachable from a router only if the route exists
    and the router has at least one OSPF neighbor."""
    out = []
    for dev, bd in base.items():
        if bd["type"] != "router":
            continue
        for net in bd["routes"]:
            if net not in cur[dev]["routes"] or not cur[dev]["ospf"]["neighbors"]:
                out.append(finding("CONN", dev, f"{dev} cannot reach {net}", "HIGH", "Simulated ping failed"))
    return out or [ok("CONN", "ALL", "All LAN reachability tests pass")]

CHECKS = [check_vlans, check_trunks, check_psec, check_ospf, check_routes,
          check_acls, check_vty, check_connectivity]

# ----------------------------------------------------------------------------
# 5. Forensic integrity: hashing, chained log, signing
# ----------------------------------------------------------------------------
def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)

def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def log_entries():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE) as f:
        return [json.loads(l) for l in f if l.strip()]

def append_log(event, data):
    entries = log_entries()
    prev = entries[-1]["hash"] if entries else GENESIS
    entry = {"idx": len(entries), "ts": now(), "event": event, "data": data, "prev": prev}
    entry["hash"] = sha256(prev + canon(entry))
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry["hash"]

def verify_log():
    prev = GENESIS
    for e in log_entries():
        body = {k: v for k, v in e.items() if k != "hash"}
        if e["prev"] != prev:
            return False, f"Chain broken at entry {e['idx']}: previous-hash link does not match"
        if sha256(prev + canon(body)) != e["hash"]:
            return False, f"Entry {e['idx']} was modified: stored hash does not match its content"
        prev = e["hash"]
    return True, f"Chain intact: {len(log_entries())} entries, head {prev[:16]}..."

def get_key():
    k = os.environ.get("AUDIT_KEY")
    if k:
        return k.encode()
    if not os.path.exists(KEY_FILE):
        with open(KEY_FILE, "wb") as f:
            f.write(os.urandom(32).hex().encode())
        os.chmod(KEY_FILE, 0o600)
    with open(KEY_FILE, "rb") as f:
        return f.read().strip()

def sign(payload):
    return hmac.new(get_key(), canon(payload).encode(), hashlib.sha256).hexdigest()

# ----------------------------------------------------------------------------
# 6. Audit workflow and report
# ----------------------------------------------------------------------------
def run_audit(inject, examiner):
    state = copy.deepcopy(BASELINE)
    append_log("audit_started", {"examiner": examiner, "injected": inject})
    for name in inject:
        FAULTS[name][0](state)
        append_log("fault_injected", {"fault": name})
    base_hash, state_hash = sha256(canon(BASELINE)), sha256(canon(state))
    append_log("state_captured", {"baseline_sha256": base_hash, "state_sha256": state_hash,
                                  "per_device": {d: sha256(canon(v)) for d, v in state.items()}})
    findings = []
    for chk in CHECKS:
        res = chk(BASELINE, state)
        findings += res
        append_log("check_run", {"check": chk.__name__,
                                 "fails": sum(1 for r in res if r["status"] == "FAIL")})
    order = list(SEVERITY_SCORE)
    findings.sort(key=lambda f: (f["status"] == "PASS", order.index(f["severity"])))
    fails = [f for f in findings if f["status"] == "FAIL"]
    counts = {s: sum(1 for f in fails if f["severity"] == s) for s in order if s != "INFO"}
    risk = round(max([f["score"] for f in fails], default=0.0), 1)
    head = append_log("audit_completed", {"fails": len(fails), "max_score": risk})

    body = {
        "custody": {
            "collected_by": examiner, "host": platform.node(), "os": platform.system(),
            "collected_at_utc": now(), "baseline_sha256": base_hash,
            "network_state_sha256": state_hash, "evidence_chain_head": head,
        },
        "summary": {"checks_run": len(findings), "failed": len(fails),
                    "by_severity": counts, "max_score": risk},
        "findings": findings,
    }
    report = {"body": body, "signature_hmac_sha256": sign(body)}
    os.makedirs(REPORT_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(REPORT_DIR, f"audit_{stamp}.json")
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    with open(path.replace(".json", ".txt"), "w") as f:
        f.write(render_text(report))
    return report, path

def render_text(report):
    b, c, s = report["body"], report["body"]["custody"], report["body"]["summary"]
    L = ["=" * 78, "NETWORK SECURITY AUDIT REPORT (CHAIN-OF-CUSTODY HEADER)", "=" * 78]
    L += [f"Collected by      : {c['collected_by']}", f"Collected at (UTC): {c['collected_at_utc']}",
          f"Host              : {c['host']} ({c['os']})",
          f"Baseline SHA-256  : {c['baseline_sha256']}",
          f"Network state hash: {c['network_state_sha256']}",
          f"Evidence chain head: {c['evidence_chain_head']}",
          f"Report signature  : {report['signature_hmac_sha256']}", ""]
    L += [f"Checks: {s['checks_run']}   Failed: {s['failed']}   Highest score: {s['max_score']}/10",
          "By severity: " + ", ".join(f"{k}={v}" for k, v in s["by_severity"].items()), "",
          "-" * 78]
    for f in b["findings"]:
        L.append(f"[{f['status']}] {f['severity']:<8} {f['score']:>4}  {f['device']:<5} {f['title']}")
        if f["status"] == "FAIL":
            L.append(f"        {f['detail']}")
            L.append(f"        Maps to: {f['cis']} | {f['nist']}")
    return "\n".join(L) + "\n"

def verify_report(path):
    with open(path) as f:
        r = json.load(f)
    return hmac.compare_digest(sign(r["body"]), r["signature_hmac_sha256"])

# ----------------------------------------------------------------------------
# 7. CLI
# ----------------------------------------------------------------------------
def tamper_demo():
    ok_, msg = verify_log()
    print("Before tampering:", msg)
    entries = log_entries()
    if len(entries) < 3:
        print("Run an audit first."); return
    backup = open(LOG_FILE).read()
    entries[2]["data"] = {"forged": True}
    with open(LOG_FILE, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    print("After editing entry 2:", verify_log()[1])
    with open(LOG_FILE, "w") as f:
        f.write(backup)
    print("Log restored:", verify_log()[1])

def demo():
    """One-click demo (used when the script is run with no arguments, e.g. the VS Code Run button)."""
    who = getpass.getuser()
    print("\n##### STEP 1: Audit a healthy network (should all PASS) #####")
    report, path = run_audit([], who)
    print(f"Failed checks: {report['body']['summary']['failed']}   Report saved: {path}")
    print("\n##### STEP 2: Simulate attacks and misconfigurations, then audit again #####")
    report, path = run_audit(["rogue_neighbor", "ospf_auth_off", "telnet", "acl_any", "native_changed"], who)
    print(render_text(report))
    print(f"Report saved: {path} (and a .txt copy)")
    print("\n##### STEP 3: Verify the evidence log and the signed report #####")
    print(("OK  " if verify_log()[0] else "FAIL ") + verify_log()[1])
    print("Report signature valid:", verify_report(path))
    print("\n##### STEP 4: Tamper-detection demo (edit one log entry) #####")
    tamper_demo()
    print("\nDone. Other commands: audit, verify-log, verify-report FILE, tamper-demo, list-faults")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")  # optional: no command = default demo audit
    a = sub.add_parser("audit")
    a.add_argument("--inject", default="", help="comma-separated fault names, or 'all'")
    a.add_argument("--examiner", default=getpass.getuser())
    sub.add_parser("verify-log")
    v = sub.add_parser("verify-report"); v.add_argument("file")
    sub.add_parser("tamper-demo")
    sub.add_parser("list-faults")
    args = ap.parse_args()

    if args.cmd is None:
        demo()
        return

    if args.cmd == "list-faults":
        for k, (_, d) in FAULTS.items():
            print(f"{k:<16} {d}")
    elif args.cmd == "audit":
        inject = list(FAULTS) if args.inject == "all" else [x for x in args.inject.split(",") if x]
        bad = [x for x in inject if x not in FAULTS]
        if bad:
            sys.exit(f"Unknown fault(s): {bad}. Use list-faults.")
        report, path = run_audit(inject, args.examiner)
        print(render_text(report)); print(f"Saved: {path} (+ .txt)")
    elif args.cmd == "verify-log":
        good, msg = verify_log(); print(("OK  " if good else "FAIL ") + msg); sys.exit(0 if good else 1)
    elif args.cmd == "verify-report":
        good = verify_report(args.file)
        print("Signature valid" if good else "SIGNATURE INVALID: report was altered"); sys.exit(0 if good else 1)
    elif args.cmd == "tamper-demo":
        tamper_demo()

if __name__ == "__main__":
    main()
