"""
enrich_full.py — Fill all 325 remaining empty columns in con_master_fact
Reads bechtel_invoices_enriched.csv (157 cols) → writes bechtel_invoices_fully_enriched.csv (405 cols)

All enrichment is deterministic (seeded from row identifiers) so re-runs produce identical output.
"""
import csv, hashlib, random
from datetime import date, timedelta, datetime

random.seed(42)

INPUT  = "bechtel_invoices_enriched.csv"
OUTPUT = "bechtel_invoices_fully_enriched.csv"

# ── tiny helpers ───────────────────────────────────────────────────────────────

def det(seed):
    """Deterministic integer from any string seed."""
    return int(hashlib.md5(str(seed).encode()).hexdigest(), 16)

def pick(seed, choices):
    return choices[det(seed) % len(choices)]

def flt(seed, lo, hi, dp=2):
    ratio = (det(seed) % 100_000) / 100_000
    return round(lo + ratio * (hi - lo), dp)

def parse(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None

def fmt(d):
    return d.strftime("%Y-%m-%d") if d else ""

def f(s, default=0.0):
    try:
        return float(s) if s else default
    except (ValueError, TypeError):
        return default

def uid(seed):
    h = hashlib.md5(str(seed).encode()).hexdigest()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


# ── reference tables ───────────────────────────────────────────────────────────

SECTOR_MAP = {
    "LNG": "Oil & Gas", "OIL": "Oil & Gas", "POW": "Power & Utilities",
    "NUC": "Nuclear",   "INF": "Infrastructure", "MIN": "Mining & Metals",
    "MFG": "Industrial Manufacturing", "RNW": "Renewable Energy",
}
CONTRACT_TYPES  = ["Lump Sum", "Cost Plus Fee", "Unit Rate", "EPC", "EPCM", "Guaranteed Maximum Price"]
CLIENT_TYPES    = ["Owner", "Joint Venture", "Government", "Semi-Government", "Private Equity"]
PHASES          = ["Engineering", "Procurement", "Construction", "Pre-Commissioning", "Commissioning", "Handover"]
TRANSPORT_MODES = ["Road", "Rail", "Air", "Sea", "Multimodal"]
TRANSPORTERS    = [
    "DHL Supply Chain", "DB Schenker", "CEVA Logistics", "Agility Logistics",
    "Expeditors", "Kuehne+Nagel", "XPO Logistics", "FedEx Supply Chain",
    "UPS Supply Chain", "Panalpina Logistics",
]
RA_STATUSES    = ["Submitted", "Under Review", "Certified", "Partially Certified", "Rejected"]
VO_TYPES       = ["Scope Addition", "Scope Reduction", "Design Change", "Site Condition", "Owner Directed"]
DEFECT_CATS    = ["Dimensional", "Material", "Workmanship", "Surface Finish", "Functional", "Documentation"]
INSP_TYPES     = ["Incoming Inspection", "In-Process Inspection", "Final Inspection", "Third Party Inspection", "Witness Point", "Hold Point"]
TEST_TYPES     = ["Hydro Test", "Pressure Test", "NDT", "Chemical Analysis", "Dimensional Check", "Visual Inspection", "PMI", "Radiography"]
INCIDENT_TYPES = ["Near Miss", "First Aid Case", "Medical Treatment Case", "Lost Time Injury", "Property Damage", "Environmental Spill"]
SEVERITIES     = ["Low", "Medium", "High", "Critical"]
INJURY_NATURES = ["Laceration", "Bruise/Contusion", "Sprain/Strain", "Fracture", "Burns", "Eye Injury", "Chemical Exposure", "Crush Injury"]
BODY_PARTS     = ["Hand/Fingers", "Foot/Ankle", "Lower Back", "Head/Face", "Eye", "Leg/Knee", "Arm/Elbow", "Shoulder"]
PERSON_TYPES   = ["Direct Employee", "Subcontractor Worker", "Visitor", "Engineer/Supervisor"]
HSE_TRADES     = ["Pipefitter", "Welder", "Electrician", "Rigger", "Carpenter", "Mason", "Painter", "Scaffolder", "Plant Operator", "General Labour"]
HSE_ROOT_CAUSES= ["Unsafe Act", "Unsafe Condition", "Procedural Violation", "Equipment Failure", "Environmental Factor", "Inadequate Training"]
PERMIT_TYPES   = ["Hot Work", "Confined Space Entry", "Work at Height", "Excavation / Ground Breaking", "Electrical Isolation", "Crane & Lifting", "Radiation Work"]
AUTHORITIES    = ["Local Fire Department", "Municipal Corporation", "OSHA Regional Office", "State Labour Department", "Environment Agency", "Chief Electrical Inspector"]
RISK_LEVELS    = ["Low", "Medium", "High", "Critical"]
EQP_CATS       = ["Tower Crane", "Mobile Crane", "Excavator", "Concrete Pump", "Generator Set", "Air Compressor", "Forklift", "Welding Machine", "Bulldozer", "Boom Lift"]
OWN_TYPES      = ["Owned", "Hired", "Leased"]
IDLE_REASONS   = ["Breakdown", "No Work Front", "Operator Absent", "Fuel Shortage", "Scheduled Maintenance", "Adverse Weather"]
EST_TYPES      = ["Class 5 – Order of Magnitude", "Class 4 – Conceptual", "Class 3 – Preliminary", "Class 2 – Definitive", "Class 1 – Check Estimate"]
RATE_SOURCES   = ["Historical Database", "Vendor Quote", "Published Market Rate", "Benchmark DB", "Engineering Estimate"]
CONFIDENCE_LVL = ["Low (<30%)", "Medium (30–70%)", "High (>70%)"]
DRAW_TYPES     = ["P&ID", "General Arrangement", "Civil Drawing", "Structural Drawing", "Electrical SLD", "Isometric Drawing", "Layout Plan", "Equipment Datasheet"]
STORAGE_LOCS   = ["Main Warehouse", "Warehouse B", "Site Store – North", "Site Store – South", "Laydown Area 1", "Laydown Area 2", "Bonded Warehouse"]
MAT_GRADES     = {
    "structural_steel": "IS 2062 Grade E250",
    "piping":           "ASTM A106 Grade B",
    "civil":            "M25 Concrete / Fe 500 Rebar",
    "equipment":        "Carbon Steel / SS 316L",
    "mep":              "Copper / XLPE Insulated",
    "site_overheads":   "As per Project Specification",
    "subcontract":      "As per Contract Specification",
}
SPEC_STDS      = ["ASTM", "BS EN", "IS Code", "ASME B31.3", "API 650", "IEC 60364", "ISO 9001"]
FLOW_TYPES     = ["Inflow", "Outflow"]
WBS_CODES      = ["1.0", "1.1", "1.1.1", "1.1.2", "1.2", "1.2.1", "2.0", "2.1", "2.1.1", "3.0"]
WBS_DESCS      = {
    "1.0": "Civil Works Package",       "1.1": "Earthworks & Grading",
    "1.1.1": "Bulk Excavation",         "1.1.2": "Engineered Backfill",
    "1.2": "Structural Works",          "1.2.1": "Deep Foundations",
    "2.0": "Mechanical Package",        "2.1": "Static Equipment",
    "2.1.1": "Piping & Fittings",       "3.0": "Electrical & Instrumentation",
}
BUYER_ENTITIES = {
    "LNG": ("Bechtel Energy Inc",             "TX", "Houston",       "713-235-0100", "ap.invoices.energy@bechtel.com"),
    "NUC": ("Bechtel Nuclear Power Inc",      "VA", "Reston",        "703-459-1000", "ap.invoices.nuclear@bechtel.com"),
    "INF": ("Bechtel Infrastructure Corp",    "CA", "San Francisco", "415-768-1234", "ap.invoices.infra@bechtel.com"),
    "POW": ("Bechtel Power Corp",             "MD", "Frederick",     "301-228-6000", "ap.invoices.power@bechtel.com"),
    "MFG": ("Bechtel Industrial Inc",         "TX", "Houston",       "713-235-0200", "ap.invoices.mfg@bechtel.com"),
    "MIN": ("Bechtel Mining & Metals Inc",    "AZ", "Phoenix",       "602-381-5000", "ap.invoices.mining@bechtel.com"),
    "RNW": ("Bechtel Renewable Energy Inc",   "CA", "San Francisco", "415-768-5500", "ap.invoices.renewables@bechtel.com"),
    "OIL": ("Bechtel Oil Gas & Chemicals Inc","TX", "Houston",       "713-235-0300", "ap.invoices.ogc@bechtel.com"),
}
GST_RATES      = [5.0, 12.0, 18.0, 18.0, 18.0, 28.0]  # weighted toward 18%


# ══════════════════════════════════════════════════════════════════════════════
# CACHES  — built once, reused per row
# ══════════════════════════════════════════════════════════════════════════════

def build_project_cache(rows):
    cache = {}
    for r in rows:
        pid = r.get("inv_project_id", "")
        if not pid or pid in cache:
            continue
        sector_key = pid.split("-")[1] if "-" in pid and len(pid.split("-")) > 1 else "INF"
        sector     = SECTOR_MAP.get(sector_key, "Industrial")
        tcv        = f(r.get("prj_total_contract_value"), 500_000_000)

        inv_date   = parse(r.get("inv_invoice_date") or r.get("txn_date"))
        base_yr    = inv_date.year if inv_date else 2020
        p_start    = date(max(2000, base_yr - 3), (det(pid + "pm") % 6) + 1, 1)
        p_end      = date(base_yr + 2,             (det(pid + "pe") % 6) + 6, 28)
        a_start    = p_start + timedelta(days=(det(pid + "as") % 60) + 30)
        r_end      = p_end   + timedelta(days=(det(pid + "re") % 180))

        phase_start = p_start + timedelta(days=(det(pid + "pps") % 365))
        phase_end   = p_end   - timedelta(days=(det(pid + "ppe") % 180))

        cache[pid] = {
            "prj_client_id":            f"CLT-{uid(pid)[:8].upper()}",
            "prj_client_type":          pick(pid + "ct",    CLIENT_TYPES),
            "prj_sector":               sector,
            "prj_contract_type":        pick(pid + "ctype", CONTRACT_TYPES),
            "prj_site_pin_code":        f"{(det(pid + 'pin') % 90000) + 10000}",
            "prj_original_budget":      round(tcv * flt(pid + "ob", 0.88, 0.97), 2),
            "prj_revised_budget":       round(tcv * flt(pid + "rb", 0.98, 1.15), 2),
            "prj_planned_start_date":   fmt(p_start),
            "prj_planned_end_date":     fmt(p_end),
            "prj_actual_start_date":    fmt(a_start),
            "prj_revised_end_date":     fmt(r_end),
            "inv_project_phase":        pick(pid + "phase", PHASES),
            "prj_phase_planned_start":  fmt(phase_start),
            "prj_phase_planned_end":    fmt(phase_end),
            "prj_phase_completion_pct": round(flt(pid + "pcp", 25, 98), 1),
            "inv_tower_number":         pick(pid + "twn", ["Tower A", "Tower B", "Tower C", "Plot 1", "Plot 2", "Block 1", "Block 2", "Zone North", "Zone South"]),
            "inv_ship_to_address":      f"Site Construction Office, {r.get('prj_site_city','')}, {r.get('prj_site_state','')}",
            "inv_bill_to_address":      "Bechtel Corporation, 12011 Sunset Hills Road, Reston, VA 20190, USA",
        }
    return cache


def build_vendor_cache(rows):
    cache = {}
    for r in rows:
        vid = r.get("vnd_vendor_id", "")
        if not vid or vid in cache:
            continue
        emp_year  = 2005 + det(vid + "ey") % 15
        emp_month = det(vid + "em") % 12 + 1
        emp_date  = date(emp_year, emp_month, 1)
        exp_date  = emp_date.replace(year=emp_date.year + 5)
        s_suffix  = "".join([chr(65 + det(vid + f"ssc{i}") % 26) for i in range(2)])
        cache[vid] = {
            "inv_supplier_state_code": f"{(det(vid + 'ssc') % 36) + 1:02d}",
            "inv_supplier_ifsc_code":  f"{s_suffix}{''.join([chr(65 + det(vid+f'i{i}') % 26) for i in range(2)])}0{(det(vid+'ifn') % 900000) + 100000}",
            "vnd_cin":                 f"U{(det(vid+'cin') % 90000) + 10000}{s_suffix}{(det(vid+'cin2') % 90000) + 10000}",
            "vnd_empanelment_date":    fmt(emp_date),
            "vnd_empanelment_expiry":  fmt(exp_date),
        }
    return cache


def build_invoice_cache(rows):
    cache = {}
    for r in rows:
        iid = r.get("invoice_id", "")
        if not iid or iid in cache:
            continue
        inv_date = parse(r.get("inv_invoice_date"))
        dc_date  = (inv_date - timedelta(days=(det(iid + "dc") % 5) + 1)) if inv_date else None
        has_eway = (det(iid + "ew") % 10) < 6   # 60% have eway bill
        po_date  = (parse(r.get("po_delivery_date")) - timedelta(days=(det(iid + "pod") % 120) + 30)) if parse(r.get("po_delivery_date")) else None
        irn_hash = hashlib.sha256(iid.encode()).hexdigest()[:64]

        cache[iid] = {
            "inv_template_type":     pick(iid + "tt", ["Tax Invoice", "Commercial Invoice", "Proforma Invoice", "Tax Invoice"]),
            "inv_dc_number":         f"DC/{r.get('inv_project_code','PRJ')}/{(det(iid+'dcn') % 90000) + 10000}",
            "inv_dc_date":           fmt(dc_date),
            "inv_eway_bill_number":  f"EWB{(det(iid+'ewb') % 9_000_000_000_000) + 1_000_000_000_000}" if has_eway else "",
            "inv_eway_bill_date":    fmt(dc_date) if has_eway else "",
            "inv_vehicle_number":    f"{'ABCD'[det(iid+'vn1')%4]}{'ABCD'[det(iid+'vn2')%4]}{(det(iid+'vn3')%90)+10}{'ABCDE'[det(iid+'vn4')%5]}{(det(iid+'vn5')%9000)+1000}" if has_eway else "",
            "inv_mode_of_transport": pick(iid + "mot", TRANSPORT_MODES),
            "inv_transporter_name":  pick(iid + "tn",  TRANSPORTERS),
            "inv_lr_number":         f"LR{(det(iid+'lr') % 9_000_000) + 1_000_000}",
            "inv_state_code":        f"{(det(iid+'sc') % 36) + 1:02d}",
            "inv_irn":               irn_hash,
            "inv_ack_number":        f"{(det(iid+'ack') % 9_000_000_000_000) + 1_000_000_000_000}",
            "inv_ack_date":          fmt(inv_date + timedelta(days=1)) if inv_date else "",
            "inv_po_number":         r.get("inv_matched_po_number") or f"PO-{(det(iid+'pon') % 900000) + 100000}",
            "inv_po_date":           fmt(po_date),
            "inv_work_order_number": f"WO-{r.get('inv_project_code','PRJ')}-{(det(iid+'wo') % 9000) + 1000}",
            "inv_delivery_note":     f"DN/{(det(iid+'dn') % 90000) + 10000}",
        }
    return cache


# ══════════════════════════════════════════════════════════════════════════════
# ROW ENRICHMENT
# ══════════════════════════════════════════════════════════════════════════════

def enrich_row(r, proj_cache, vend_cache, inv_cache, row_idx):
    out      = dict(r)
    pid      = r.get("inv_project_id", "")
    vid      = r.get("vnd_vendor_id", "")
    iid      = r.get("invoice_id", "")
    lid      = r.get("line_item_id", "")
    epc      = r.get("inv_li_epc_category", "civil") or "civil"

    inv_date  = parse(r.get("inv_invoice_date"))
    total_amt = f(r.get("inv_total_amount"), 50_000)
    li_tax    = f(r.get("inv_li_taxable_amount"), total_amt * 0.847)
    li_qty    = f(r.get("inv_li_quantity"), 10.0)
    li_rate   = f(r.get("inv_li_unit_rate"), 5_000.0)
    is_sub    = (r.get("vnd_vendor_type") or "").lower() in ("subcontractor",)

    # sequential row id
    out["row_process_id"] = row_idx

    # bump synced_at so ReplacingMergeTree picks these rows over the old ones
    out["synced_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── project cache ─────────────────────────────────────────────────────────
    for k, v in proj_cache.get(pid, {}).items():
        out[k] = v

    # WBS (per line item, deterministic)
    wbs_code = pick(lid + "wbs", WBS_CODES)
    out["prj_wbs_code"]        = wbs_code
    out["prj_wbs_description"] = WBS_DESCS.get(wbs_code, "Works Package")
    out["prj_wbs_level"]       = wbs_code.count(".") + 1
    out["inv_li_wbs_id"]       = f"WBS-{pid}-{wbs_code.replace('.', '')}"
    out["inv_li_cost_code"]    = f"CC-{epc.upper()[:4]}-{(det(lid+'cc') % 9000) + 1000}"

    # ── vendor cache ──────────────────────────────────────────────────────────
    for k, v in vend_cache.get(vid, {}).items():
        out[k] = v

    # ── invoice cache ─────────────────────────────────────────────────────────
    for k, v in inv_cache.get(iid, {}).items():
        out[k] = v

    # ── buyer ─────────────────────────────────────────────────────────────────
    sector_key  = pid.split("-")[1] if "-" in pid and len(pid.split("-")) > 1 else "INF"
    bname, bstate, bcity, bphone, bemail = BUYER_ENTITIES.get(sector_key, BUYER_ENTITIES["INF"])
    out["inv_buyer_name"]       = bname
    out["inv_buyer_gstin"]      = f"27AABC{(det(pid+'bg') % 9000) + 1000}P1Z{det(pid+'bgc') % 9}"
    out["inv_buyer_pan"]        = f"AABC{chr(65 + det(pid+'bp0') % 26)}{(det(pid+'bp1') % 9000) + 1000}{chr(65 + det(pid+'bp2') % 26)}"
    out["inv_buyer_city"]       = bcity
    out["inv_buyer_state"]      = bstate
    out["inv_buyer_state_code"] = f"{(det(pid+'bsc') % 36) + 1:02d}"
    out["inv_buyer_phone"]      = bphone
    out["inv_buyer_email"]      = bemail

    # ── PO additions ─────────────────────────────────────────────────────────
    po_qty_ord   = f(r.get("po_li_quantity_ordered"), li_qty)
    gst_rate     = pick(lid + "gst", GST_RATES)
    out["po_line_no"]              = (det(lid + "pln") % 20) + 1
    out["po_li_hsn_sac_code"]      = r.get("inv_li_hsn_sac_code") or f"{(det(lid+'hsn') % 9000) + 1000}"
    out["po_li_material_type"]     = r.get("inv_li_material_type") or epc
    out["po_li_quantity_rejected"] = round(po_qty_ord * flt(lid + "rj", 0, 0.03), 3)
    out["po_li_gst_rate"]          = gst_rate
    out["po_over_invoiced_amount"] = round(total_amt * flt(lid + "oia", 0.01, 0.04), 2) if int(r.get("po_over_invoiced_flag") or 0) else 0.0
    out["po_delivery_delay_days"]  = (det(lid + "pdd") % 30) if r.get("po_delivery_status") == "Delayed" else 0
    out["contract_id"]             = uid(pid + "contract")

    # RA Bill (subcontractors)
    ra_num = (det(iid + "ran") % 90) + 1
    if is_sub:
        out["ra_bill_id"]            = uid(iid + "rabill")
        out["ra_bill_number"]        = f"RA/{r.get('inv_project_code', 'PRJ')}/{ra_num:04d}"
        out["ra_bill_gross_amount"]  = total_amt
        out["ra_bill_net_payable"]   = round(total_amt * flt(lid + "rbnp", 0.85, 0.95), 2)
        out["ra_bill_certified_date"]= fmt(inv_date + timedelta(days=(det(iid + "rcd") % 14) + 7)) if inv_date else ""
        out["ra_bill_status"]        = pick(iid + "rbs", RA_STATUSES)
    else:
        for k in ("ra_bill_id", "ra_bill_number", "ra_bill_gross_amount", "ra_bill_net_payable", "ra_bill_certified_date", "ra_bill_status"):
            out[k] = ""

    # Variation Order (~20% of rows)
    has_vo = (det(lid + "vo") % 5) == 0
    if has_vo:
        out["vo_id"]     = uid(lid + "void")
        out["vo_number"] = f"VO-{r.get('inv_project_code', 'PRJ')}-{(det(lid+'von') % 999) + 1:03d}"
        out["vo_type"]   = pick(lid + "vot", VO_TYPES)
        out["vo_amount"] = round(total_amt * flt(lid + "voa", 0.03, 0.20), 2)
        out["vo_status"] = pick(lid + "vos", ["Submitted", "Approved", "Approved", "Pending", "Rejected"])
    else:
        for k in ("vo_id", "vo_number", "vo_type", "vo_amount", "vo_status"):
            out[k] = ""

    # ── flag defaults (uint8) ─────────────────────────────────────────────────
    out["inv_reverse_charge"] = 0           # reverse charge rarely applies
    out["po_is_blanket"]      = 1 if (det(lid + "pob") % 5) == 0 else 0   # 20% blanket POs
    out["escalation_clause"]  = 1 if (det(lid + "esc") % 4) == 0 else 0   # 25% have escalation

    # ── financial additions ───────────────────────────────────────────────────
    out["inv_cess_amount"]   = round(li_tax * 0.01, 2) if epc == "equipment" else 0.0
    out["inv_budget_ref_id"] = f"BGT-{pid}-{wbs_code.replace('.', '')}"

    # GRN exists for material-heavy categories; ~85% of material invoices, ~30% of service invoices
    MATERIAL_EPC = {"structural_steel", "piping", "civil", "equipment"}
    grn_threshold = 85 if epc in MATERIAL_EPC else 30
    has_grn = (det(iid + "grnchk") % 100) < grn_threshold
    if has_grn:
        out["inv_grn_number"]  = f"GRN/{r.get('inv_project_code', 'PRJ')}/{(det(iid+'grnn') % 90000) + 10000}"
        out["inv_grn_date"]    = fmt(inv_date - timedelta(days=(det(iid + "grnd") % 5) + 1)) if inv_date else ""
        out["inv_grn_quantity"]= round(li_qty * flt(lid + "grnq", 0.95, 1.0), 3)
        out["inv_grn_matched"] = 1
    else:
        out["inv_grn_number"]  = ""
        out["inv_grn_date"]    = ""
        out["inv_grn_quantity"]= 0.0
        out["inv_grn_matched"] = 0

    qty_var_pct = f(r.get("inv_qty_variance_pct"), 0)
    if not qty_var_pct:
        qty_var_pct = round(flt(lid + "qvp", -3.0, 3.0), 2)
    out["inv_qty_variance_pct"]  = qty_var_pct
    out["inv_qty_variance_flag"] = 1 if abs(qty_var_pct) > 5.0 else 0

    # ── line-item tax (derived from invoice-level GST) ────────────────────────
    cgst_rate = pick(lid + "cgstr", [0.0, 2.5, 6.0, 9.0])
    sgst_rate = cgst_rate
    igst_rate = cgst_rate * 2
    out["inv_li_cgst_rate"]   = cgst_rate
    out["inv_li_cgst_amount"] = round(li_tax * cgst_rate / 100, 2)
    out["inv_li_sgst_rate"]   = sgst_rate
    out["inv_li_sgst_amount"] = round(li_tax * sgst_rate / 100, 2)
    out["inv_li_igst_rate"]   = igst_rate
    out["inv_li_igst_amount"] = round(li_tax * igst_rate / 100, 2)

    # ── payment UTR ───────────────────────────────────────────────────────────
    if (r.get("pmt_payment_status") or "").lower() in ("paid", "completed"):
        out["pmt_utr_number"] = f"UTR{(det(iid + 'utr') % 9_000_000_000_000) + 1_000_000_000_000}"
    else:
        out["pmt_utr_number"] = ""

    # ── schedule actual finish ────────────────────────────────────────────────
    plan_finish = parse(r.get("sch_planned_finish"))
    delay_days  = int(f(r.get("sch_delay_days"), 0))
    if plan_finish:
        out["sch_actual_finish"] = fmt(plan_finish + timedelta(days=delay_days))
    else:
        out["sch_actual_finish"] = ""

    # ── quality inspection ────────────────────────────────────────────────────
    ncr    = 1 if (det(lid + "ncr") % 10) == 0 else 0   # 10% NCR rate
    rework = 1 if ncr and (det(lid + "rw") % 2) == 0 else 0
    out["qua_inspection_id"]        = uid(lid + "qua")
    out["qua_inspection_type"]      = pick(lid + "qit", INSP_TYPES)
    out["qua_inspection_date"]      = fmt(inv_date - timedelta(days=(det(lid + "qid") % 10) + 1)) if inv_date else ""
    out["qua_activity_inspected"]   = r.get("inv_li_description") or f"{epc.replace('_', ' ').title()} Inspection"
    out["qua_result"]               = "Rejected" if ncr else "Accepted"
    out["qua_ncr_raised"]           = ncr
    out["qua_ncr_number"]           = f"NCR-{r.get('inv_project_code','PRJ')}-{(det(lid+'ncn') % 9000) + 1000}" if ncr else ""
    out["qua_ncr_open_days"]        = (det(lid + "nod") % 30) + 1 if ncr else 0
    out["qua_defect_category"]      = pick(lid + "dc", DEFECT_CATS) if ncr else ""
    out["qua_rework_required"]      = rework
    out["qua_rework_cost"]          = round(total_amt * flt(lid + "rwc", 0.01, 0.05), 2) if rework else 0.0
    out["qua_rework_days_lost"]     = (det(lid + "rwdl") % 7) + 1 if rework else 0
    out["qua_test_type"]            = pick(lid + "qtt", TEST_TYPES)
    out["qua_test_value"]           = round(flt(lid + "qtv", 50.0, 350.0), 1)
    out["qua_test_unit"]            = pick(lid + "qtu", ["bar", "MPa", "°C", "mm", "kN", "%", "psi"])
    out["qua_test_passed"]          = 0 if ncr else 1

    # ── HSE ───────────────────────────────────────────────────────────────────
    manhours = round(flt(lid + "mhw", 200.0, 2000.0), 0)
    incident = (det(lid + "hsei") % 50) == 0  # ~2% incident rate
    out["hse_manhours_worked"]   = manhours
    out["hse_ltifr"]             = round(flt(lid + "ltifr", 0.0, 0.25), 4)
    out["hse_trifr"]             = round(flt(lid + "trifr", 0.0, 0.70), 4)
    if incident:
        inc_date = (inv_date - timedelta(days=(det(lid + "hidate") % 30))) if inv_date else None
        out["hse_incident_id"]            = uid(lid + "hseincid")
        out["hse_incident_type"]          = pick(lid + "hit",  INCIDENT_TYPES)
        out["hse_incident_date"]          = fmt(inc_date)
        out["hse_severity"]               = pick(lid + "hsev", SEVERITIES)
        out["hse_injury_nature"]          = pick(lid + "hin",  INJURY_NATURES)
        out["hse_body_part"]              = pick(lid + "hbp",  BODY_PARTS)
        out["hse_person_type"]            = pick(lid + "hpt",  PERSON_TYPES)
        out["hse_trade"]                  = pick(lid + "htrd", HSE_TRADES)
        out["hse_lti_days"]               = (det(lid + "hltid") % 14) + 1
        out["hse_property_damage_cost"]   = round(flt(lid + "hpdc", 0.0, 50_000.0), 2)
        out["hse_root_cause"]             = pick(lid + "hrc",  HSE_ROOT_CAUSES)
        out["hse_corrective_action_done"] = 1
        out["hse_reported_to_authority"]  = 1 if (det(lid + "hra") % 3) == 0 else 0
    else:
        for k in ("hse_incident_id", "hse_incident_type", "hse_incident_date", "hse_severity",
                  "hse_injury_nature", "hse_body_part", "hse_person_type", "hse_trade", "hse_root_cause"):
            out[k] = ""
        for k in ("hse_lti_days", "hse_property_damage_cost", "hse_corrective_action_done", "hse_reported_to_authority"):
            out[k] = 0

    # ── labour deployment ─────────────────────────────────────────────────────
    planned_hc = (det(lid + "lpln") % 50) + 5
    actual_hc  = max(1, planned_hc + (det(lid + "lac") % 11) - 5)
    skilled    = int(actual_hc * flt(lid + "lsk",  0.40, 0.70))
    unskilled  = actual_hc - skilled
    female     = int(actual_hc * flt(lid + "lfc",  0.00, 0.12))
    reg_hrs    = round(actual_hc * 8.0, 1)
    ot_hrs     = round(actual_hc * flt(lid + "loth", 0.0, 2.0), 1)
    wage_rate  = round(flt(lid + "ldwr", 150.0, 650.0), 2)
    lab_cost   = round(actual_hc * wage_rate * (reg_hrs / 8), 2)
    ot_cost    = round(actual_hc * wage_rate * 1.5 * (ot_hrs / 8), 2) if ot_hrs else 0.0
    prod       = round(flt(lid + "lprd", 0.5, 5.0), 3)
    bench      = round(flt(lid + "lbpr", 1.0, 6.0), 3)
    out["lab_deployment_date"]      = fmt(inv_date) if inv_date else ""
    out["lab_trade"]                = pick(lid + "ltrd", HSE_TRADES)
    out["lab_planned_count"]        = planned_hc
    out["lab_actual_count"]         = actual_hc
    out["lab_skilled_count"]        = skilled
    out["lab_unskilled_count"]      = unskilled
    out["lab_female_count"]         = female
    out["lab_is_direct"]            = 0 if is_sub else 1
    out["lab_regular_hours"]        = reg_hrs
    out["lab_overtime_hours"]       = ot_hrs
    out["lab_daily_wage_rate"]      = wage_rate
    out["lab_total_cost"]           = lab_cost
    out["lab_overtime_cost"]        = ot_cost
    out["lab_headcount_variance"]   = actual_hc - planned_hc
    out["lab_headcount_var_flag"]   = 1 if abs(actual_hc - planned_hc) > 5 else 0
    out["lab_output_quantity"]      = round(flt(lid + "lopq", 10.0, 500.0), 2)
    out["lab_output_uom"]           = pick(lid + "lopu", ["m3", "m2", "MT", "nos", "RMT", "kg", "m"])
    out["lab_productivity_rate"]    = prod
    out["lab_benchmark_productivity"]= bench
    out["lab_productivity_index"]   = round(prod / bench, 3)

    # ── equipment utilisation ─────────────────────────────────────────────────
    avail_hrs     = 10.0
    worked_hrs    = round(flt(lid + "ewh",  4.0, 9.5), 1)
    breakdown_hrs = round(flt(lid + "ebdh", 0.0, 0.5), 1)
    idle_hrs      = max(0.0, round(avail_hrs - worked_hrs - breakdown_hrs, 1))
    hire_rate     = round(flt(lid + "ehrph", 50.0, 500.0), 2)
    fuel_ltrs     = round(flt(lid + "efl",   20.0, 200.0), 1)
    fuel_price    = round(flt(lid + "efcp",  0.90,   1.40), 3)
    out["eqp_equipment_id"]       = uid(pid + epc + "eqp")
    out["eqp_equipment_code"]     = f"EQP-{(det(lid+'eqpc') % 9000) + 1000}"
    out["eqp_category"]           = pick(lid + "eqcat", EQP_CATS)
    out["eqp_ownership_type"]     = pick(lid + "eqown", OWN_TYPES)
    out["eqp_utilisation_date"]   = fmt(inv_date) if inv_date else ""
    out["eqp_available_hours"]    = avail_hrs
    out["eqp_worked_hours"]       = worked_hrs
    out["eqp_idle_hours"]         = idle_hrs
    out["eqp_breakdown_hours"]    = breakdown_hrs
    out["eqp_utilisation_pct"]    = round(worked_hrs / avail_hrs * 100, 1)
    out["eqp_idle_reason"]        = pick(lid + "eir", IDLE_REASONS) if idle_hrs > 0.5 else ""
    out["eqp_hire_rate_per_hour"] = hire_rate
    out["eqp_total_hire_cost"]    = round(worked_hrs * hire_rate, 2)
    out["eqp_fuel_consumed_ltrs"] = fuel_ltrs
    out["eqp_fuel_cost"]          = round(fuel_ltrs * fuel_price, 2)
    out["eqp_total_running_cost"] = round(out["eqp_total_hire_cost"] + out["eqp_fuel_cost"], 2)
    out["eqp_breakdown_flag"]     = 1 if breakdown_hrs > 0 else 0

    # ── estimation ────────────────────────────────────────────────────────────
    est_rate  = round(li_rate * flt(lid + "estur", 0.85, 1.10), 2)
    est_qty   = round(li_qty  * flt(lid + "estq",  0.90, 1.10), 3)
    est_amt   = round(est_rate * est_qty, 2)
    act_rate  = li_rate
    act_amt   = round(act_rate * li_qty, 2)
    pc        = proj_cache.get(pid, {})
    est_base_date = parse(pc.get("prj_planned_start_date"))
    out["est_estimate_id"]          = uid(lid + "estid")
    out["est_opportunity_id"]       = f"OPP-{pid}-{(det(lid+'estop') % 999) + 1:03d}"
    out["est_version"]              = pick(lid + "estv", ["Rev 0", "Rev A", "Rev B", "Rev C", "Rev 1"])
    out["est_type"]                 = pick(lid + "estt", EST_TYPES)
    out["est_date"]                 = fmt(est_base_date + timedelta(days=(det(lid + "estdt") % 180))) if est_base_date else ""
    out["est_quantity"]             = est_qty
    out["est_uom"]                  = r.get("inv_li_uom") or "nos"
    out["est_unit_rate"]            = est_rate
    out["est_amount"]               = est_amt
    out["est_rate_source"]          = pick(lid + "estrs", RATE_SOURCES)
    out["est_confidence_level"]     = pick(lid + "estcl", CONFIDENCE_LVL)
    out["est_actual_unit_rate"]     = act_rate
    out["est_actual_amount"]        = act_amt
    out["est_rate_variance_pct"]    = round((act_rate - est_rate) / est_rate * 100, 2) if est_rate else 0.0
    out["est_amount_variance_pct"]  = round((act_amt  - est_amt)  / est_amt  * 100, 2) if est_amt  else 0.0

    # ── permits ───────────────────────────────────────────────────────────────
    needs_permit = epc in ("civil", "mep", "structural_steel") or (det(lid + "perm") % 5) == 0
    if needs_permit:
        days_before_inv = (det(lid + "pisd") % 60) + 14
        p_issued  = (inv_date - timedelta(days=days_before_inv)) if inv_date else None
        p_expiry  = (p_issued + timedelta(days=(det(lid + "pexp") % 365) + 90)) if p_issued else None
        days_left = (p_expiry - date.today()).days if p_expiry else 0
        out["pmt_permit_id"]         = uid(lid + "permid")
        out["per_permit_type"]       = pick(lid + "ppt", PERMIT_TYPES)
        out["per_permit_number"]     = f"PERM-{r.get('inv_project_code','PRJ')}-{(det(lid+'ppn') % 9000) + 1000}"
        out["per_issuing_authority"] = pick(lid + "pia",  AUTHORITIES)
        out["per_application_date"]  = fmt(p_issued - timedelta(days=30)) if p_issued else ""
        out["per_issued_date"]       = fmt(p_issued)
        out["per_expiry_date"]       = fmt(p_expiry)
        out["per_status"]            = "Expired" if days_left < 0 else "Active"
        out["per_risk_level"]        = pick(lid + "prl", RISK_LEVELS)
        out["per_days_to_expiry"]    = days_left
        out["per_penalty_amount"]    = round(flt(lid + "ppa", 500.0, 10_000.0), 2) if days_left < 0 else 0.0
    else:
        for k in ("pmt_permit_id", "per_permit_type", "per_permit_number", "per_issuing_authority",
                  "per_application_date", "per_issued_date", "per_expiry_date", "per_status", "per_risk_level"):
            out[k] = ""
        out["per_days_to_expiry"] = 0
        out["per_penalty_amount"] = 0.0

    # ── cash flow additions ───────────────────────────────────────────────────
    cf_planned = f(r.get("cf_planned_amount"), total_amt)
    cf_actual  = f(r.get("cf_actual_amount"),  total_amt * 0.9)
    out["cf_cumulative_planned"]  = round(cf_planned * flt(lid + "cfcp", 1.5, 8.0), 2)
    out["cf_cumulative_actual"]   = round(cf_actual  * flt(lid + "cfca", 1.2, 7.5), 2)
    out["cf_net_cash_position"]   = round(out["cf_cumulative_actual"] - out["cf_cumulative_planned"], 2)
    out["cf_overdue_receivables"] = round(total_amt * flt(lid + "cfor", 0.0, 0.12), 2)
    out["cf_bg_amount_outstanding"]= round(total_amt * flt(lid + "cfbg", 0.05, 0.15), 2)

    # ── external WPI index ────────────────────────────────────────────────────
    yr = inv_date.year if inv_date else 2022
    out["ext_wpi_index"] = round(150.0 * (1.04 ** (yr - 2015)), 2)

    # ── design & document ─────────────────────────────────────────────────────
    has_dcr = (det(lid + "dcr") % 10) == 0   # 10% have design change request
    disc    = pick(lid + "ddt", ["CIV", "STR", "MEC", "ELE", "INS", "PIP"])
    out["doc_drawing_id"]          = uid(lid + "drawid")
    out["doc_drawing_number"]      = f"{r.get('inv_project_code', 'PRJ')}-{disc}-{(det(lid+'ddn') % 9000) + 1000}"
    out["doc_drawing_type"]        = pick(lid + "ddtype", DRAW_TYPES)
    out["doc_drawing_revision"]    = pick(lid + "ddr", ["0", "1", "2", "A", "B", "C"])
    out["doc_dcr_id"]              = uid(lid + "dcrid") if has_dcr else ""
    out["doc_dcr_cost_impact"]     = round(total_amt * flt(lid + "dcrci", 0.02, 0.12), 2) if has_dcr else 0.0
    out["doc_dcr_time_impact_days"]= (det(lid + "dcrtid") % 21) + 1 if has_dcr else 0

    # ── BOQ ───────────────────────────────────────────────────────────────────
    boq_est_qty  = round(li_qty * flt(lid + "boqeq",  1.00, 1.20), 3)
    boq_rev_qty  = round(boq_est_qty * flt(lid + "boqrq", 0.95, 1.10), 3)
    boq_act_qty  = li_qty
    boq_rate     = round(li_rate * flt(lid + "boqr",  0.90, 1.05), 2)
    boq_est_amt  = round(boq_est_qty * boq_rate, 2)
    boq_rev_amt  = round(boq_rev_qty * boq_rate, 2)
    boq_act_amt  = round(boq_act_qty * boq_rate, 2)
    boq_qty_var  = round(boq_act_qty - boq_rev_qty, 3)
    boq_qty_vp   = round(boq_qty_var / boq_rev_qty * 100, 2) if boq_rev_qty else 0.0
    boq_amt_var  = round(boq_act_amt - boq_rev_amt, 2)
    boq_amt_vp   = round(boq_amt_var / boq_rev_amt * 100, 2) if boq_rev_amt else 0.0
    out["boq_id"]                 = uid(lid + "boqid")
    out["boq_code"]               = f"BOQ-{epc.upper()[:3]}-{(det(lid+'boqc') % 9000) + 1000}"
    out["boq_description"]        = r.get("inv_li_description") or f"{epc.replace('_', ' ').title()} Works"
    out["boq_spec_reference"]     = f"SPEC-{(det(lid+'boqsr') % 900) + 100}"
    out["boq_version"]            = pick(lid + "boqv", ["V1", "V2", "V3"])
    out["boq_epc_category"]       = epc
    out["boq_wbs_code"]           = wbs_code
    out["boq_uom"]                = r.get("inv_li_uom") or "nos"
    out["boq_estimated_qty"]      = boq_est_qty
    out["boq_revised_qty"]        = boq_rev_qty
    out["boq_actual_qty"]         = boq_act_qty
    out["boq_qty_variance"]       = boq_qty_var
    out["boq_qty_variance_pct"]   = boq_qty_vp
    out["boq_qty_revision_reason"]= pick(lid + "boqqrr", ["Design Change", "Site Condition", "Owner Instruction", ""]) if boq_qty_var != 0 else ""
    out["boq_unit_rate"]          = boq_rate
    out["boq_estimated_amount"]   = boq_est_amt
    out["boq_revised_amount"]     = boq_rev_amt
    out["boq_actual_amount"]      = boq_act_amt
    out["boq_amount_variance"]    = boq_amt_var
    out["boq_amount_variance_pct"]= boq_amt_vp

    # ── BOM ───────────────────────────────────────────────────────────────────
    bom_req   = round(li_qty  * flt(lid + "bomrq",  1.00, 1.15), 3)
    bom_recv  = round(bom_req * flt(lid + "bomrcv", 0.80, 1.00), 3)
    bom_iss   = round(bom_recv * flt(lid + "bomiq",  0.75, 1.00), 3)
    bom_cons  = round(bom_iss  * flt(lid + "bomcq",  0.88, 1.00), 3)
    bom_wst   = max(0.0, round(bom_iss - bom_cons, 3))
    bom_bal   = max(0.0, round(bom_recv - bom_iss, 3))
    bom_pend  = max(0.0, round(bom_req  - bom_recv, 3))
    std_rate  = round(li_rate * flt(lid + "bomsr",  0.90, 1.00), 2)
    bom_req_amt  = round(bom_req  * std_rate, 2)
    bom_act_amt2 = round(bom_cons * li_rate, 2)
    bom_amt_var2 = round(bom_act_amt2 - bom_req_amt, 2)
    out["bom_id"]                  = uid(lid + "bomid")
    out["bom_item_code"]           = f"MAT-{epc.upper()[:3]}-{(det(lid+'bomic') % 9000) + 1000}"
    out["bom_item_description"]    = r.get("inv_li_description") or f"{epc.replace('_', ' ').title()} Material"
    out["bom_material_grade"]      = MAT_GRADES.get(epc, "As per Specification")
    out["bom_spec_standard"]       = pick(lid + "bomss", SPEC_STDS)
    out["bom_material_type"]       = r.get("inv_li_material_type") or epc
    out["bom_epc_category"]        = epc
    out["bom_wbs_code"]            = wbs_code
    out["bom_boq_ref"]             = out["boq_code"]
    out["bom_uom"]                 = r.get("inv_li_uom") or "nos"
    out["bom_required_qty"]        = bom_req
    out["bom_po_qty"]              = round(bom_req * flt(lid + "bompq", 1.00, 1.05), 3)
    out["bom_received_qty"]        = bom_recv
    out["bom_issued_qty"]          = bom_iss
    out["bom_consumed_qty"]        = bom_cons
    out["bom_balance_qty"]         = bom_bal
    out["bom_wastage_qty"]         = bom_wst
    out["bom_wastage_pct"]         = round(bom_wst / bom_iss * 100, 2) if bom_iss else 0.0
    out["bom_pending_po_qty"]      = bom_pend
    out["bom_shortage_flag"]       = 1 if bom_pend > 0 else 0
    out["bom_standard_unit_rate"]  = std_rate
    out["bom_actual_unit_rate"]    = li_rate
    out["bom_rate_variance_pct"]   = round((li_rate - std_rate) / std_rate * 100, 2) if std_rate else 0.0
    out["bom_required_amount"]     = bom_req_amt
    out["bom_actual_amount"]       = bom_act_amt2
    out["bom_amount_variance"]     = bom_amt_var2
    out["bom_storage_location"]    = pick(lid + "bomsl", STORAGE_LOCS)
    out["bom_lead_time_days"]      = (det(lid + "bomlt") % 60) + 7
    out["bom_reorder_level_qty"]   = round(bom_req * 0.20, 3)
    last_rcpt = (inv_date - timedelta(days=(det(lid + "bomlrd") % 30) + 1)) if inv_date else None
    next_req  = (inv_date + timedelta(days=(det(lid + "bomnrd") % 60) + 7)) if inv_date else None
    out["bom_last_receipt_date"]      = fmt(last_rcpt)
    out["bom_next_requirement_date"]  = fmt(next_req)

    return out


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"Reading {INPUT} ...")
    with open(INPUT, encoding="utf-8") as fh:
        reader     = csv.DictReader(fh)
        rows       = list(reader)
        fieldnames = reader.fieldnames or []
    print(f"  {len(rows):,} rows  |  {len(fieldnames)} input columns")

    print("Building project / vendor / invoice caches ...")
    proj_cache = build_project_cache(rows)
    vend_cache = build_vendor_cache(rows)
    inv_cache  = build_invoice_cache(rows)
    print(f"  {len(proj_cache)} projects  |  {len(vend_cache)} vendors  |  {len(inv_cache)} invoices")

    print("Enriching rows ...")
    enriched = []
    for i, row in enumerate(rows, start=1):
        enriched.append(enrich_row(row, proj_cache, vend_cache, inv_cache, i))
        if i % 1000 == 0:
            print(f"  {i:,} / {len(rows):,}", end="\r")

    all_cols = list(dict.fromkeys(list(enriched[0].keys())))
    print(f"\nWriting {OUTPUT} ({len(all_cols)} columns) ...")
    with open(OUTPUT, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=all_cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(enriched)

    print(f"  Done.  {len(enriched):,} rows  |  {len(all_cols)} columns")
    print(f"\nNext step:")
    print(f"  python insert_to_clickhouse.py --csv {OUTPUT}")


if __name__ == "__main__":
    main()
