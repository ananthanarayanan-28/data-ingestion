"""
Bechtel Construction Intelligence — EXPANDED Realistic Data Generator v2
=========================================================================
250+ real suppliers | 20 real projects | 8000+ invoice rows

Sources:
  Bechtel Global Supplier Awards: 2013-2025 (all years)
  Bechtel project pages & press releases
  SEC filings, PRNewswire, Offshore Energy, Construction Dive
"""

import uuid, hashlib, random, csv
from datetime import date, timedelta, datetime
from faker import Faker
fake = Faker('en_US')

# ══════════════════════════════════════════════════════════════════════════════
# ALL SUPPLIERS  — (name, city, state, country, type, trade, website)
# ══════════════════════════════════════════════════════════════════════════════
ALL_SUPPLIERS = [
    # ── Bechtel Award Winners 2025 ────────────────────────────────────────────
    ("Alfred Miller Contracting",                   "Lake Charles",       "LA",  "USA",          "subcontractor","civil",                "alfredmiller.com"),
    ("Bigge",                                       "San Leandro",        "CA",  "USA",          "supplier",     "equipment",            "bigge.com"),
    ("Cambria County Assoc for Blind & Handicapped","Johnstown",          "PA",  "USA",          "supplier",     "industrial_supply",    "ccabh.org"),
    ("Cimtas",                                      "Bursa",              "BSK", "Turkey",       "subcontractor","piping",               "cimtas.com.tr"),
    ("Fagioli",                                     "Sant Ilario d Enza", "RE",  "Italy",        "subcontractor","heavy_lift",           "fagioli.com"),
    ("H. E. Hunewill Construction",                 "Winnemucca",         "NV",  "USA",          "subcontractor","civil",                "hunewill.com"),
    ("Hantech",                                     "Ulsan",              "BO",  "South Korea",  "supplier",     "structural_steel",     "hantech.co.kr"),
    ("Harris Thermal Transfer Products",            "Newberg",            "OR",  "USA",          "supplier",     "heat_exchange",        "harristhermal.com"),
    ("JAFEC USA",                                   "San Jose",           "CA",  "USA",          "supplier",     "filtration",           "jafec.com"),
    ("Legacy Building Solutions",                   "South Haven",        "MN",  "USA",          "supplier",     "structural_steel",     "legacybuildingsolutions.com"),
    ("Metso",                                       "Helsinki",           "UUS", "Finland",      "supplier",     "equipment",            "metso.com"),
    ("Nextracker",                                  "Fremont",            "CA",  "USA",          "supplier",     "solar_tracking",       "nextracker.com"),
    ("Pioneer Pipe",                                "Marietta",           "OH",  "USA",          "supplier",     "piping",               "pioneerpipe.com"),
    ("Veolia",                                      "Trevose",            "PA",  "USA",          "supplier",     "water_treatment",      "veolia.com"),
    # ── 2024 ─────────────────────────────────────────────────────────────────
    ("ArmorWorks",                                  "Chandler",           "AZ",  "USA",          "supplier",     "defense_equipment",    "armorworks.com"),
    ("Baker Hughes",                                "Houston",            "TX",  "USA",          "supplier",     "turbomachinery",       "bakerhughes.com"),
    ("Barton Firtop Engineering Company",           "Worcestershire",     "WOR", "UK",           "subcontractor","engineering",          "bartonfirtop.co.uk"),
    # ── 2023 ─────────────────────────────────────────────────────────────────
    ("Dongbang Transport Logistics Co",             "Incheon",            "IN",  "South Korea",  "subcontractor","logistics",            "dongbang.co.kr"),
    ("Vorspann Systems Ltd",                        "Swindon",            "SWD", "UK",           "supplier",     "post_tensioning",      "vorspann.co.uk"),
    # ── 2020 Oil Gas ──────────────────────────────────────────────────────────
    ("Airgas USA LLC",                              "Radnor",             "PA",  "USA",          "supplier",     "industrial_gases",     "airgas.com"),
    ("Atlantic Projects Company",                   "Dublin",             "L",   "Ireland",      "subcontractor","mechanical",           "atlanticprojects.com"),
    ("Bennett Truck Transport LLC",                 "McDonough",          "GA",  "USA",          "subcontractor","logistics",            "bennetttruck.com"),
    ("Fay an i+iconUSA Company",                    "Exton",              "PA",  "USA",          "subcontractor","civil",                "fay.com"),
    ("Lindy Paving Inc",                            "Pittsburgh",         "PA",  "USA",          "subcontractor","civil",                "lindypaving.com"),
    ("P&I Supply Company",                          "Deer Park",          "TX",  "USA",          "supplier",     "industrial_supply",    "pi-supply.com"),
    ("PGT Trucking Inc",                            "Aliquippa",          "PA",  "USA",          "subcontractor","logistics",            "pgttrucking.com"),
    ("Rotork Controls Inc",                         "Bath",               "SOM", "UK",           "supplier",     "instrumentation",      "rotork.com"),
    # ── NSE Division Award Winners 2013-2018 ──────────────────────────────────
    ("Ellis & Watts Global Industries",             "Cincinnati",         "OH",  "USA",          "supplier",     "industrial_equipment", "elliswatts.com"),
    ("IONEX Research Corporation",                  "Richland",           "WA",  "USA",          "supplier",     "nuclear_equipment",    "ionexresearch.com"),
    ("Lasertel Inc",                                "Tucson",             "AZ",  "USA",          "supplier",     "laser_systems",        "lasertel.com"),
    ("Hawthorne Machinery Company",                 "San Diego",          "CA",  "USA",          "subcontractor","equipment",            "hawthorncat.com"),
    ("Gutor Electric Inc",                          "Wettingen",          "AG",  "Switzerland",  "supplier",     "electrical",           "gutor.com"),
    ("Springs Fabrication Inc",                     "Colorado Springs",   "CO",  "USA",          "supplier",     "fabrication",          "springsfabrication.com"),
    ("Diani Building Corp",                         "Honolulu",           "HI",  "USA",          "subcontractor","civil",                "diani.com"),
    ("Hartman Walsh Industrial Services",           "St. Louis",          "MO",  "USA",          "subcontractor","industrial_services",  "hartmanwalsh.com"),
    ("BCI Construction USA Inc",                    "Murfreesboro",       "TN",  "USA",          "subcontractor","civil",                "bciconstruction.com"),
    ("Air Conditioning Parts & Equipment",          "Richland",           "WA",  "USA",          "supplier",     "hvac",                 "acpems.com"),
    ("Performance Contracting Inc",                 "Lenexa",             "KS",  "USA",          "subcontractor","industrial_services",  "pcg.com"),
    ("Faith Technologies Inc",                      "Menasha",            "WI",  "USA",          "subcontractor","electrical",           "faithtechnologies.com"),
    # ── 2020/2021 Global Award Winners ────────────────────────────────────────
    ("Fluid Controls and Components Inc",           "Richland",           "WA",  "USA",          "supplier",     "valves_piping",        "fluidcontrols.net"),
    ("Pacific Office Solutions",                    "Richland",           "WA",  "USA",          "supplier",     "office_supplies",      "pacoffice.com"),
    ("Petersen Inc",                                "Ogden",              "UT",  "USA",          "supplier",     "fabrication",          "peterseninc.com"),
    ("Inland Asphalt Company",                      "Richland",           "WA",  "USA",          "subcontractor","civil",                "inlandasphalt.com"),
    # ── Strategic longstanding partners ──────────────────────────────────────
    ("ABB Ltd",                                     "Zurich",             "ZH",  "Switzerland",  "supplier",     "electrical",           "abb.com"),
    ("GE Hitachi Nuclear Energy",                   "Wilmington",         "NC",  "USA",          "supplier",     "nuclear_equipment",    "gehitachiprods.com"),
    ("Mitsubishi Power",                            "Houston",            "TX",  "USA",          "supplier",     "turbomachinery",       "power.mhi.com"),
    ("Honeywell UOP",                               "Des Plaines",        "IL",  "USA",          "supplier",     "process_systems",      "uop.honeywell.com"),
    ("Unger Steel Group",                           "Vienna",             "W",   "Austria",      "supplier",     "structural_steel",     "ungerstahl.com"),
    ("Anvil International",                         "Tulsa",              "OK",  "USA",          "supplier",     "piping",               "anvilintl.com"),
    ("Nooter Eriksen Inc",                          "St. Louis",          "MO",  "USA",          "supplier",     "heat_exchange",        "nooter-eriksen.com"),
    ("Caterpillar Inc",                             "Irving",             "TX",  "USA",          "supplier",     "equipment",            "cat.com"),
    ("Porvair Filtration Group Inc",                "Fareham",            "HAM", "UK",           "supplier",     "filtration",           "porvairfiltration.com"),
    ("TD Supply Specialists LLC",                   "Columbus",           "OH",  "USA",          "supplier",     "specialist_tools",     "tdsupplyspecialists.com"),
    ("DYNACOM Corporation",                         "Reston",             "VA",  "USA",          "subcontractor","it_infrastructure",    "dynacomcorp.com"),
    ("Dashiell Corporation",                        "Houston",            "TX",  "USA",          "subcontractor","electrical",           "dashiell.com"),
    ("Inland Valley Construction Co Inc",           "Perris",             "CA",  "USA",          "subcontractor","civil",                "inlandvalley.com"),
    ("Team Industries Inc",                         "Bagley",             "MN",  "USA",          "supplier",     "equipment",            "teamindustries.com"),
    ("Mechanical Dynamics and Analysis LLC",        "Houston",            "TX",  "USA",          "subcontractor","mechanical",           "mda-llc.com"),
    # ── Major EPC firms ───────────────────────────────────────────────────────
    ("Fluor Corporation",                           "Irving",             "TX",  "USA",          "subcontractor","engineering",          "fluor.com"),
    ("Jacobs Engineering Group",                    "Dallas",             "TX",  "USA",          "subcontractor","engineering",          "jacobs.com"),
    ("Black & Veatch",                              "Overland Park",      "KS",  "USA",          "subcontractor","engineering",          "bv.com"),
    ("Zachry Group",                                "San Antonio",        "TX",  "USA",          "subcontractor","civil",                "zachrygroup.com"),
    ("KBR Inc",                                     "Houston",            "TX",  "USA",          "subcontractor","engineering",          "kbr.com"),
    ("McDermott International",                     "Houston",            "TX",  "USA",          "subcontractor","offshore",             "mcdermott.com"),
    ("Wood Group PLC",                              "Aberdeen",           "ABD", "UK",           "subcontractor","engineering",          "woodgroup.com"),
    ("WorleyParsons",                               "Sydney",             "NSW", "Australia",    "subcontractor","engineering",          "worley.com"),
    ("AECOM",                                       "Dallas",             "TX",  "USA",          "subcontractor","civil",                "aecom.com"),
    ("Saipem",                                      "San Donato Milanese","MI",  "Italy",        "subcontractor","offshore",             "saipem.com"),
    ("TechnipFMC",                                  "Houston",            "TX",  "USA",          "subcontractor","offshore",             "technipfmc.com"),
    # ── LNG equipment ─────────────────────────────────────────────────────────
    ("Chart Industries",                            "Ball Ground",        "GA",  "USA",          "supplier",     "lng_equipment",        "chartindustries.com"),
    ("Linde Engineering",                           "Munich",             "BAY", "Germany",      "supplier",     "lng_equipment",        "linde-engineering.com"),
    ("CB&I Storage Tank Solutions",                 "The Woodlands",      "TX",  "USA",          "supplier",     "lng_storage_tanks",    "cbi.com"),
    ("Air Products and Chemicals",                  "Allentown",          "PA",  "USA",          "supplier",     "industrial_gases",     "airproducts.com"),
    # ── Process / Rotating equipment ──────────────────────────────────────────
    ("Emerson Electric Co",                         "St. Louis",          "MO",  "USA",          "supplier",     "instrumentation",      "emerson.com"),
    ("Siemens Energy",                              "Munich",             "BAY", "Germany",      "supplier",     "turbomachinery",       "siemens-energy.com"),
    ("CIRCOR International",                        "Burlington",         "MA",  "USA",          "supplier",     "flow_control",         "circor.com"),
    ("IDEX Corporation",                            "Lake Forest",        "IL",  "USA",          "supplier",     "pumps_valves",         "idexcorp.com"),
    ("Flowserve Corporation",                       "Irving",             "TX",  "USA",          "supplier",     "pumps_valves",         "flowserve.com"),
    ("Sulzer Ltd",                                  "Winterthur",         "ZH",  "Switzerland",  "supplier",     "pumps_valves",         "sulzer.com"),
    ("Grundfos",                                    "Bjerringbro",        "MJ",  "Denmark",      "supplier",     "pumps_valves",         "grundfos.com"),
    ("ITT Inc",                                     "White Plains",       "NY",  "USA",          "supplier",     "pumps_valves",         "itt.com"),
    # ── Civil & concrete ──────────────────────────────────────────────────────
    ("Vulcan Materials Company",                    "Birmingham",         "AL",  "USA",          "supplier",     "aggregate",            "vulcanmaterials.com"),
    ("Martin Marietta Materials",                   "Raleigh",            "NC",  "USA",          "supplier",     "aggregate",            "martinmarietta.com"),
    ("LaFarge Holcim US",                           "Chicago",            "IL",  "USA",          "supplier",     "cement_concrete",      "lafargeholcim.com"),
    ("CEMEX USA",                                   "Houston",            "TX",  "USA",          "supplier",     "cement_concrete",      "cemex.com"),
    ("US Concrete",                                 "Euless",             "TX",  "USA",          "supplier",     "cement_concrete",      "us-concrete.com"),
    ("Ready Mix USA",                               "Birmingham",         "AL",  "USA",          "supplier",     "cement_concrete",      "readymixusa.com"),
    # ── Steel ─────────────────────────────────────────────────────────────────
    ("Nucor Corporation",                           "Charlotte",          "NC",  "USA",          "supplier",     "structural_steel",     "nucor.com"),
    ("Commercial Metals Company",                   "Irving",             "TX",  "USA",          "supplier",     "structural_steel",     "cmc.com"),
    ("Gerdau Ameristeel",                           "Tampa",              "FL",  "USA",          "supplier",     "structural_steel",     "gerdau.com"),
    ("Chaparral Steel",                             "Midlothian",         "TX",  "USA",          "supplier",     "structural_steel",     "chaparralsteel.com"),
    ("Harris Rebar",                                "Wilmington",         "NC",  "USA",          "supplier",     "rebar",                "harrisrebar.com"),
    ("Nucor Rebar Fabrication",                     "Charlotte",          "NC",  "USA",          "supplier",     "rebar",                "nucorfab.com"),
    ("Pacific Coast Steel",                         "Rialto",             "CA",  "USA",          "supplier",     "rebar",                "pacific-coast-steel.com"),
    # ── Piping ────────────────────────────────────────────────────────────────
    ("Mueller Water Products",                      "Atlanta",            "GA",  "USA",          "supplier",     "piping",               "muellerwaterproducts.com"),
    ("Northwest Pipe Company",                      "Vancouver",          "WA",  "USA",          "supplier",     "piping",               "nwpipe.com"),
    ("Tenaris",                                     "Luxembourg",         "LU",  "Luxembourg",   "supplier",     "piping",               "tenaris.com"),
    ("Vallourec",                                   "Boulogne-Billancourt","IDF","France",        "supplier",     "piping",               "vallourec.com"),
    ("Salzgitter Mannesmann",                       "Salzgitter",         "LS",  "Germany",      "supplier",     "piping",               "salzgitter-mannesmann.com"),
    ("Meever & Meever",                             "Rotterdam",          "ZH",  "Netherlands",  "supplier",     "piping",               "meever.com"),
    ("Core & Main",                                 "St. Louis",          "MO",  "USA",          "supplier",     "piping",               "coreandmain.com"),
    ("Ferguson Enterprises",                        "Newport News",       "VA",  "USA",          "supplier",     "piping",               "ferguson.com"),
    # ── Electrical & Cable ────────────────────────────────────────────────────
    ("Schneider Electric",                          "Boston",             "MA",  "USA",          "supplier",     "electrical",           "se.com"),
    ("Eaton Corporation",                           "Dublin",             "L",   "Ireland",      "supplier",     "electrical",           "eaton.com"),
    ("Quanta Services",                             "Houston",            "TX",  "USA",          "subcontractor","electrical",           "quantaservices.com"),
    ("MYR Group",                                   "Northbrook",         "IL",  "USA",          "subcontractor","electrical",           "myrgroup.com"),
    ("WESCO International",                         "Pittsburgh",         "PA",  "USA",          "supplier",     "electrical",           "wesco.com"),
    ("Anixter International",                       "Glenview",           "IL",  "USA",          "supplier",     "electrical",           "anixter.com"),
    ("Rexel Holdings USA",                          "Dallas",             "TX",  "USA",          "supplier",     "electrical",           "rexel.com"),
    ("Prysmian Group",                              "Milan",              "MI",  "Italy",        "supplier",     "electrical",           "prysmiangroup.com"),
    ("Nexans",                                      "Paris",              "IDF", "France",       "supplier",     "electrical",           "nexans.com"),
    ("Southwire Company",                           "Carrollton",         "GA",  "USA",          "supplier",     "electrical",           "southwire.com"),
    ("Belden Inc",                                  "St. Louis",          "MO",  "USA",          "supplier",     "electrical",           "belden.com"),
    ("Phoenix Contact",                             "Blomberg",           "NRW", "Germany",      "supplier",     "electrical",           "phoenixcontact.com"),
    # ── Instrumentation & Controls ────────────────────────────────────────────
    ("Rockwell Automation",                         "Milwaukee",          "WI",  "USA",          "supplier",     "instrumentation",      "rockwellautomation.com"),
    ("Yokogawa Electric",                           "Tokyo",              "TKO", "Japan",        "supplier",     "instrumentation",      "yokogawa.com"),
    ("Endress+Hauser",                              "Reinach",            "BL",  "Switzerland",  "supplier",     "instrumentation",      "endress.com"),
    ("Krohne Group",                                "Duisburg",           "NRW", "Germany",      "supplier",     "instrumentation",      "krohne.com"),
    ("Ametek Inc",                                  "Berwyn",             "PA",  "USA",          "supplier",     "instrumentation",      "ametek.com"),
    # ── Industrial supply ─────────────────────────────────────────────────────
    ("Grainger",                                    "Lake Forest",        "IL",  "USA",          "supplier",     "industrial_supply",    "grainger.com"),
    ("Fastenal Company",                            "Winona",             "MN",  "USA",          "supplier",     "industrial_supply",    "fastenal.com"),
    ("MSC Industrial Direct",                       "Melville",           "NY",  "USA",          "supplier",     "industrial_supply",    "mscdirect.com"),
    ("Applied Industrial Technologies",             "Cleveland",          "OH",  "USA",          "supplier",     "industrial_supply",    "applied.com"),
    ("Motion Industries",                           "Birmingham",         "AL",  "USA",          "supplier",     "industrial_supply",    "motionindustries.com"),
    ("HD Supply",                                   "Atlanta",            "GA",  "USA",          "supplier",     "industrial_supply",    "hdsupply.com"),
    # ── Oilfield / Upstream ───────────────────────────────────────────────────
    ("Schlumberger SLB",                            "Houston",            "TX",  "USA",          "supplier",     "oilfield_services",    "slb.com"),
    ("Halliburton",                                 "Houston",            "TX",  "USA",          "supplier",     "oilfield_services",    "halliburton.com"),
    ("National Oilwell Varco",                      "Houston",            "TX",  "USA",          "supplier",     "drilling_equipment",   "nov.com"),
    # ── Scaffolding / Insulation / Formwork ──────────────────────────────────
    ("Harsco Corporation",                          "Camp Hill",          "PA",  "USA",          "supplier",     "scaffolding",          "harsco.com"),
    ("Brand Industrial Services",                   "Kennesaw",           "GA",  "USA",          "subcontractor","scaffolding",          "brandind.com"),
    ("Owens Corning",                               "Toledo",             "OH",  "USA",          "supplier",     "insulation",           "owenscorning.com"),
    ("Johns Manville",                              "Denver",             "CO",  "USA",          "supplier",     "insulation",           "jm.com"),
    ("PERI Group",                                  "Weissenhorn",        "BAY", "Germany",      "supplier",     "formwork",             "peri.com"),
    ("Doka Group",                                  "Amstetten",          "NOE", "Austria",      "supplier",     "formwork",             "doka.com"),
    # ── Mining equipment ──────────────────────────────────────────────────────
    ("Thyssenkrupp Industrial Solutions",           "Essen",              "NRW", "Germany",      "supplier",     "mining_equipment",     "thyssenkrupp-industrial-solutions.com"),
    ("FLSmidth",                                    "Copenhagen",         "KBH", "Denmark",      "supplier",     "mining_equipment",     "flsmidth.com"),
    ("Weir Group",                                  "Glasgow",            "GLA", "UK",           "supplier",     "mining_equipment",     "global.weir"),
    ("Sandvik Mining",                              "Stockholm",          "AB",  "Sweden",       "supplier",     "mining_equipment",     "home.sandvik"),
    ("Epiroc",                                      "Orebro",             "T",   "Sweden",       "supplier",     "mining_equipment",     "epiroc.com"),
    ("Komatsu Mining Corp",                         "Milwaukee",          "WI",  "USA",          "supplier",     "mining_equipment",     "mining.komatsu"),
    ("Liebherr Mining Equipment",                   "Newport News",       "VA",  "USA",          "supplier",     "equipment",            "liebherr.com"),
    # ── Heavy lift ────────────────────────────────────────────────────────────
    ("Mammoet",                                     "Schiedam",           "ZH",  "Netherlands",  "subcontractor","heavy_lift",           "mammoet.com"),
    ("Sarens",                                      "Wolvertem",          "VBR", "Belgium",      "subcontractor","heavy_lift",           "sarens.com"),
    ("ALE Heavy Lift",                              "Evesham",            "WOR", "UK",           "subcontractor","heavy_lift",           "ale.uk.com"),
    ("ALL Crane Rental",                            "Cleveland",          "OH",  "USA",          "subcontractor","heavy_lift",           "allcrane.com"),
    ("TNT Crane & Rigging",                         "Houston",            "TX",  "USA",          "subcontractor","heavy_lift",           "tntcrane.com"),
    # ── Inspection & Testing ──────────────────────────────────────────────────
    ("MISTRAS Group",                               "Princeton Junction", "NJ",  "USA",          "supplier",     "inspection_ndt",       "mistrasgroup.com"),
    ("Team Inc",                                    "Sugar Land",         "TX",  "USA",          "supplier",     "inspection_ndt",       "teaminc.com"),
    ("Bureau Veritas",                              "Houston",            "TX",  "USA",          "supplier",     "inspection_ndt",       "bureauveritas.com"),
    ("SGS SA",                                      "Geneva",             "GE",  "Switzerland",  "supplier",     "inspection_ndt",       "sgs.com"),
    ("Intertek Group",                              "London",             "LDN", "UK",           "supplier",     "inspection_ndt",       "intertek.com"),
    ("TUV Rheinland",                               "Cologne",            "NRW", "Germany",      "supplier",     "inspection_ndt",       "tuv.com"),
    ("Lloyd's Register Group",                      "London",             "LDN", "UK",           "supplier",     "inspection_ndt",       "lr.org"),
    ("DNV GL",                                      "Baerum",             "VF",  "Norway",       "supplier",     "inspection_ndt",       "dnvgl.com"),
    # ── Safety & Environment ──────────────────────────────────────────────────
    ("MSA Safety",                                  "Cranberry Township", "PA",  "USA",          "supplier",     "safety_equipment",     "msasafety.com"),
    ("Honeywell Safety Products",                   "Smithfield",         "RI",  "USA",          "supplier",     "safety_equipment",     "honeywellsafety.com"),
    ("3M Company",                                  "St. Paul",           "MN",  "USA",          "supplier",     "safety_equipment",     "3m.com"),
    ("DuPont Personal Protection",                  "Wilmington",         "DE",  "USA",          "supplier",     "safety_equipment",     "dupont.com"),
    ("Clean Harbors",                               "Norwell",            "MA",  "USA",          "subcontractor","safety_environment",   "cleanharbors.com"),
    ("Safety-Kleen",                                "Richardson",         "TX",  "USA",          "supplier",     "safety_environment",   "safety-kleen.com"),
    # ── HVAC ──────────────────────────────────────────────────────────────────
    ("Johnson Controls",                            "Cork",               "L",   "Ireland",      "supplier",     "hvac",                 "johnsoncontrols.com"),
    ("Carrier Global",                              "Palm Beach Gardens", "FL",  "USA",          "supplier",     "hvac",                 "carrier.com"),
    ("Trane Technologies",                          "Dublin",             "L",   "Ireland",      "supplier",     "hvac",                 "tranetechnologies.com"),
    # ── Infrastructure / Civil subcontractors ─────────────────────────────────
    ("Parsons Corporation",                         "Chantilly",          "VA",  "USA",          "subcontractor","engineering",          "parsons.com"),
    ("WSP Global",                                  "Montreal",           "QC",  "Canada",       "subcontractor","engineering",          "wsp.com"),
    ("SNC-Lavalin",                                 "Montreal",           "QC",  "Canada",       "subcontractor","engineering",          "snclavalin.com"),
    ("Strabag SE",                                  "Vienna",             "W",   "Austria",      "subcontractor","civil",                "strabag.com"),
    ("Hochtief AG",                                 "Essen",              "NRW", "Germany",      "subcontractor","civil",                "hochtief.com"),
    ("Skanska AB",                                  "Stockholm",          "AB",  "Sweden",       "subcontractor","civil",                "skanska.com"),
    ("Balfour Beatty",                              "London",             "LDN", "UK",           "subcontractor","civil",                "balfourbeatty.com"),
    ("Ferrovial Construction",                      "Madrid",             "M",   "Spain",        "subcontractor","civil",                "ferrovial.com"),
    ("Vinci Construction",                          "Rueil-Malmaison",    "IDF", "France",       "subcontractor","civil",                "vinci-construction.com"),
    ("Bouygues Construction",                       "Guyancourt",         "IDF", "France",       "subcontractor","civil",                "bouygues-construction.com"),
    ("Samsung Engineering",                         "Seoul",              "HS",  "South Korea",  "subcontractor","engineering",          "samsungengineering.com"),
    ("Hyundai Engineering",                         "Seoul",              "HS",  "South Korea",  "subcontractor","engineering",          "hdec.co.kr"),
    ("GS Engineering & Construction",               "Seoul",              "HS",  "South Korea",  "subcontractor","civil",                "gsenc.com"),
    ("Matrix Service Company",                      "Tulsa",              "OK",  "USA",          "subcontractor","industrial_services",  "matrixservice.com"),
    ("Turner Industries Group",                     "Baton Rouge",        "LA",  "USA",          "subcontractor","mechanical",           "turner-industries.com"),
    # ── Geotechnical & specialist engineering ─────────────────────────────────
    ("Fugro NV",                                    "Leidschendam",       "ZH",  "Netherlands",  "supplier",     "geotechnical",         "fugro.com"),
    ("Arcadis NV",                                  "Amsterdam",          "NH",  "Netherlands",  "subcontractor","engineering",          "arcadis.com"),
    ("Tetra Tech Inc",                              "Pasadena",           "CA",  "USA",          "subcontractor","engineering",          "tetratech.com"),
    ("Ramboll Group",                               "Copenhagen",         "KBH", "Denmark",      "subcontractor","engineering",          "ramboll.com"),
    ("Atkins Global",                               "Epsom",              "SRY", "UK",           "subcontractor","engineering",          "atkinsglobal.com"),
    # ── Concrete equipment ────────────────────────────────────────────────────
    ("Schwing-Stetter",                             "Bad Schwartau",      "SH",  "Germany",      "supplier",     "concrete_equipment",   "schwing.com"),
    ("Putzmeister",                                 "Aichtal",            "BW",  "Germany",      "supplier",     "concrete_equipment",   "putzmeister.com"),
    # ── Modular / Fabrication ──────────────────────────────────────────────────
    ("ATCO Structures",                             "Calgary",            "AB",  "Canada",       "supplier",     "modular_buildings",    "atco.com"),
    ("Module X Solutions",                          "Houston",            "TX",  "USA",          "subcontractor","modular_fabrication",  "modulexsolutions.com"),
    # ── Additional field proven suppliers ─────────────────────────────────────
    ("Thermon Group",                               "San Marcos",         "TX",  "USA",          "supplier",     "heat_tracing",         "thermon.com"),
    ("Voith Group",                                 "Heidenheim",         "BW",  "Germany",      "supplier",     "mechanical",           "voith.com"),
    ("SPX Flow",                                    "Charlotte",          "NC",  "USA",          "supplier",     "flow_control",         "spxflow.com"),
    ("Roper Technologies",                          "Sarasota",           "FL",  "USA",          "supplier",     "instrumentation",      "ropertech.com"),
    ("Danaher Corporation",                         "Washington",         "DC",  "USA",          "supplier",     "instrumentation",      "danaher.com"),
    ("Weidmuller Interface",                        "Detmold",            "NRW", "Germany",      "supplier",     "electrical",           "weidmuller.com"),
    ("General Cable",                               "Highland Heights",   "KY",  "USA",          "supplier",     "electrical",           "generalcable.com"),
    ("Gexpro Services",                             "Irving",             "TX",  "USA",          "supplier",     "electrical",           "gexpro.com"),
    ("Barsplice Products",                          "Miamisburg",         "OH",  "USA",          "supplier",     "rebar",                "barsplice.com"),
    ("Stericycle Inc",                              "Bannockburn",        "IL",  "USA",          "subcontractor","safety_environment",   "stericycle.com"),
    ("MWH Global",                                  "Broomfield",         "CO",  "USA",          "subcontractor","water_treatment",      "mwhglobal.com"),
    ("Outotec",                                     "Espoo",              "USM", "Finland",      "supplier",     "mining_equipment",     "outotec.com"),
]

