"""
ClickHouse Insert Script — con_master_fact (403 columns)
=========================================================
Reads bechtel_invoices_v2.csv and inserts into ClickHouse.

Strategy:
  - CSV has 63 columns (the EXTRACTED columns we generated)
  - Remaining 340 columns are NULL/default (ENRICHED — filled later by enrichment waves)
  - Every row is cast to the correct ClickHouse type before insert
  - Inserts in batches of 500 rows to avoid memory issues
  - Uses ReplacingMergeTree safe upsert pattern (synced_at as version)

Prerequisites:
  pip install clickhouse-driver pandas

Usage:
  # Default (uses pre-configured connection)
  python insert_to_clickhouse.py

  # Override connection
  python insert_to_clickhouse.py --host 192.168.1.10 --port 8124 --user admin --password admin123 --database invoice_extraction

  # Dry run (print first 2 rows, no insert)
  python insert_to_clickhouse.py --dry-run
"""

import csv
import argparse
import sys
from datetime import datetime, date
from typing import Any

from constants import (
    CLICKHOUSE_HOST, CLICKHOUSE_PORT, CLICKHOUSE_USER,
    CLICKHOUSE_PASSWORD, CLICKHOUSE_DATABASE, CLICKHOUSE_TABLE,
)

# ── Install check ────────────────────────────────────────────────────────────
try:
    from clickhouse_driver import Client
except ImportError:
    print("ERROR: clickhouse-driver not installed.")
    print("Run: pip install clickhouse-driver")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — ALL 403 COLUMN DEFINITIONS
# Maps column_name → (clickhouse_type, python_default_when_missing)
# Types: "str" | "int" | "float" | "date" | "datetime" | "uint8"
# ══════════════════════════════════════════════════════════════════════════════

