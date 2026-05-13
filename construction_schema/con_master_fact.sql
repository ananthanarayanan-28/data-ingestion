-- =============================================================================
-- CONSTRUCTION / EPC INTELLIGENCE PLATFORM
-- Single Master Fact Table — ClickHouse
-- =============================================================================
--
-- One row per transaction line item. Every dimension from every project phase
-- is denormalised into this single table.
--
-- Design principles (same as original inv_fact_line_items):
--   ReplacingMergeTree(synced_at)  — safe incremental upsert; newer synced_at wins
--   Always query with FINAL        — SELECT ... FROM con_master_fact FINAL
--   PARTITION BY invoice month     — coalesce fallback for missing dates
--
-- Row identity:
--   Every row is uniquely identified by (transaction_id, line_item_id)
--   transaction_id covers all transaction types:
--     INV-{uuid}   invoice line
--     PO-{uuid}    purchase order line
--     RA-{uuid}    running account bill line
--     VO-{uuid}    variation order line
--     GRN-{uuid}   goods receipt note line
--     EST-{uuid}   estimate line
--     PRG-{uuid}   progress / earned value entry
--     LAB-{uuid}   labour deployment entry
--     EQP-{uuid}   equipment utilisation entry
--     INC-{uuid}   safety incident entry
--     QUA-{uuid}   quality inspection entry
--
-- Column tiers:
--   [EXTRACTED]  populated by document extractor / field capture; present immediately
--   [DERIVED]    computed from extracted data alone; no external source needed
--   [ENRICHED]   NULL until external master data arrives; enrichment job re-inserts rows
--
-- Migrating from inv_fact_line_items:
--   All original columns are preserved with their original names.
--   New columns are appended after the original block they relate to.
--   Drop old table only after back-filling transaction_id = 'INV-' || invoice_id
-- =============================================================================