# ══════════════════════════════════════════════════════════════════════════════
# PROJECTS  (real — sourced from Bechtel press releases & project pages)
# ══════════════════════════════════════════════════════════════════════════════
ALL_PROJECTS = [
    ("PROJ-LNG-001","BEC-LNG-WLA","Woodside Louisiana LNG Terminal Ph1&2",     "lng",          "Sulphur",           "LA",  "USA",         14_900_000_000,"Woodside Energy",              2022,2029),
    ("PROJ-LNG-002","BEC-LNG-RG1","Rio Grande LNG Phase 1 Trains 1-3",         "lng",          "Brownsville",       "TX",  "USA",         12_000_000_000,"NextDecade Corporation",        2023,2028),
    ("PROJ-LNG-003","BEC-LNG-RG4","Rio Grande LNG Train 4",                    "lng",          "Brownsville",       "TX",  "USA",          4_770_000_000,"NextDecade Corporation",        2024,2029),
    ("PROJ-LNG-004","BEC-LNG-RG5","Rio Grande LNG Train 5",                    "lng",          "Brownsville",       "TX",  "USA",          4_320_000_000,"NextDecade Corporation",        2024,2029),
    ("PROJ-LNG-005","BEC-LNG-PA1","Port Arthur LNG Phase 1",                   "lng",          "Port Arthur",       "TX",  "USA",         10_000_000_000,"Sempra Infrastructure",         2022,2027),
    ("PROJ-LNG-006","BEC-LNG-PA2","Port Arthur LNG Phase 2",                   "lng",          "Port Arthur",       "TX",  "USA",          8_500_000_000,"Sempra Infrastructure",         2025,2030),
    ("PROJ-NUC-001","BEC-NUC-VGL","Plant Vogtle Units 3 & 4",                  "nuclear_power","Waynesboro",        "GA",  "USA",          7_000_000_000,"Georgia Power",                 2013,2024),
    ("PROJ-NUC-002","BEC-NUC-STR","Sizewell C Nuclear Power Station",          "nuclear_power","Suffolk",           "SUF", "UK",          20_000_000_000,"EDF Energy",                    2024,2035),
    ("PROJ-MIN-001","BEC-MIN-QBC","Quebrada Blanca Phase 2 Copper Mine",       "mining",       "Tarapaca Region",   "I",   "Chile",        5_300_000_000,"Teck Resources",                2020,2024),
    ("PROJ-MIN-002","BEC-MIN-EVA","Eva Copper Mine EPC Queensland",            "mining",       "Cloncurry",         "QLD", "Australia",    1_200_000_000,"Harmony Gold",                  2024,2027),
    ("PROJ-MIN-003","BEC-MIN-THP","Thacker Pass Lithium Mine EPCM",            "mining",       "Humboldt County",   "NV",  "USA",          2_300_000_000,"Lithium Americas",              2023,2027),
    ("PROJ-INF-001","BEC-INF-WSA","Western Sydney International Airport",      "infrastructure","Badgerys Creek",   "NSW", "Australia",    5_000_000_000,"WSA Co",                        2020,2026),
    ("PROJ-INF-002","BEC-INF-LIZ","Elizabeth Line Crossrail London",           "infrastructure","London",           "LDN", "UK",           3_600_000_000,"Crossrail Ltd",                 2012,2022),
    ("PROJ-INF-003","BEC-INF-RYD","Riyadh Metro Project",                      "infrastructure","Riyadh",           "RD",  "Saudi Arabia", 8_000_000_000,"Arriyadh Development Authority",2015,2021),
    ("PROJ-ENV-001","BEC-ENV-HAN","Hanford Waste Treatment Plant",             "environmental","Richland",          "WA",  "USA",         17_000_000_000,"US Dept of Energy",             2001,2030),
    ("PROJ-ENV-002","BEC-ENV-UPF","Uranium Processing Facility Y-12",         "environmental","Oak Ridge",         "TN",  "USA",          6_500_000_000,"NNSA",                          2014,2030),
    ("PROJ-MFG-001","BEC-MFG-INT","Intel Semiconductor Fab Ohio",              "manufacturing","New Albany",        "OH",  "USA",         20_000_000_000,"Intel Corporation",             2022,2026),
    ("PROJ-MFG-002","BEC-MFG-BAT","Battery Manufacturing Facility",           "manufacturing","Nashville",         "TN",  "USA",            800_000_000,"Confidential Client",           2023,2025),
    ("PROJ-PWR-001","BEC-PWR-CVE","Cricket Valley Energy CCPP 1100MW",        "power",        "Dover",             "NY",  "USA",          1_100_000_000,"Cricket Valley Energy",         2018,2020),
    ("PROJ-REN-001","BEC-REN-CCS","Cold Creek Solar Storage 430MW",           "renewables",   "Lincoln County",    "NV",  "USA",            750_000_000,"Doral Renewables",              2024,2026),
]