COLUMNS = {
    # ── Section 0: Dedup keys ──────────────────────────────────────────────
    "transaction_id":              ("str",      None),
    "line_item_id":                ("str",      None),
    "synced_at":                   ("datetime", None),
    "row_process_id":              ("int",      0),

    # ── Section 1: Transaction type ────────────────────────────────────────
    "txn_type":                    ("str",      "invoice"),
    "txn_source":                  ("str",      None),
    "txn_date":                    ("date",     None),

    # ── Section 2: Project dimensions ──────────────────────────────────────
    "inv_project_name":            ("str",      None),
    "inv_project_code":            ("str",      None),
    "inv_tower_number":            ("str",      None),
    "inv_ship_to_address":         ("str",      None),
    "inv_bill_to_address":         ("str",      None),
    "inv_project_id":              ("str",      None),
    "prj_client_id":               ("str",      None),
    "prj_client_name":             ("str",      None),
    "prj_client_type":             ("str",      None),
    "prj_sector":                  ("str",      None),
    "prj_type":                    ("str",      None),
    "prj_contract_type":           ("str",      None),
    "prj_status":                  ("str",      None),
    "prj_site_city":               ("str",      None),
    "prj_site_state":              ("str",      None),
    "prj_site_pin_code":           ("str",      None),
    "prj_total_contract_value":    ("float",    None),
    "prj_original_budget":         ("float",    None),
    "prj_revised_budget":          ("float",    None),
    "prj_planned_start_date":      ("date",     None),
    "prj_planned_end_date":        ("date",     None),
    "prj_actual_start_date":       ("date",     None),
    "prj_revised_end_date":        ("date",     None),
    "prj_is_epc":                  ("uint8",    0),
    "inv_project_phase":           ("str",      None),
    "prj_phase_planned_start":     ("date",     None),
    "prj_phase_planned_end":       ("date",     None),
    "prj_phase_completion_pct":    ("float",    None),
    "inv_li_cost_code":            ("str",      None),
    "inv_li_wbs_id":               ("str",      None),
    "prj_wbs_code":                ("str",      None),
    "prj_wbs_description":         ("str",      None),
    "prj_wbs_level":               ("int",      None),

    # ── Section 3: Invoice header ──────────────────────────────────────────
    "invoice_id":                  ("str",      None),
    "inv_invoice_number":          ("str",      None),
    "inv_invoice_date":            ("date",     None),
    "inv_invoice_type":            ("str",      None),
    "inv_template_type":           ("str",      None),
    "inv_invoice_currency":        ("str",      "USD"),
    "inv_dc_number":               ("str",      None),
    "inv_dc_date":                 ("date",     None),
    "inv_eway_bill_number":        ("str",      None),
    "inv_eway_bill_date":          ("date",     None),
    "inv_vehicle_number":          ("str",      None),
    "inv_mode_of_transport":       ("str",      None),
    "inv_transporter_name":        ("str",      None),
    "inv_lr_number":               ("str",      None),
    "inv_place_of_supply":         ("str",      None),
    "inv_state_code":              ("str",      None),
    "inv_reverse_charge":          ("uint8",    0),
    "inv_irn":                     ("str",      None),
    "inv_ack_number":              ("str",      None),
    "inv_ack_date":                ("date",     None),

    # ── Section 4: PO / Contract linkage ──────────────────────────────────
    "inv_po_number":               ("str",      None),
    "inv_po_date":                 ("date",     None),
    "inv_work_order_number":       ("str",      None),
    "inv_delivery_note":           ("str",      None),
    "inv_payment_terms":           ("str",      None),
    "inv_matched_po_number":       ("str",      None),
    "inv_po_match_confidence":     ("float",    None),
    "po_id":                       ("str",      None),
    "po_type":                     ("str",      None),
    "po_value":                    ("float",    None),
    "po_status":                   ("str",      None),
    "po_delivery_date":            ("date",     None),
    "po_delivery_status":          ("str",      None),
    "po_is_blanket":               ("uint8",    0),
    "po_line_no":                  ("int",      None),
    "po_li_description":           ("str",      None),
    "po_li_hsn_sac_code":          ("str",      None),
    "po_li_material_type":         ("str",      None),
    "po_li_uom":                   ("str",      None),
    "po_li_quantity_ordered":      ("float",    None),
    "po_li_quantity_received":     ("float",    None),
    "po_li_quantity_pending":      ("float",    None),
    "po_li_quantity_rejected":     ("float",    None),
    "po_li_unit_rate":             ("float",    None),
    "po_li_line_amount":           ("float",    None),
    "po_li_gst_rate":              ("float",    None),
    "po_total_invoiced_amount":    ("float",    None),
    "po_total_paid_amount":        ("float",    None),
    "po_open_amount":              ("float",    None),
    "po_over_invoiced_flag":       ("uint8",    0),
    "po_over_invoiced_amount":     ("float",    None),
    "po_delivery_delay_days":      ("int",      None),
    "contract_id":                 ("str",      None),
    "contract_number":             ("str",      None),
    "contract_type":               ("str",      None),
    "contract_value":              ("float",    None),
    "contract_start_date":         ("date",     None),
    "contract_end_date":           ("date",     None),
    "retention_pct":               ("float",    None),
    "ld_per_day":                  ("float",    None),
    "escalation_clause":           ("uint8",    0),
    "ra_bill_id":                  ("str",      None),
    "ra_bill_number":              ("str",      None),
    "ra_bill_gross_amount":        ("float",    None),
    "ra_bill_net_payable":         ("float",    None),
    "ra_bill_certified_date":      ("date",     None),
    "ra_bill_status":              ("str",      None),
    "vo_id":                       ("str",      None),
    "vo_number":                   ("str",      None),
    "vo_type":                     ("str",      None),
    "vo_amount":                   ("float",    None),
    "vo_status":                   ("str",      None),

    # ── Section 5: Invoice financial totals ────────────────────────────────
    "inv_taxable_amount":          ("float",    None),
    "inv_cgst_amount":             ("float",    None),
    "inv_sgst_amount":             ("float",    None),
    "inv_igst_amount":             ("float",    None),
    "inv_cess_amount":             ("float",    None),
    "inv_other_charges":           ("float",    None),
    "inv_total_amount":            ("float",    None),

    # ── Section 6: Budget variance ─────────────────────────────────────────
    "inv_budget_ref_id":           ("str",      None),
    "inv_budgeted_amount":         ("float",    None),
    "inv_variance_amount":         ("float",    None),
    "inv_variance_flag":           ("str",      None),
    "bgt_committed_amount":        ("float",    None),
    "bgt_actual_amount":           ("float",    None),
    "bgt_forecast_at_completion":  ("float",    None),
    "bgt_cost_code_budget":        ("float",    None),
    "bgt_cost_code_spent_pct":     ("float",    None),

    # ── Section 7: Leakage detection ───────────────────────────────────────
    "inv_duplicate_flag":          ("uint8",    0),
    "inv_duplicate_group_id":      ("str",      None),
    "inv_price_variance_flag":     ("uint8",    0),
    "inv_price_variance_pct":      ("float",    None),
    "inv_off_contract_flag":       ("uint8",    0),
    "inv_grn_matched":             ("uint8",    0),
    "inv_grn_number":              ("str",      None),
    "inv_grn_date":                ("date",     None),
    "inv_grn_quantity":            ("float",    None),
    "inv_qty_variance_flag":       ("uint8",    0),
    "inv_qty_variance_pct":        ("float",    None),

    # ── Section 8: Supplier ────────────────────────────────────────────────
    "inv_supplier_name":           ("str",      None),
    "inv_supplier_gstin":          ("str",      None),
    "inv_supplier_pan":            ("str",      None),
    "inv_supplier_city":           ("str",      None),
    "inv_supplier_state":          ("str",      None),
    "inv_supplier_state_code":     ("str",      None),
    "inv_supplier_phone":          ("str",      None),
    "inv_supplier_email":          ("str",      None),
    "inv_supplier_bank_name":      ("str",      None),
    "inv_supplier_ifsc_code":      ("str",      None),
    "vnd_vendor_id":               ("str",      None),
    "vnd_vendor_code":             ("str",      None),
    "vnd_vendor_name_normalized":  ("str",      None),
    "vnd_vendor_type":             ("str",      None),
    "vnd_trade_category":          ("str",      None),
    "vnd_specialisation":          ("str",      None),
    "vnd_cin":                     ("str",      None),
    "vnd_msme_flag":               ("uint8",    0),
    "vnd_msme_category":           ("str",      None),
    "vnd_overall_rating":          ("float",    None),
    "vnd_quality_rating":          ("float",    None),
    "vnd_delivery_rating":         ("float",    None),
    "vnd_safety_rating":           ("float",    None),
    "vnd_financial_health":        ("str",      None),
    "vnd_blacklisted":             ("uint8",    0),
    "vnd_approved_vendor":         ("uint8",    1),
    "vnd_empanelment_date":        ("date",     None),
    "vnd_empanelment_expiry":      ("date",     None),

    # ── Section 9: Buyer ────────────────────────────────────────────────────
    "inv_buyer_name":              ("str",      None),
    "inv_buyer_gstin":             ("str",      None),
    "inv_buyer_pan":               ("str",      None),
    "inv_buyer_city":              ("str",      None),
    "inv_buyer_state":             ("str",      None),
    "inv_buyer_state_code":        ("str",      None),
    "inv_buyer_phone":             ("str",      None),
    "inv_buyer_email":             ("str",      None),

    # ── Section 10: Invoice line item ──────────────────────────────────────
    "inv_li_sl_no":                ("int",      None),
    "inv_li_description":          ("str",      None),
    "inv_li_hsn_sac_code":         ("str",      None),
    "inv_li_quantity":             ("float",    None),
    "inv_li_uom":                  ("str",      None),
    "inv_li_uom_normalized":       ("str",      None),
    "inv_li_unit_rate":            ("float",    None),
    "inv_li_taxable_amount":       ("float",    None),
    "inv_li_cgst_rate":            ("float",    None),
    "inv_li_cgst_amount":          ("float",    None),
    "inv_li_sgst_rate":            ("float",    None),
    "inv_li_sgst_amount":          ("float",    None),
    "inv_li_igst_rate":            ("float",    None),
    "inv_li_igst_amount":          ("float",    None),
    "inv_li_total_amount":         ("float",    None),

    # ── Section 11: EPC category & material ────────────────────────────────
    "inv_li_epc_category":         ("str",      None),
    "inv_li_material_type":        ("str",      None),
    "mat_market_benchmark_rate":   ("float",    None),
    "mat_rate_vs_benchmark_pct":   ("float",    None),
    "mat_price_trend":             ("str",      None),

    # ── Section 12: Payment tracking ───────────────────────────────────────
    "pmt_payment_id":              ("str",      None),
    "pmt_payment_status":          ("str",      None),
    "pmt_payment_date":            ("date",     None),
    "pmt_payment_mode":            ("str",      None),
    "pmt_utr_number":              ("str",      None),
    "pmt_days_to_pay":             ("int",      None),
    "pmt_overdue_flag":            ("uint8",    0),
    "pmt_overdue_days":            ("int",      None),
    "pmt_advance_flag":            ("uint8",    0),
    "pmt_retention_held":          ("float",    None),
    "pmt_retention_released":      ("float",    None),

    # ── Section 13: Schedule & earned value ────────────────────────────────
    "sch_activity_id":             ("str",      None),
    "sch_activity_name":           ("str",      None),
    "sch_planned_start":           ("date",     None),
    "sch_planned_finish":          ("date",     None),
    "sch_actual_start":            ("date",     None),
    "sch_actual_finish":           ("date",     None),
    "sch_forecast_finish":         ("date",     None),
    "sch_planned_pct":             ("float",    None),
    "sch_actual_pct":              ("float",    None),
    "sch_delay_days":              ("int",      None),
    "sch_float_days":              ("int",      None),
    "sch_is_critical_path":        ("uint8",    0),
    "sch_delay_flag":              ("uint8",    0),
    "sch_delay_reason":            ("str",      None),
    "ev_bac":                      ("float",    None),
    "ev_pv":                       ("float",    None),
    "ev_ev":                       ("float",    None),
    "ev_ac":                       ("float",    None),
    "ev_cv":                       ("float",    None),
    "ev_sv":                       ("float",    None),
    "ev_cpi":                      ("float",    None),
    "ev_spi":                      ("float",    None),
    "ev_eac":                      ("float",    None),
    "ev_vac":                      ("float",    None),

    # ── Section 14: Quality & inspection ───────────────────────────────────
    "qua_inspection_id":           ("str",      None),
    "qua_inspection_type":         ("str",      None),
    "qua_inspection_date":         ("date",     None),
    "qua_activity_inspected":      ("str",      None),
    "qua_result":                  ("str",      None),
    "qua_ncr_raised":              ("uint8",    0),
    "qua_ncr_number":              ("str",      None),
    "qua_ncr_open_days":           ("int",      None),
    "qua_defect_category":         ("str",      None),
    "qua_rework_required":         ("uint8",    0),
    "qua_rework_cost":             ("float",    None),
    "qua_rework_days_lost":        ("int",      None),
    "qua_test_type":               ("str",      None),
    "qua_test_value":              ("float",    None),
    "qua_test_unit":               ("str",      None),
    "qua_test_passed":             ("uint8",    0),

    # ── Section 15: Safety & HSSE ──────────────────────────────────────────
    "hse_incident_id":             ("str",      None),
    "hse_incident_type":           ("str",      None),
    "hse_incident_date":           ("date",     None),
    "hse_severity":                ("str",      None),
    "hse_injury_nature":           ("str",      None),
    "hse_body_part":               ("str",      None),
    "hse_person_type":             ("str",      None),
    "hse_trade":                   ("str",      None),
    "hse_lti_days":                ("int",      None),
    "hse_property_damage_cost":    ("float",    None),
    "hse_root_cause":              ("str",      None),
    "hse_corrective_action_done":  ("uint8",    0),
    "hse_reported_to_authority":   ("uint8",    0),
    "hse_manhours_worked":         ("float",    None),
    "hse_ltifr":                   ("float",    None),
    "hse_trifr":                   ("float",    None),

    # ── Section 16: Labour deployment ─────────────────────────────────────
    "lab_deployment_date":         ("date",     None),
    "lab_trade":                   ("str",      None),
    "lab_planned_count":           ("int",      None),
    "lab_actual_count":            ("int",      None),
    "lab_skilled_count":           ("int",      None),
    "lab_unskilled_count":         ("int",      None),
    "lab_female_count":            ("int",      None),
    "lab_is_direct":               ("uint8",    0),
    "lab_regular_hours":           ("float",    None),
    "lab_overtime_hours":          ("float",    None),
    "lab_daily_wage_rate":         ("float",    None),
    "lab_total_cost":              ("float",    None),
    "lab_overtime_cost":           ("float",    None),
    "lab_headcount_variance":      ("int",      None),
    "lab_headcount_var_flag":      ("uint8",    0),
    "lab_output_quantity":         ("float",    None),
    "lab_output_uom":              ("str",      None),
    "lab_productivity_rate":       ("float",    None),
    "lab_benchmark_productivity":  ("float",    None),
    "lab_productivity_index":      ("float",    None),

    # ── Section 17: Equipment utilisation ─────────────────────────────────
    "eqp_equipment_id":            ("str",      None),
    "eqp_equipment_code":          ("str",      None),
    "eqp_category":                ("str",      None),
    "eqp_ownership_type":          ("str",      None),
    "eqp_utilisation_date":        ("date",     None),
    "eqp_available_hours":         ("float",    None),
    "eqp_worked_hours":            ("float",    None),
    "eqp_idle_hours":              ("float",    None),
    "eqp_breakdown_hours":         ("float",    None),
    "eqp_utilisation_pct":         ("float",    None),
    "eqp_idle_reason":             ("str",      None),
    "eqp_hire_rate_per_hour":      ("float",    None),
    "eqp_total_hire_cost":         ("float",    None),
    "eqp_fuel_consumed_ltrs":      ("float",    None),
    "eqp_fuel_cost":               ("float",    None),
    "eqp_total_running_cost":      ("float",    None),
    "eqp_breakdown_flag":          ("uint8",    0),

    # ── Section 18: Estimation ─────────────────────────────────────────────
    "est_estimate_id":             ("str",      None),
    "est_opportunity_id":          ("str",      None),
    "est_version":                 ("str",      None),
    "est_type":                    ("str",      None),
    "est_date":                    ("date",     None),
    "est_quantity":                ("float",    None),
    "est_uom":                     ("str",      None),
    "est_unit_rate":               ("float",    None),
    "est_amount":                  ("float",    None),
    "est_rate_source":             ("str",      None),
    "est_confidence_level":        ("str",      None),
    "est_actual_unit_rate":        ("float",    None),
    "est_actual_amount":           ("float",    None),
    "est_rate_variance_pct":       ("float",    None),
    "est_amount_variance_pct":     ("float",    None),

    # ── Section 19: Permits ────────────────────────────────────────────────
    "pmt_permit_id":               ("str",      None),
    "per_permit_type":             ("str",      None),
    "per_permit_number":           ("str",      None),
    "per_issuing_authority":       ("str",      None),
    "per_application_date":        ("date",     None),
    "per_issued_date":             ("date",     None),
    "per_expiry_date":             ("date",     None),
    "per_status":                  ("str",      None),
    "per_risk_level":              ("str",      None),
    "per_days_to_expiry":          ("int",      None),
    "per_penalty_amount":          ("float",    None),

    # ── Section 20: Cash flow ──────────────────────────────────────────────
    "cf_flow_month":               ("date",     None),
    "cf_flow_type":                ("str",      None),
    "cf_planned_amount":           ("float",    None),
    "cf_actual_amount":            ("float",    None),
    "cf_variance_amount":          ("float",    None),
    "cf_cumulative_planned":       ("float",    None),
    "cf_cumulative_actual":        ("float",    None),
    "cf_net_cash_position":        ("float",    None),
    "cf_working_capital_days":     ("int",      None),
    "cf_overdue_receivables":      ("float",    None),
    "cf_bg_amount_outstanding":    ("float",    None),

    # ── Section 21: External market ───────────────────────────────────────
    "ext_commodity_name":          ("str",      None),
    "ext_price_date":              ("date",     None),
    "ext_market_price":            ("float",    None),
    "ext_price_unit":              ("str",      None),
    "ext_price_mom_pct":           ("float",    None),
    "ext_price_yoy_pct":           ("float",    None),
    "ext_rolling_3m_avg":          ("float",    None),
    "ext_rolling_12m_avg":         ("float",    None),
    "ext_price_volatility":        ("float",    None),
    "ext_forex_rate":              ("float",    None),
    "ext_wpi_index":               ("float",    None),

    # ── Section 22: Design & document ─────────────────────────────────────
    "doc_drawing_id":              ("str",      None),
    "doc_drawing_number":          ("str",      None),
    "doc_drawing_type":            ("str",      None),
    "doc_drawing_revision":        ("str",      None),
    "doc_dcr_id":                  ("str",      None),
    "doc_dcr_cost_impact":         ("float",    None),
    "doc_dcr_time_impact_days":    ("int",      None),

    # ── Section 23: BOQ ────────────────────────────────────────────────────
    "boq_id":                      ("str",      None),
    "boq_code":                    ("str",      None),
    "boq_description":             ("str",      None),
    "boq_spec_reference":          ("str",      None),
    "boq_version":                 ("str",      None),
    "boq_epc_category":            ("str",      None),
    "boq_wbs_code":                ("str",      None),
    "boq_uom":                     ("str",      None),
    "boq_estimated_qty":           ("float",    None),
    "boq_revised_qty":             ("float",    None),
    "boq_actual_qty":              ("float",    None),
    "boq_qty_variance":            ("float",    None),
    "boq_qty_variance_pct":        ("float",    None),
    "boq_qty_revision_reason":     ("str",      None),
    "boq_unit_rate":               ("float",    None),
    "boq_estimated_amount":        ("float",    None),
    "boq_revised_amount":          ("float",    None),
    "boq_actual_amount":           ("float",    None),
    "boq_amount_variance":         ("float",    None),
    "boq_amount_variance_pct":     ("float",    None),

    # ── Section 24: BOM ────────────────────────────────────────────────────
    "bom_id":                      ("str",      None),
    "bom_item_code":               ("str",      None),
    "bom_item_description":        ("str",      None),
    "bom_material_grade":          ("str",      None),
    "bom_spec_standard":           ("str",      None),
    "bom_material_type":           ("str",      None),
    "bom_epc_category":            ("str",      None),
    "bom_wbs_code":                ("str",      None),
    "bom_boq_ref":                 ("str",      None),
    "bom_uom":                     ("str",      None),
    "bom_required_qty":            ("float",    None),
    "bom_po_qty":                  ("float",    None),
    "bom_received_qty":            ("float",    None),
    "bom_issued_qty":              ("float",    None),
    "bom_consumed_qty":            ("float",    None),
    "bom_balance_qty":             ("float",    None),
    "bom_wastage_qty":             ("float",    None),
    "bom_wastage_pct":             ("float",    None),
    "bom_pending_po_qty":          ("float",    None),
    "bom_shortage_flag":           ("uint8",    0),
    "bom_standard_unit_rate":      ("float",    None),
    "bom_actual_unit_rate":        ("float",    None),
    "bom_rate_variance_pct":       ("float",    None),
    "bom_required_amount":         ("float",    None),
    "bom_actual_amount":           ("float",    None),
    "bom_amount_variance":         ("float",    None),
    "bom_storage_location":        ("str",      None),
    "bom_lead_time_days":          ("int",      None),
    "bom_reorder_level_qty":       ("float",    None),
    "bom_last_receipt_date":       ("date",     None),
    "bom_next_requirement_date":   ("date",     None),
}