CREATE TABLE IF NOT EXISTS con_master_fact
(
    -- =========================================================================
    -- SECTION 0: DEDUP / VERSIONING KEYS
    -- =========================================================================
    transaction_id          String,                              -- INV-x | PO-x | RA-x | VO-x | GRN-x | EST-x | PRG-x | LAB-x | EQP-x | INC-x | QUA-x
    line_item_id            String,                              -- generate_id("li"); 'stub' when no line items
    synced_at               DateTime,                           -- ReplacingMergeTree version column
    row_process_id          Int64 DEFAULT 0,                    -- stable hash of (transaction_id, line_item_id); used by enrichment worker

    -- =========================================================================
    -- SECTION 1: TRANSACTION TYPE & SOURCE
    -- =========================================================================
    -- [EXTRACTED] — set at ingestion time, never changes
    txn_type                LowCardinality(String),             -- invoice | purchase_order | ra_bill | variation_order | grn | estimate | progress | labour | equipment | incident | inspection
    txn_source              LowCardinality(Nullable(String)),   -- ocr_pdf | erp_export | manual_entry | field_app | api_feed
    txn_date                Nullable(Date),                     -- canonical date for this row regardless of txn_type

    -- =========================================================================
    -- SECTION 2: PROJECT & SITE DIMENSIONS
    -- =========================================================================
    -- [EXTRACTED] raw from document
    inv_project_name        Nullable(String),
    inv_project_code        Nullable(String),
    inv_tower_number        Nullable(String),
    inv_ship_to_address     Nullable(String),
    inv_bill_to_address     Nullable(String),

    -- [ENRICHED] resolved from project master
    inv_project_id          Nullable(String),
    prj_client_id           Nullable(String),
    prj_client_name         Nullable(String),
    prj_client_type         LowCardinality(Nullable(String)),   -- developer | govt | psu | private | jv
    prj_sector              LowCardinality(Nullable(String)),   -- residential | commercial | industrial | infra | power | oil_gas
    prj_type                LowCardinality(Nullable(String)),   -- residential | commercial | industrial | epc | roads | power
    prj_contract_type       LowCardinality(Nullable(String)),   -- lump_sum | item_rate | epc | cost_plus | hybrid
    prj_status              LowCardinality(Nullable(String)),   -- pre_construction | active | on_hold | completed | cancelled
    prj_site_city           Nullable(String),
    prj_site_state          LowCardinality(Nullable(String)),
    prj_site_pin_code       Nullable(String),
    prj_total_contract_value Nullable(Float64),
    prj_original_budget     Nullable(Float64),
    prj_revised_budget      Nullable(Float64),
    prj_planned_start_date  Nullable(Date),
    prj_planned_end_date    Nullable(Date),
    prj_actual_start_date   Nullable(Date),
    prj_revised_end_date    Nullable(Date),
    prj_is_epc              UInt8 DEFAULT 0,

    -- [ENRICHED] phase
    inv_project_phase       LowCardinality(Nullable(String)),   -- foundation | structure | mep | finishing | external | handover
    prj_phase_planned_start Nullable(Date),
    prj_phase_planned_end   Nullable(Date),
    prj_phase_completion_pct Nullable(Float32),

    -- [ENRICHED] WBS / cost code
    inv_li_cost_code        Nullable(String),
    inv_li_wbs_id           Nullable(String),
    prj_wbs_code            Nullable(String),
    prj_wbs_description     Nullable(String),
    prj_wbs_level           Nullable(Int8),                    -- 1=top, 4=leaf

    -- =========================================================================
    -- SECTION 3: INVOICE HEADER  [EXTRACTED]
    -- =========================================================================
    -- Original inv_fact_line_items columns preserved verbatim
    invoice_id              Nullable(String),                   -- original invoice_id; NULL for non-invoice rows
    inv_invoice_number      Nullable(String),
    inv_invoice_date        Nullable(Date),
    inv_invoice_type        LowCardinality(Nullable(String)),   -- tax_invoice | delivery_chalan | eway_bill | proforma | credit_note
    inv_template_type       LowCardinality(Nullable(String)),
    inv_invoice_currency    LowCardinality(String) DEFAULT 'INR',

    -- Delivery chalan
    inv_dc_number           Nullable(String),
    inv_dc_date             Nullable(Date),

    -- e-Way bill
    inv_eway_bill_number    Nullable(String),
    inv_eway_bill_date      Nullable(Date),

    -- Logistics
    inv_vehicle_number      Nullable(String),
    inv_mode_of_transport   Nullable(String),
    inv_transporter_name    Nullable(String),
    inv_lr_number           Nullable(String),

    -- GST / supply
    inv_place_of_supply     Nullable(String),
    inv_state_code          Nullable(String),
    inv_reverse_charge      UInt8 DEFAULT 0,

    -- e-Invoice
    inv_irn                 Nullable(String),
    inv_ack_number          Nullable(String),
    inv_ack_date            Nullable(Date),

    -- =========================================================================
    -- SECTION 4: PO / CONTRACT LINKAGE  [EXTRACTED + ENRICHED]
    -- =========================================================================
    inv_po_number           Nullable(String),                   -- [EXTRACTED] raw from document
    inv_po_date             Nullable(Date),
    inv_work_order_number   Nullable(String),
    inv_delivery_note       Nullable(String),
    inv_payment_terms       Nullable(String),
    inv_matched_po_number   Nullable(String),                   -- [ENRICHED] fuzzy matched
    inv_po_match_confidence Nullable(Float32),                  -- [ENRICHED] 0.0–1.0

    -- [ENRICHED] from PO master — header
    po_id                   Nullable(String),
    po_type                 LowCardinality(Nullable(String)),   -- material | subcontract | service | equipment_hire
    po_value                Nullable(Float64),
    po_status               LowCardinality(Nullable(String)),   -- draft | issued | partial | fulfilled | cancelled
    po_delivery_date        Nullable(Date),
    po_delivery_status      LowCardinality(Nullable(String)),   -- pending | partial | complete | delayed
    po_is_blanket           UInt8 DEFAULT 0,                    -- 1 = blanket / rate contract PO

    -- [ENRICHED] from PO master — line level
    po_line_no              Nullable(Int32),
    po_li_description       Nullable(String),                   -- item description from PO
    po_li_hsn_sac_code      Nullable(String),
    po_li_material_type     LowCardinality(Nullable(String)),   -- steel | cement | aggregate | pipe | cable | equipment | service | other
    po_li_uom               LowCardinality(Nullable(String)),   -- MT | KG | NOS | RMT | SQM | CUM
    po_li_quantity_ordered  Nullable(Float64),
    po_li_quantity_received Nullable(Float64),
    po_li_quantity_pending  Nullable(Float64),                  -- [DERIVED] ordered - received
    po_li_quantity_rejected Nullable(Float64),
    po_li_unit_rate         Nullable(Float64),
    po_li_line_amount       Nullable(Float64),                  -- quantity_ordered × unit_rate
    po_li_gst_rate          Nullable(Float32),

    -- [ENRICHED] PO financial reconciliation
    po_total_invoiced_amount Nullable(Float64),                 -- sum of all invoices against this PO
    po_total_paid_amount    Nullable(Float64),
    po_open_amount          Nullable(Float64),                  -- [DERIVED] po_value - po_total_invoiced_amount
    po_over_invoiced_flag   UInt8 DEFAULT 0,                    -- 1 = invoiced > PO value
    po_over_invoiced_amount Nullable(Float64),                  -- excess invoiced over PO value
    po_delivery_delay_days  Nullable(Int32),                    -- actual receipt date - committed delivery date

    -- [ENRICHED] from contract master
    contract_id             Nullable(String),
    contract_number         Nullable(String),
    contract_type           LowCardinality(Nullable(String)),   -- lump_sum | item_rate | rate_contract | back_to_back
    contract_value          Nullable(Float64),
    contract_start_date     Nullable(Date),
    contract_end_date       Nullable(Date),
    retention_pct           Nullable(Float32),
    ld_per_day              Nullable(Float64),
    escalation_clause       UInt8 DEFAULT 0,

    -- [ENRICHED] RA bill linkage
    ra_bill_id              Nullable(String),
    ra_bill_number          Nullable(String),
    ra_bill_gross_amount    Nullable(Float64),
    ra_bill_net_payable     Nullable(Float64),
    ra_bill_certified_date  Nullable(Date),
    ra_bill_status          LowCardinality(Nullable(String)),   -- submitted | certified | paid | disputed

    -- [ENRICHED] Variation order linkage
    vo_id                   Nullable(String),
    vo_number               Nullable(String),
    vo_type                 LowCardinality(Nullable(String)),   -- addition | omission | substitution | extra_item
    vo_amount               Nullable(Float64),
    vo_status               LowCardinality(Nullable(String)),   -- approved | rejected | disputed

    -- =========================================================================
    -- SECTION 5: INVOICE FINANCIAL TOTALS  [EXTRACTED]
    -- =========================================================================
    inv_taxable_amount      Nullable(Float64),
    inv_cgst_amount         Nullable(Float64),
    inv_sgst_amount         Nullable(Float64),
    inv_igst_amount         Nullable(Float64),
    inv_cess_amount         Nullable(Float64),
    inv_other_charges       Nullable(Float64),
    inv_total_amount        Nullable(Float64),

    -- =========================================================================
    -- SECTION 6: BUDGET VARIANCE  [ENRICHED]
    -- =========================================================================
    inv_budget_ref_id       Nullable(String),
    inv_budgeted_amount     Nullable(Float64),
    inv_variance_amount     Nullable(Float64),                  -- inv_total_amount - inv_budgeted_amount
    inv_variance_flag       LowCardinality(Nullable(String)),   -- over | under | on_budget

    -- [ENRICHED] full earned value dimensions
    bgt_committed_amount    Nullable(Float64),                  -- PO value committed
    bgt_actual_amount       Nullable(Float64),                  -- invoiced to date
    bgt_forecast_at_completion Nullable(Float64),               -- EAC
    bgt_cost_code_budget    Nullable(Float64),                  -- total budget for this cost code
    bgt_cost_code_spent_pct Nullable(Float32),                  -- actual / budget * 100

    -- =========================================================================
    -- SECTION 7: LEAKAGE DETECTION  [DERIVED + ENRICHED]
    -- =========================================================================
    inv_duplicate_flag      UInt8 DEFAULT 0,
    inv_duplicate_group_id  Nullable(String),
    inv_price_variance_flag UInt8 DEFAULT 0,
    inv_price_variance_pct  Nullable(Float32),
    inv_off_contract_flag   UInt8 DEFAULT 0,

    -- [ENRICHED] 3-way match (invoice ↔ PO ↔ GRN)
    inv_grn_matched         UInt8 DEFAULT 0,
    inv_grn_number          Nullable(String),
    inv_grn_date            Nullable(Date),
    inv_grn_quantity        Nullable(Float64),
    inv_qty_variance_flag   UInt8 DEFAULT 0,
    inv_qty_variance_pct    Nullable(Float32),

    -- =========================================================================
    -- SECTION 8: SUPPLIER / VENDOR  [EXTRACTED + ENRICHED]
    -- =========================================================================
    -- [EXTRACTED] from document
    inv_supplier_name       Nullable(String),
    inv_supplier_gstin      Nullable(String),
    inv_supplier_pan        Nullable(String),
    inv_supplier_city       Nullable(String),
    inv_supplier_state      LowCardinality(Nullable(String)),
    inv_supplier_state_code LowCardinality(Nullable(String)),
    inv_supplier_phone      Nullable(String),
    inv_supplier_email      Nullable(String),
    inv_supplier_bank_name  Nullable(String),
    inv_supplier_ifsc_code  Nullable(String),

    -- [ENRICHED] from vendor master
    vnd_vendor_id           Nullable(String),
    vnd_vendor_code         Nullable(String),
    vnd_vendor_name_normalized LowCardinality(Nullable(String)), -- [ENRICHED] canonical clean name; resolves "L&T" / "Larsen & Toubro" / "L and T" → same entity
    vnd_vendor_type         LowCardinality(Nullable(String)),   -- supplier | subcontractor | consultant | labour_contractor | equipment_vendor
    vnd_trade_category      LowCardinality(Nullable(String)),   -- civil | structural | mep | finishing | equipment | logistics
    vnd_specialisation      Nullable(String),                   -- free text e.g. "post-tensioning, heavy formwork"
    vnd_cin                 Nullable(String),                   -- company registration number (MCA)
    vnd_msme_flag           UInt8 DEFAULT 0,
    vnd_msme_category       LowCardinality(Nullable(String)),   -- micro | small | medium
    vnd_overall_rating      Nullable(Float32),                  -- 0.0–5.0
    vnd_quality_rating      Nullable(Float32),
    vnd_delivery_rating     Nullable(Float32),
    vnd_safety_rating       Nullable(Float32),
    vnd_financial_health    LowCardinality(Nullable(String)),   -- A | B | C | D
    vnd_blacklisted         UInt8 DEFAULT 0,
    vnd_approved_vendor     UInt8 DEFAULT 1,
    vnd_empanelment_date    Nullable(Date),                     -- when vendor was first empanelled
    vnd_empanelment_expiry  Nullable(Date),

    -- =========================================================================
    -- SECTION 9: BUYER  [EXTRACTED]
    -- =========================================================================
    inv_buyer_name          Nullable(String),
    inv_buyer_gstin         Nullable(String),
    inv_buyer_pan           Nullable(String),
    inv_buyer_city          Nullable(String),
    inv_buyer_state         LowCardinality(Nullable(String)),
    inv_buyer_state_code    LowCardinality(Nullable(String)),
    inv_buyer_phone         Nullable(String),
    inv_buyer_email         Nullable(String),

    -- =========================================================================
    -- SECTION 10: INVOICE LINE ITEM  [EXTRACTED + DERIVED]
    -- =========================================================================
    inv_li_sl_no            Nullable(Int32),
    inv_li_description      Nullable(String),
    inv_li_hsn_sac_code     Nullable(String),
    inv_li_quantity         Nullable(Float64),
    inv_li_uom              Nullable(String),                   -- [EXTRACTED] raw
    inv_li_uom_normalized   LowCardinality(Nullable(String)),   -- [DERIVED] MT | KG | NOS | RMT | SQM | CUM
    inv_li_unit_rate        Nullable(Float64),
    inv_li_taxable_amount   Nullable(Float64),
    inv_li_cgst_rate        Nullable(Float64),
    inv_li_cgst_amount      Nullable(Float64),
    inv_li_sgst_rate        Nullable(Float64),
    inv_li_sgst_amount      Nullable(Float64),
    inv_li_igst_rate        Nullable(Float64),
    inv_li_igst_amount      Nullable(Float64),
    inv_li_total_amount     Nullable(Float64),

    -- =========================================================================
    -- SECTION 11: EPC CATEGORY & MATERIAL  [DERIVED / ENRICHED]
    -- =========================================================================
    inv_li_epc_category     LowCardinality(Nullable(String)),   -- civil | structural_steel | mep | equipment | subcontract | site_overheads
    inv_li_material_type    LowCardinality(Nullable(String)),   -- steel | cement | aggregate | concrete | wire | cable | pipe | block | rebar | equipment | service | other

    -- [DERIVED] price intelligence
    mat_market_benchmark_rate   Nullable(Float64),              -- from ext commodity feed
    mat_rate_vs_benchmark_pct   Nullable(Float32),              -- unit_rate vs market %
    mat_price_trend             LowCardinality(Nullable(String)), -- rising | stable | falling

    -- =========================================================================
    -- SECTION 12: PAYMENT TRACKING  [ENRICHED]
    -- =========================================================================
    pmt_payment_id          Nullable(String),
    pmt_payment_status      LowCardinality(Nullable(String)),   -- unpaid | partial | paid
    pmt_payment_date        Nullable(Date),
    pmt_payment_mode        LowCardinality(Nullable(String)),   -- neft | rtgs | cheque | upi | lc
    pmt_utr_number          Nullable(String),
    pmt_days_to_pay         Nullable(Int32),                    -- payment_date - invoice_date
    pmt_overdue_flag        UInt8 DEFAULT 0,
    pmt_overdue_days        Nullable(Int32),
    pmt_advance_flag        UInt8 DEFAULT 0,                    -- 1 = advance payment
    pmt_retention_held      Nullable(Float64),
    pmt_retention_released  Nullable(Float64),

    -- =========================================================================
    -- SECTION 13: SCHEDULE / EARNED VALUE  [ENRICHED from schedule system]
    -- =========================================================================
    sch_activity_id         Nullable(String),
    sch_activity_name       Nullable(String),
    sch_planned_start       Nullable(Date),
    sch_planned_finish      Nullable(Date),
    sch_actual_start        Nullable(Date),
    sch_actual_finish       Nullable(Date),
    sch_forecast_finish     Nullable(Date),
    sch_planned_pct         Nullable(Float32),
    sch_actual_pct          Nullable(Float32),
    sch_delay_days          Nullable(Int32),
    sch_float_days          Nullable(Int32),
    sch_is_critical_path    UInt8 DEFAULT 0,
    sch_delay_flag          UInt8 DEFAULT 0,
    sch_delay_reason        LowCardinality(Nullable(String)),   -- weather | material_shortage | labour_shortage | design_change | permission | client | other

    -- Earned value metrics
    ev_bac                  Nullable(Float64),                  -- Budget at Completion
    ev_pv                   Nullable(Float64),                  -- Planned Value
    ev_ev                   Nullable(Float64),                  -- Earned Value
    ev_ac                   Nullable(Float64),                  -- Actual Cost
    ev_cv                   Nullable(Float64),                  -- Cost Variance (EV - AC)
    ev_sv                   Nullable(Float64),                  -- Schedule Variance (EV - PV)
    ev_cpi                  Nullable(Float32),                  -- Cost Performance Index
    ev_spi                  Nullable(Float32),                  -- Schedule Performance Index
    ev_eac                  Nullable(Float64),                  -- Estimate at Completion
    ev_vac                  Nullable(Float64),                  -- Variance at Completion

    -- =========================================================================
    -- SECTION 14: QUALITY & INSPECTION  [ENRICHED from QA system / field app]
    -- =========================================================================
    qua_inspection_id       Nullable(String),
    qua_inspection_type     LowCardinality(Nullable(String)),   -- in_process | stage | final | third_party | client
    qua_inspection_date     Nullable(Date),
    qua_activity_inspected  Nullable(String),
    qua_result              LowCardinality(Nullable(String)),   -- pass | fail | conditional_pass
    qua_ncr_raised          UInt8 DEFAULT 0,
    qua_ncr_number          Nullable(String),
    qua_ncr_open_days       Nullable(Int32),
    qua_defect_category     LowCardinality(Nullable(String)),   -- structural | finishing | mep | waterproofing | safety | material
    qua_rework_required     UInt8 DEFAULT 0,
    qua_rework_cost         Nullable(Float64),
    qua_rework_days_lost    Nullable(Int32),
    qua_test_type           LowCardinality(Nullable(String)),   -- concrete_cube | soil_compaction | weld | rebar | water_pressure | electrical
    qua_test_value          Nullable(Float64),
    qua_test_unit           Nullable(String),
    qua_test_passed         UInt8 DEFAULT 0,

    -- =========================================================================
    -- SECTION 15: SAFETY & HSSE  [ENRICHED from HSE system / field app]
    -- =========================================================================
    hse_incident_id         Nullable(String),
    hse_incident_type       LowCardinality(Nullable(String)),   -- near_miss | first_aid | medical_treatment | lost_time | fatality | property_damage | environmental
    hse_incident_date       Nullable(Date),
    hse_severity            LowCardinality(Nullable(String)),   -- low | medium | high | critical
    hse_injury_nature       LowCardinality(Nullable(String)),
    hse_body_part           LowCardinality(Nullable(String)),
    hse_person_type         LowCardinality(Nullable(String)),   -- direct | subcontractor | visitor
    hse_trade               LowCardinality(Nullable(String)),
    hse_lti_days            Nullable(Int32),
    hse_property_damage_cost Nullable(Float64),
    hse_root_cause          LowCardinality(Nullable(String)),   -- unsafe_act | unsafe_condition | procedural | equipment_failure | weather
    hse_corrective_action_done UInt8 DEFAULT 0,
    hse_reported_to_authority  UInt8 DEFAULT 0,
    hse_manhours_worked     Nullable(Float64),
    hse_ltifr               Nullable(Float32),                  -- LTI Frequency Rate
    hse_trifr               Nullable(Float32),                  -- Total Recordable Injury FR

    -- =========================================================================
    -- SECTION 16: LABOUR DEPLOYMENT  [ENRICHED from field app / DPR]
    -- =========================================================================
    lab_deployment_date     Nullable(Date),
    lab_trade               LowCardinality(Nullable(String)),   -- mason | carpenter | bar_bender | electrician | plumber | welder | helper | supervisor
    lab_planned_count       Nullable(Int32),
    lab_actual_count        Nullable(Int32),
    lab_skilled_count       Nullable(Int32),
    lab_unskilled_count     Nullable(Int32),
    lab_female_count        Nullable(Int32),
    lab_is_direct           UInt8 DEFAULT 0,
    lab_regular_hours       Nullable(Float32),
    lab_overtime_hours      Nullable(Float32),
    lab_daily_wage_rate     Nullable(Float64),
    lab_total_cost          Nullable(Float64),
    lab_overtime_cost       Nullable(Float64),
    lab_headcount_variance  Nullable(Int32),                    -- actual - planned
    lab_headcount_var_flag  UInt8 DEFAULT 0,
    lab_output_quantity     Nullable(Float64),
    lab_output_uom          LowCardinality(Nullable(String)),
    lab_productivity_rate   Nullable(Float64),                  -- output per man-day
    lab_benchmark_productivity Nullable(Float64),
    lab_productivity_index  Nullable(Float32),                  -- actual / benchmark

    -- =========================================================================
    -- SECTION 17: EQUIPMENT UTILISATION  [ENRICHED from equipment log / field app]
    -- =========================================================================
    eqp_equipment_id        Nullable(String),
    eqp_equipment_code      LowCardinality(Nullable(String)),
    eqp_category            LowCardinality(Nullable(String)),   -- crane | excavator | concrete_pump | batching_plant | generator | compactor | vehicle
    eqp_ownership_type      LowCardinality(Nullable(String)),   -- owned | hired | lease
    eqp_utilisation_date    Nullable(Date),
    eqp_available_hours     Nullable(Float32),
    eqp_worked_hours        Nullable(Float32),
    eqp_idle_hours          Nullable(Float32),
    eqp_breakdown_hours     Nullable(Float32),
    eqp_utilisation_pct     Nullable(Float32),
    eqp_idle_reason         LowCardinality(Nullable(String)),   -- no_work | rain | breakdown | waiting_material | operator_absent
    eqp_hire_rate_per_hour  Nullable(Float64),
    eqp_total_hire_cost     Nullable(Float64),
    eqp_fuel_consumed_ltrs  Nullable(Float64),
    eqp_fuel_cost           Nullable(Float64),
    eqp_total_running_cost  Nullable(Float64),
    eqp_breakdown_flag      UInt8 DEFAULT 0,

    -- =========================================================================
    -- SECTION 18: ESTIMATION INTELLIGENCE  [ENRICHED from estimate register]
    -- =========================================================================
    est_estimate_id         Nullable(String),
    est_opportunity_id      Nullable(String),
    est_version             LowCardinality(Nullable(String)),   -- v1 | v2 | final
    est_type                LowCardinality(Nullable(String)),   -- preliminary | detailed | final
    est_date                Nullable(Date),
    est_quantity            Nullable(Float64),
    est_uom                 LowCardinality(Nullable(String)),
    est_unit_rate           Nullable(Float64),
    est_amount              Nullable(Float64),
    est_rate_source         LowCardinality(Nullable(String)),   -- historical | market_quote | assumption | benchmark
    est_confidence_level    LowCardinality(Nullable(String)),   -- high | medium | low
    est_actual_unit_rate    Nullable(Float64),                  -- populated at close for feedback loop
    est_actual_amount       Nullable(Float64),
    est_rate_variance_pct   Nullable(Float32),
    est_amount_variance_pct Nullable(Float32),

    -- =========================================================================
    -- SECTION 19: PERMITS & COMPLIANCE  [ENRICHED from permit register]
    -- =========================================================================
    pmt_permit_id           Nullable(String),
    per_permit_type         LowCardinality(Nullable(String)),   -- building_permit | env_clearance | fire_noc | aviation_noc | utility | labour_licence
    per_permit_number       Nullable(String),
    per_issuing_authority   Nullable(String),
    per_application_date    Nullable(Date),
    per_issued_date         Nullable(Date),
    per_expiry_date         Nullable(Date),
    per_status              LowCardinality(Nullable(String)),   -- not_applied | applied | under_review | issued | expired | rejected
    per_risk_level          LowCardinality(Nullable(String)),   -- low | medium | high | critical
    per_days_to_expiry      Nullable(Int32),
    per_penalty_amount      Nullable(Float64),

    -- =========================================================================
    -- SECTION 20: CASH FLOW  [ENRICHED from finance system]
    -- =========================================================================
    cf_flow_month           Nullable(Date),                     -- first day of month
    cf_flow_type            LowCardinality(Nullable(String)),   -- outflow | inflow
    cf_planned_amount       Nullable(Float64),
    cf_actual_amount        Nullable(Float64),
    cf_variance_amount      Nullable(Float64),
    cf_cumulative_planned   Nullable(Float64),
    cf_cumulative_actual    Nullable(Float64),
    cf_net_cash_position    Nullable(Float64),
    cf_working_capital_days Nullable(Int32),
    cf_overdue_receivables  Nullable(Float64),
    cf_bg_amount_outstanding Nullable(Float64),                 -- bank guarantee exposure

    -- =========================================================================
    -- SECTION 21: EXTERNAL / MARKET  [ENRICHED from commodity feed]
    -- =========================================================================
    ext_commodity_name      LowCardinality(Nullable(String)),   -- steel_tmt | cement_opc | copper_wire | diesel | aggregate
    ext_price_date          Nullable(Date),
    ext_market_price        Nullable(Float64),
    ext_price_unit          LowCardinality(Nullable(String)),
    ext_price_mom_pct       Nullable(Float32),                  -- month-over-month change %
    ext_price_yoy_pct       Nullable(Float32),                  -- year-over-year change %
    ext_rolling_3m_avg      Nullable(Float64),
    ext_rolling_12m_avg     Nullable(Float64),
    ext_price_volatility    Nullable(Float32),                  -- 30-day volatility index
    ext_forex_rate          Nullable(Float64),                  -- USD/INR for imported items
    ext_wpi_index           Nullable(Float64),                  -- Wholesale Price Index

    -- =========================================================================
    -- SECTION 22: DESIGN & DOCUMENT LINKAGE  [ENRICHED]
    -- =========================================================================
    doc_drawing_id          Nullable(String),
    doc_drawing_number      Nullable(String),
    doc_drawing_type        LowCardinality(Nullable(String)),   -- architectural | structural | mep | civil
    doc_drawing_revision    Nullable(String),
    doc_dcr_id              Nullable(String),                   -- design change request
    doc_dcr_cost_impact     Nullable(Float64),
    doc_dcr_time_impact_days Nullable(Int32),

    -- =========================================================================
    -- SECTION 23: BOQ — BILL OF QUANTITIES  [ENRICHED from BOQ register]
    -- =========================================================================
    -- Identification
    boq_id                  Nullable(String),
    boq_code                Nullable(String),                   -- BOQ item reference e.g. "3.2.1.4"
    boq_description         Nullable(String),                   -- e.g. "M25 RCC in columns & beams"
    boq_spec_reference      Nullable(String),                   -- specification clause reference
    boq_version             LowCardinality(Nullable(String)),   -- original | revised_1 | revised_2
    boq_epc_category        LowCardinality(Nullable(String)),   -- civil | structural_steel | mep | equipment | subcontract | site_overheads
    boq_wbs_code            Nullable(String),

    -- Quantities
    boq_uom                 LowCardinality(Nullable(String)),   -- CUM | SQM | RMT | MT | KG | NOS | LS
    boq_estimated_qty       Nullable(Float64),                  -- original scoped quantity
    boq_revised_qty         Nullable(Float64),                  -- revised after VO / DCR
    boq_actual_qty          Nullable(Float64),                  -- quantity actually executed on site
    boq_qty_variance        Nullable(Float64),                  -- [DERIVED] actual - estimated
    boq_qty_variance_pct    Nullable(Float32),                  -- [DERIVED] variance / estimated * 100
    boq_qty_revision_reason LowCardinality(Nullable(String)),   -- client_change | design_change | site_condition | error_correction

    -- Rates & amounts
    boq_unit_rate           Nullable(Float64),                  -- rate per unit from BOQ
    boq_estimated_amount    Nullable(Float64),                  -- estimated_qty × unit_rate
    boq_revised_amount      Nullable(Float64),                  -- revised_qty × unit_rate
    boq_actual_amount       Nullable(Float64),                  -- actual cost billed for this BOQ item
    boq_amount_variance     Nullable(Float64),                  -- [DERIVED] actual - estimated amount
    boq_amount_variance_pct Nullable(Float32),                  -- [DERIVED] % overrun on this BOQ item

    -- =========================================================================
    -- SECTION 24: BOM — BILL OF MATERIALS  [ENRICHED from material management]
    -- =========================================================================
    -- Identification
    bom_id                  Nullable(String),
    bom_item_code           Nullable(String),                   -- material item code e.g. "STL-TMT-12-500"
    bom_item_description    Nullable(String),                   -- e.g. "TMT Fe500 12mm dia rebar"
    bom_material_grade      Nullable(String),                   -- e.g. "Fe500", "M25", "IS:2062 E250"
    bom_spec_standard       Nullable(String),                   -- IS / BS / ASTM standard reference
    bom_material_type       LowCardinality(Nullable(String)),   -- steel | cement | aggregate | concrete | wire | cable | pipe | block | rebar | equipment | service | other
    bom_epc_category        LowCardinality(Nullable(String)),
    bom_wbs_code            Nullable(String),
    bom_boq_ref             Nullable(String),                   -- link back to BOQ item this material supports

    -- Quantities
    bom_uom                 LowCardinality(Nullable(String)),   -- MT | KG | NOS | RMT | SQM | CUM | LTR
    bom_required_qty        Nullable(Float64),                  -- total quantity needed for the project / phase
    bom_po_qty              Nullable(Float64),                  -- quantity ordered via POs so far
    bom_received_qty        Nullable(Float64),                  -- quantity received at site store (GRN)
    bom_issued_qty          Nullable(Float64),                  -- quantity issued from store to site
    bom_consumed_qty        Nullable(Float64),                  -- quantity actually consumed / installed
    bom_balance_qty         Nullable(Float64),                  -- [DERIVED] received - issued (stock at hand)
    bom_wastage_qty         Nullable(Float64),                  -- [DERIVED] issued - consumed
    bom_wastage_pct         Nullable(Float32),                  -- [DERIVED] wastage / issued * 100
    bom_pending_po_qty      Nullable(Float64),                  -- [DERIVED] required - po_qty (yet to be ordered)
    bom_shortage_flag       UInt8 DEFAULT 0,                    -- 1 = received < required; material at risk

    -- Rates & amounts
    bom_standard_unit_rate  Nullable(Float64),                  -- budgeted / standard rate from estimate
    bom_actual_unit_rate    Nullable(Float64),                  -- weighted avg actual purchase rate
    bom_rate_variance_pct   Nullable(Float32),                  -- [DERIVED] (actual - standard) / standard * 100
    bom_required_amount     Nullable(Float64),                  -- required_qty × standard_unit_rate
    bom_actual_amount       Nullable(Float64),                  -- actual cost (received_qty × actual_unit_rate)
    bom_amount_variance     Nullable(Float64),                  -- [DERIVED] actual - required amount

    -- Storage & logistics
    bom_storage_location    Nullable(String),                   -- site store / yard reference
    bom_lead_time_days      Nullable(Int32),                    -- supplier lead time for this material
    bom_reorder_level_qty   Nullable(Float64),                  -- trigger reorder when balance falls below this
    bom_last_receipt_date   Nullable(Date),
    bom_next_requirement_date Nullable(Date)                    -- when next batch needed on site
)
ENGINE = ReplacingMergeTree(synced_at)
PARTITION BY toYYYYMM(coalesce(inv_invoice_date, txn_date, toDate(synced_at)))
ORDER BY (transaction_id, line_item_id)
SETTINGS index_granularity = 8192;