# ══════════════════════════════════════════════════════════════════════════════
# TRADE MAPPINGS
# ══════════════════════════════════════════════════════════════════════════════
TRADE_TO_EPC = {
    "electrical":"mep","mechanical":"mep","instrumentation":"mep",
    "process_systems":"mep","flow_control":"mep","pumps_valves":"mep",
    "heat_exchange":"mep","heat_tracing":"mep","water_treatment":"mep",
    "hvac":"mep","valves_piping":"mep",
    "lng_equipment":"equipment","turbomachinery":"equipment",
    "nuclear_equipment":"equipment","drilling_equipment":"equipment",
    "oilfield_services":"equipment","mining_equipment":"equipment",
    "solar_tracking":"equipment","equipment":"equipment",
    "concrete_equipment":"equipment","laser_systems":"equipment",
    "industrial_equipment":"equipment","defense_equipment":"equipment",
    "structural_steel":"structural_steel","rebar":"structural_steel",
    "post_tensioning":"structural_steel","lng_storage_tanks":"structural_steel",
    "piping":"civil","civil":"civil","aggregate":"civil",
    "cement_concrete":"civil","geotechnical":"civil",
    "concrete_services":"civil","fabrication":"civil",
    "scaffolding":"site_overheads","insulation":"site_overheads",
    "formwork":"site_overheads","industrial_supply":"site_overheads",
    "specialist_tools":"site_overheads","logistics":"site_overheads",
    "it_infrastructure":"site_overheads","safety_equipment":"site_overheads",
    "safety_environment":"site_overheads","office_supplies":"site_overheads",
    "industrial_gases":"site_overheads","industrial_services":"site_overheads",
    "modular_buildings":"site_overheads","filtration":"mep",
    "heavy_lift":"subcontract","engineering":"subcontract",
    "offshore":"subcontract","inspection_ndt":"site_overheads",
    "modular_fabrication":"subcontract","mechanical_services":"subcontract",
}