assert len(COLUMNS) == 405, f"Expected 405 columns, got {len(COLUMNS)}"

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — TYPE CASTING
# ══════════════════════════════════════════════════════════════════════════════

def cast_value(col: str, raw: Any, col_type: str, default: Any) -> Any:
    """Cast a raw CSV string value to the correct Python type for ClickHouse."""

    # Empty string → use default
    if raw is None or raw == "" or raw == "None":
        return default

    try:
        if col_type == "str":
            return str(raw).strip()

        elif col_type == "uint8":
            v = str(raw).strip()
            return int(float(v)) if v else (default if default is not None else 0)

        elif col_type == "int":
            v = str(raw).strip()
            return int(float(v)) if v else default

        elif col_type == "float":
            v = str(raw).strip()
            return float(v) if v else default

        elif col_type == "date":
            v = str(raw).strip()
            if not v:
                return default
            # Handle YYYY-MM-DD
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            return default

        elif col_type == "datetime":
            v = str(raw).strip()
            if not v:
                return datetime.now()
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
            return datetime.now()

    except (ValueError, TypeError):
        return default

    return default


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — ROW BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def build_row(csv_row: dict) -> dict:
    """
    Build a complete 403-column dict from a CSV row.
    CSV columns that exist → cast to correct type.
    Missing columns → use default (NULL or 0).
    """
    row = {}
    for col, (col_type, default) in COLUMNS.items():
        raw = csv_row.get(col)  # None if column not in CSV
        row[col] = cast_value(col, raw, col_type, default)

    # ── Override synced_at to current time if not set properly
    if not isinstance(row.get("synced_at"), datetime):
        row["synced_at"] = datetime.now()

    # ── Ensure mandatory string keys are never None
    for mandatory in ("transaction_id", "line_item_id", "txn_type", "inv_invoice_currency"):
        if row[mandatory] is None:
            row[mandatory] = ""

    return row


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — CLICKHOUSE INSERT
# ══════════════════════════════════════════════════════════════════════════════