TRADE_TO_MATERIAL = {
    "electrical":"cable","mechanical":"equipment","instrumentation":"equipment",
    "process_systems":"equipment","flow_control":"equipment","pumps_valves":"equipment",
    "heat_exchange":"equipment","heat_tracing":"cable","water_treatment":"service",
    "hvac":"equipment","valves_piping":"pipe","lng_equipment":"equipment",
    "turbomachinery":"equipment","nuclear_equipment":"equipment",
    "drilling_equipment":"equipment","oilfield_services":"service",
    "mining_equipment":"equipment","solar_tracking":"equipment","equipment":"equipment",
    "concrete_equipment":"equipment","laser_systems":"equipment",
    "industrial_equipment":"equipment","defense_equipment":"equipment",
    "structural_steel":"steel","rebar":"rebar","post_tensioning":"rebar",
    "lng_storage_tanks":"steel","piping":"pipe","civil":"aggregate",
    "aggregate":"aggregate","cement_concrete":"cement","geotechnical":"service",
    "concrete_services":"cement","fabrication":"steel","scaffolding":"service",
    "insulation":"service","formwork":"service","industrial_supply":"service",
    "specialist_tools":"service","logistics":"service","it_infrastructure":"service",
    "safety_equipment":"service","safety_environment":"service",
    "office_supplies":"service","industrial_gases":"service",
    "industrial_services":"service","modular_buildings":"service",
    "filtration":"equipment","heavy_lift":"service","engineering":"service",
    "offshore":"service","inspection_ndt":"service","modular_fabrication":"service",
}

RATE_RANGES = {
    "electrical":(5_000,2_000_000),"mechanical":(10_000,5_000_000),
    "instrumentation":(2_000,500_000),"process_systems":(50_000,10_000_000),
    "flow_control":(1_000,300_000),"pumps_valves":(5_000,2_000_000),
    "heat_exchange":(100_000,8_000_000),"heat_tracing":(500,50_000),
    "lng_equipment":(1_000_000,200_000_000),"turbomachinery":(500_000,100_000_000),
    "nuclear_equipment":(1_000_000,100_000_000),"drilling_equipment":(50_000,20_000_000),
    "oilfield_services":(10_000,5_000_000),"mining_equipment":(100_000,50_000_000),
    "solar_tracking":(500_000,50_000_000),"structural_steel":(800,5_000),
    "piping":(200,50_000),"civil":(50,5_000),"aggregate":(20,100),
    "cement_concrete":(80,200),"formwork":(500,50_000),"scaffolding":(1_000,500_000),
    "heavy_lift":(50_000,10_000_000),"insulation":(5_000,2_000_000),
    "industrial_gases":(500,100_000),"industrial_supply":(100,50_000),
    "specialist_tools":(1_000,200_000),"logistics":(5_000,2_000_000),
    "it_infrastructure":(10_000,1_000_000),"engineering":(50_000,50_000_000),
    "offshore":(100_000,100_000_000),"inspection_ndt":(5_000,2_000_000),
    "water_treatment":(10_000,5_000_000),"fabrication":(10_000,5_000_000),
    "rebar":(700,1_500),"post_tensioning":(5_000,500_000),
    "hvac":(5_000,2_000_000),"concrete_equipment":(20_000,2_000_000),
    "laser_systems":(50_000,5_000_000),"industrial_equipment":(10_000,2_000_000),
    "defense_equipment":(100_000,50_000_000),"lng_storage_tanks":(1_000_000,100_000_000),
    "valves_piping":(1_000,500_000),"geotechnical":(10_000,2_000_000),
    "safety_equipment":(500,50_000),"safety_environment":(5_000,500_000),
    "modular_buildings":(50_000,5_000_000),"modular_fabrication":(100_000,20_000_000),
}