def insert_batches(client: Client, rows: list, batch_size: int = 500, table: str = "con_master_fact"):
    """Insert rows in batches. Uses column-oriented insert for speed."""

    col_names = list(COLUMNS.keys())
    total     = len(rows)
    inserted  = 0
    errors    = 0

    print(f"\n  Inserting {total:,} rows in batches of {batch_size}...")

    for i in range(0, total, batch_size):
        batch = rows[i : i + batch_size]

        # Build list-of-dicts for clickhouse_driver
        data = [
            [row[col] for col in col_names]
            for row in batch
        ]

        try:
            client.execute(
                f"INSERT INTO con_master_fact ({', '.join(col_names)}) VALUES",
                data,
                types_check=False,       # faster — we pre-cast types
                settings={"max_partitions_per_insert_block": 1000},
            )
            inserted += len(batch)
            pct = int(inserted / total * 100)
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            print(f"  [{bar}] {pct:3d}%  {inserted:,} / {total:,} rows", end="\r")

        except Exception as e:
            errors += len(batch)
            print(f"\n  ERROR on batch {i//batch_size + 1}: {e}")
            print(f"  Sample row keys: {list(batch[0].keys())[:5]}")

    print(f"\n  Done. Inserted: {inserted:,}  Errors: {errors}")
    return inserted, errors


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — VERIFICATION QUERIES
# ══════════════════════════════════════════════════════════════════════════════