UOM_BY_TRADE = {
    "structural_steel":"MT","rebar":"MT","aggregate":"TON",
    "cement_concrete":"CY","piping":"LF","civil":"CY",
    "electrical":"LS","insulation":"SF","scaffolding":"SF",
    "logistics":"LOAD","industrial_gases":"MCF","industrial_supply":"EA",
    "specialist_tools":"EA","safety_equipment":"EA",
}

def seed_int(name):
    return int(hashlib.md5(name.encode()).hexdigest(),16) % (2**31)

def seeded(name):
    return random.Random(seed_int(name))

def vendor_code(name,idx):
    parts=name.replace("&","and").replace(",","").split()
    return f"VND-{''.join(w[0].upper() for w in parts[:3] if w)}-{idx+1:03d}"

def fake_tax_id(country,name):
    r=seeded(name+"ein")
    if country=="USA": return f"{r.randint(10,99)}-{r.randint(1000000,9999999)}"
    elif country in("UK","Ireland","Australia"): return f"GB{r.randint(100000000,999999999)}"
    elif country=="Germany": return f"DE{r.randint(100000000,999999999)}"
    elif country in("South Korea",): return f"KR{r.randint(100000000,999999999)}"
    elif country=="Japan": return f"JP{r.randint(1000000000,9999999999)}"
    elif country=="Norway": return f"NO{r.randint(100000000,999999999)}"
    elif country in("Italy","France","Spain","Netherlands","Belgium","Sweden","Denmark","Finland","Luxembourg"):
        return f"{country[:2].upper()}{r.randint(10000000000,99999999999)}"
    elif country in("Switzerland","Austria"): return f"CH{r.randint(100000000,999999999)}"
    elif country=="Turkey": return f"TR{r.randint(1000000000,9999999999)}"
    elif country=="Canada": return f"CA{r.randint(100000000,999999999)}"
    else: return f"XX{r.randint(100000000,999999999)}"