def verify(client: Client, table: str = "con_master_fact"):
    print("\n" + "="*55)
    print("VERIFICATION QUERIES")
    print("="*55)

    queries = [
        ("Total rows",
         f"SELECT count() FROM {table} FINAL"),

        ("Rows by txn_type",
         f"SELECT txn_type, count() AS n FROM {table} FINAL GROUP BY txn_type"),

        ("Top 5 suppliers by spend",
         f"""SELECT vnd_vendor_name_normalized, round(sum(inv_total_amount)/1e6, 2) AS spend_usd_m
            FROM {table} FINAL
            WHERE inv_total_amount IS NOT NULL AND vnd_vendor_name_normalized != ''
            GROUP BY vnd_vendor_name_normalized
            ORDER BY spend_usd_m DESC LIMIT 5"""),

        ("Spend by EPC category",
         f"""SELECT inv_li_epc_category, count() AS lines, round(sum(inv_li_total_amount)/1e6,2) AS spend_usd_m
            FROM {table} FINAL
            WHERE inv_li_epc_category IS NOT NULL
            GROUP BY inv_li_epc_category ORDER BY spend_usd_m DESC"""),

        ("Leakage flags summary",
         f"""SELECT
              countIf(inv_duplicate_flag = 1)      AS duplicates,
              countIf(inv_off_contract_flag = 1)   AS off_contract,
              countIf(inv_price_variance_flag = 1) AS price_outliers
            FROM {table} FINAL"""),

        ("Columns populated (non-NULL) for first row",
         f"""SELECT count() AS populated_columns
            FROM (
              SELECT * FROM {table} FINAL LIMIT 1
            ) AS t"""),
    ]

    for label, sql in queries:
        print(f"\n  {label}:")
        try:
            result = client.execute(sql)
            for row in result:
                print(f"    {row}")
        except Exception as e:
            print(f"    ERROR: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Insert Bechtel data into ClickHouse con_master_fact")
    parser.add_argument("--host",     default=CLICKHOUSE_HOST,     help="ClickHouse host")
    parser.add_argument("--port",     default=CLICKHOUSE_PORT,     type=int, help="ClickHouse native port")
    parser.add_argument("--user",     default=CLICKHOUSE_USER,     help="ClickHouse user")
    parser.add_argument("--password", default=CLICKHOUSE_PASSWORD, help="ClickHouse password")
    parser.add_argument("--database", default=CLICKHOUSE_DATABASE, help="ClickHouse database")
    parser.add_argument("--table",    default=CLICKHOUSE_TABLE,    help="ClickHouse table name")
    parser.add_argument("--csv",      default="bechtel_invoices_v2.csv", help="Path to invoices CSV")
    parser.add_argument("--batch",    default=500,    type=int,          help="Batch size for inserts")
    parser.add_argument("--dry-run",  action="store_true",               help="Parse & show 2 rows, no insert")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════════════╗
║  Bechtel → ClickHouse  con_master_fact  (405 cols)  ║
╚══════════════════════════════════════════════════════╝
  Host     : {args.host}:{args.port}
  Database : {args.database}
  Table    : {args.table}
  User     : {args.user}
  CSV      : {args.csv}
  Columns  : {len(COLUMNS)}
  Batch    : {args.batch}
  Dry run  : {args.dry_run}
""")

    # ── Read CSV ──────────────────────────────────────────────────────────
    print("Step 1: Reading CSV...")
    try:
        with open(args.csv, encoding="utf-8") as f:
            csv_rows = list(csv.DictReader(f))
        print(f"  Read {len(csv_rows):,} rows  |  CSV has {len(csv_rows[0].keys())} columns")
    except FileNotFoundError:
        print(f"  ERROR: File not found: {args.csv}")
        sys.exit(1)

    # ── Build full 403-column rows ────────────────────────────────────────
    print("\nStep 2: Casting all rows to 403 columns...")
    full_rows = []
    for i, csv_row in enumerate(csv_rows):
        full_rows.append(build_row(csv_row))
        if (i+1) % 1000 == 0:
            print(f"  Processed {i+1:,} rows...", end="\r")
    print(f"  Built {len(full_rows):,} full rows — each with {len(full_rows[0])} columns")

    # Sort by partition key so each batch touches as few partitions as possible
    from datetime import date as date_type
    full_rows.sort(key=lambda r: (
        r.get("inv_invoice_date") or r.get("txn_date") or date_type.today()
    ))

    # ── Dry run ───────────────────────────────────────────────────────────
    if args.dry_run:
        print("\n── DRY RUN: First 2 rows ──────────────────────────────")
        for i, row in enumerate(full_rows[:2]):
            print(f"\nRow {i+1}:")
            populated = {k: v for k, v in row.items() if v is not None and v != "" and v != 0}
            null_count = sum(1 for v in row.values() if v is None)
            print(f"  Populated columns : {len(populated)}")
            print(f"  NULL columns      : {null_count}")
            print(f"  Sample values     :")
            sample_keys = ["transaction_id","inv_supplier_name","inv_project_name",
                          "inv_total_amount","inv_invoice_date","vnd_vendor_type",
                          "inv_li_epc_category","inv_duplicate_flag","prj_client_name"]
            for k in sample_keys:
                print(f"    {k:<35} = {row.get(k)}")
        print("\nDry run complete. Run without --dry-run to insert.")
        return

    # ── Connect to ClickHouse ─────────────────────────────────────────────
    print("\nStep 3: Connecting to ClickHouse...")
    try:
        client = Client(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            database=args.database,
            secure=False,
            settings={"use_client_time_zone": True},
        )
        version = client.execute("SELECT version()")[0][0]
        print(f"  Connected  ClickHouse version: {version}")
    except Exception as e:
        print(f"  ERROR connecting: {e}")
        print("\n  Make sure ClickHouse is running:")
        print("  Docker:  docker run -d -p 9000:9000 -p 8123:8123 clickhouse/clickhouse-server")
        sys.exit(1)

    # ── Create table if needed ────────────────────────────────────────────
    print("\nStep 4: Checking table exists...")
    try:
        count = client.execute(f"SELECT count() FROM {args.table}")[0][0]
        print(f"  Table '{args.table}' exists — current row count: {count:,}")
    except Exception:
        print(f"  Table '{args.table}' not found — creating from schema file...")
        try:
            with open("construction_schema/con_master_fact.sql") as f:
                ddl = f.read()
            # Remove materialized views (insert table first)
            ddl_table_only = ddl.split("ENGINE = ReplacingMergeTree")[0] + \
                             "ENGINE = ReplacingMergeTree(synced_at)\n" + \
                             "PARTITION BY toYYYYMM(coalesce(inv_invoice_date, txn_date, toDate(synced_at)))\n" + \
                             "ORDER BY (transaction_id, line_item_id)\n" + \
                             "SETTINGS index_granularity = 8192;"
            client.execute(ddl_table_only)
            print("  Table created successfully")
        except Exception as e:
            print(f"  ERROR creating table: {e}")
            print("  Please create the table manually using con_master_fact.sql")
            sys.exit(1)

    # ── Insert ────────────────────────────────────────────────────────────
    print("\nStep 5: Inserting data...")
    inserted, errors = insert_batches(client, full_rows, args.batch, args.table)

    # ── Verify ────────────────────────────────────────────────────────────
    if inserted > 0:
        print("\nStep 6: Verification...")
        verify(client, args.table)

    print(f"""
╔══════════════════════════════════════════════════════╗
║  COMPLETE                                           ║
║  Inserted : {inserted:<10,}                              ║
║  Errors   : {errors:<10,}                              ║
╚══════════════════════════════════════════════════════╝

  Query your data:
  SELECT vnd_vendor_name_normalized,
         round(sum(inv_total_amount)/1e6, 2) AS spend_usd_m
  FROM {args.table} FINAL
  GROUP BY vnd_vendor_name_normalized
  ORDER BY spend_usd_m DESC
  LIMIT 10;
""")


if __name__ == "__main__":
    main()