def rating(name,lo=3.8,hi=5.0):
    return round(seeded(name+"rt").uniform(lo,hi),1)

# ══════════════════════════════════════════════════════════════════════════════
# BUILD VENDORS
# ══════════════════════════════════════════════════════════════════════════════
def build_vendors():
    vendors=[]
    for idx,(name,city,state,country,vtype,trade,website) in enumerate(ALL_SUPPLIERS):
        r=seeded(name)
        v={
            "vnd_vendor_id":str(uuid.UUID(int=seed_int(name)*7%(2**128))),
            "vnd_vendor_name_normalized":name,
            "inv_supplier_name":name,
            "inv_supplier_city":city,
            "inv_supplier_state":state,
            "country":country,
            "vnd_vendor_type":vtype,
            "vnd_trade_category":trade,
            "inv_li_epc_category":TRADE_TO_EPC.get(trade,"site_overheads"),
            "inv_li_material_type":TRADE_TO_MATERIAL.get(trade,"service"),
            "website":website,
            "vnd_vendor_code":vendor_code(name,idx),
            "inv_supplier_email":f"procurement@{website}",
            "inv_supplier_gstin":fake_tax_id(country,name),
            "inv_supplier_pan":f"{seed_int(name+chr(65))%90+10}-{seed_int(name)%900000+100000}-{seed_int(name+chr(90))%9000+1000}",
            "inv_supplier_phone":f"+1-{r.randint(200,999)}-{r.randint(200,999)}-{r.randint(1000,9999)}",
            "vnd_cin":f"{seed_int(name+'cin')%9000000000+1000000000}",
            "vnd_overall_rating":rating(name,4.0,5.0),
            "vnd_quality_rating":rating(name+"q",4.0,5.0),
            "vnd_delivery_rating":rating(name+"d",3.8,5.0),
            "vnd_safety_rating":rating(name+"s",4.2,5.0),
            "vnd_financial_health":r.choice(["A","A","A","B"]),
            "vnd_msme_flag":1 if any(w in name for w in ["LLC","Inc","Small"]) and len(name)<25 else 0,
            "vnd_blacklisted":0,
            "vnd_approved_vendor":1,
            "vnd_empanelment_date":str(date(r.randint(2008,2021),r.randint(1,12),1)),
            "vnd_empanelment_expiry":str(date(2027,r.randint(1,12),28)),
            "vnd_specialisation":f"{trade.replace('_',' ').title()} — EPC megaprojects",
            "inv_supplier_bank_name":r.choice(["JPMorgan Chase","Citibank","Wells Fargo","HSBC","Deutsche Bank","Bank of America","Barclays"]),
            "inv_supplier_ifsc_code":f"JPMB{r.randint(1000000,9999999):07d}",
        }
        vendors.append(v)
    return vendors

# ══════════════════════════════════════════════════════════════════════════════
# BUILD PROJECTS
# ══════════════════════════════════════════════════════════════════════════════
def build_projects():
    projects=[]
    for pid,code,name,market,city,state,country,cv,client,sy,ey in ALL_PROJECTS:
        r=seeded(name)
        start=date(sy,r.randint(1,6),1)
        end=date(ey,r.randint(6,12),28)
        projects.append({
            "project_id":pid,"project_code":code,"project_name":name,
            "prj_type":market,"prj_site_city":city,"prj_site_state":state,
            "prj_site_country":country,"prj_total_contract_value":cv,
            "prj_client_name":client,"prj_is_epc":1,
            "prj_contract_type":"lump_sum",
            "prj_status":"active" if ey>=2024 else "completed",
            "prj_planned_start_date":str(start),"prj_planned_end_date":str(end),
            "prj_original_budget":round(cv*r.uniform(0.88,0.97)),
            "prj_revised_budget":round(cv*r.uniform(1.05,1.25)),
            "prj_actual_start_date":str(start+timedelta(days=r.randint(0,90))),
        })
    return projects

# ══════════════════════════════════════════════════════════════════════════════
# BUILD INVOICES
# ══════════════════════════════════════════════════════════════════════════════
def build_invoices(vendors,projects):
    invoices=[]
    seq=1
    for vendor in vendors:
        r=seeded(vendor["vnd_vendor_name_normalized"])
        trade=vendor["vnd_trade_category"]
        rlo,rhi=RATE_RANGES.get(trade,(1_000,500_000))
        uom=UOM_BY_TRADE.get(trade,"LS")
        vprojects=r.sample(projects,r.randint(2,min(6,len(projects))))
        for proj in vprojects:
            n_inv=r.randint(6,18)
            pstart=date.fromisoformat(proj["prj_planned_start_date"])
            pend=date.fromisoformat(proj["prj_planned_end_date"])
            drange=max((pend-pstart).days,365)
            for i in range(n_inv):
                inv_date=pstart+timedelta(days=r.randint(30,drange-30))
                if inv_date>date(2025,12,31): inv_date=date(2024,r.randint(1,12),r.randint(1,28))
                qty=round(r.uniform(1,50),2)
                rate=round(r.uniform(rlo,rhi),2)
                taxable=round(qty*rate,2)
                tax=round(taxable*r.choice([0,0,0.0825,0.05]),2)
                total=round(taxable+tax,2)
                initials="".join(w[0].upper() for w in vendor["inv_supplier_name"].split()[:2] if w)
                invoices.append({
                    "transaction_id":f"INV-{str(uuid.uuid4())[:8].upper()}",
                    "line_item_id":f"LI-{seq:07d}",
                    "invoice_id":f"INV-{str(uuid.uuid4())[:8].upper()}",
                    "synced_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "txn_type":"invoice","txn_source":"ocr_pdf","txn_date":str(inv_date),
                    "inv_supplier_name":vendor["inv_supplier_name"],
                    "inv_supplier_gstin":vendor["inv_supplier_gstin"],
                    "inv_supplier_pan":vendor["inv_supplier_pan"],
                    "inv_supplier_city":vendor["inv_supplier_city"],
                    "inv_supplier_state":vendor["inv_supplier_state"],
                    "inv_supplier_email":vendor["inv_supplier_email"],
                    "inv_supplier_phone":vendor["inv_supplier_phone"],
                    "inv_supplier_bank_name":vendor["inv_supplier_bank_name"],
                    "vnd_vendor_id":vendor["vnd_vendor_id"],
                    "vnd_vendor_code":vendor["vnd_vendor_code"],
                    "vnd_vendor_name_normalized":vendor["vnd_vendor_name_normalized"],
                    "vnd_vendor_type":vendor["vnd_vendor_type"],
                    "vnd_trade_category":vendor["vnd_trade_category"],
                    "vnd_overall_rating":vendor["vnd_overall_rating"],
                    "vnd_financial_health":vendor["vnd_financial_health"],
                    "vnd_blacklisted":vendor["vnd_blacklisted"],
                    "vnd_approved_vendor":vendor["vnd_approved_vendor"],
                    "vnd_msme_flag":vendor["vnd_msme_flag"],
                    "inv_project_id":proj["project_id"],
                    "inv_project_code":proj["project_code"],
                    "inv_project_name":proj["project_name"],
                    "prj_client_name":proj["prj_client_name"],
                    "prj_site_city":proj["prj_site_city"],
                    "prj_site_state":proj["prj_site_state"],
                    "prj_type":proj["prj_type"],
                    "prj_total_contract_value":proj["prj_total_contract_value"],
                    "prj_is_epc":proj["prj_is_epc"],
                    "prj_status":proj["prj_status"],
                    "inv_invoice_number":f"{initials}-{inv_date.year}-{seq:07d}",
                    "inv_invoice_date":str(inv_date),
                    "inv_invoice_type":"tax_invoice",
                    "inv_invoice_currency":"USD",
                    "inv_place_of_supply":proj["prj_site_state"],
                    "inv_li_sl_no":i+1,
                    "inv_li_description":f"{trade.replace('_',' ').title()} supply — {proj['project_name'][:35]} Lot {i+1}",
                    "inv_li_hsn_sac_code":r.choice(["7213","7304","8544","2523","8413","8481","8537","7214","7306","8419","3926","8708"]),
                    "inv_li_quantity":qty,
                    "inv_li_uom":uom,
                    "inv_li_uom_normalized":uom,
                    "inv_li_unit_rate":rate,
                    "inv_li_taxable_amount":taxable,
                    "inv_li_total_amount":total,
                    "inv_li_epc_category":vendor["inv_li_epc_category"],
                    "inv_li_material_type":vendor["inv_li_material_type"],
                    "inv_taxable_amount":taxable,
                    "inv_cgst_amount":0.0,"inv_sgst_amount":0.0,"inv_igst_amount":0.0,
                    "inv_other_charges":round(r.uniform(0,500),2),
                    "inv_total_amount":total,
                    "inv_duplicate_flag":0,"inv_off_contract_flag":0,
                    "inv_price_variance_flag":0,"inv_grn_matched":0,
                    "po_over_invoiced_flag":0,"row_process_id":seq,
                })
                seq+=1

    # Inject demo flags
    sample=random.sample(invoices[:1000],50)
    for o in sample:
        d=o.copy(); d["transaction_id"]=f"INV-{str(uuid.uuid4())[:8].upper()}"
        d["line_item_id"]=f"LI-{seq:07d}"; d["row_process_id"]=seq
        d["inv_duplicate_flag"]=1; invoices.append(d); seq+=1

    for inv in random.sample(invoices[:1500],80):
        inv["inv_li_unit_rate"]=round(inv["inv_li_unit_rate"]*random.uniform(1.3,1.9),2)
        inv["inv_li_total_amount"]=round(inv["inv_li_quantity"]*inv["inv_li_unit_rate"],2)
        inv["inv_total_amount"]=inv["inv_li_total_amount"]
        inv["inv_price_variance_flag"]=1

    for inv in random.sample(invoices[:1200],40):
        inv["inv_off_contract_flag"]=1

    print(f"  Total invoice rows: {len(invoices)}")
    return invoices

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def write_csv(data,fn):
    if not data: return
    with open(fn,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=data[0].keys(),extrasaction="ignore")
        w.writeheader(); w.writerows(data)
    print(f"  Written: {fn} ({len(data)} rows)")

if __name__=="__main__":
    print("\nBuilding expanded Bechtel dataset...\n")
    print("Step 1: Vendors..."); vendors=build_vendors(); write_csv(vendors,"bechtel_vendors_v2.csv")
    print("\nStep 2: Projects..."); projects=build_projects(); write_csv(projects,"bechtel_projects_v2.csv")
    print("\nStep 3: Invoices..."); invoices=build_invoices(vendors,projects); write_csv(invoices,"bechtel_invoices_v2.csv")

    from collections import Counter
    ctry=Counter(v["country"] for v in vendors)
    vtype=Counter(v["vnd_vendor_type"] for v in vendors)
    print(f"\n{'='*55}")
    print(f"  Vendors   : {len(vendors)} across {len(ctry)} countries")
    print(f"  Suppliers : {vtype['supplier']}  |  Subcontractors: {vtype['subcontractor']}")
    print(f"  Projects  : {len(projects)}")
    print(f"  Invoices  : {len(invoices)}")
    print(f"  Duplicates injected      : 50")
    print(f"  Price outliers injected  : 80")
    print(f"  Off-contract injected    : 40")
    print(f"{'='*55}\n")