"""Marketing copy used across the public site.

Kept in a single module so non-technical editors only have one file to touch
and the templates stay presentational.
"""

# --- Iconography (inline SVG strings) -----------------------------------
# Use currentColor so Tailwind text-* classes paint them.
ICON_SHIELD   = '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 3l8 3v6c0 4.5-3.4 8.4-8 9-4.6-.6-8-4.5-8-9V6l8-3z" stroke-linejoin="round"/></svg>'
ICON_CLOUD    = '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M7 18a4 4 0 010-8 6 6 0 0111.5 1.5A4 4 0 0118 18H7z" stroke-linejoin="round"/></svg>'
ICON_RADAR    = '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 010 18M3 12h18"/></svg>'
ICON_SIREN    = '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 18h14M7 18v-5a5 5 0 0110 0v5M9 7V4M15 7V4"/></svg>'
ICON_LOCK_N   = '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="5" y="11" width="14" height="9" rx="1.5"/><path d="M8 11V8a4 4 0 018 0v3"/></svg>'
ICON_COMPASS  = '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="9"/><path d="M14.5 9.5l-1.5 4-4 1.5 1.5-4 4-1.5z" stroke-linejoin="round"/></svg>'
ICON_GRID     = '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="4" y="4" width="7" height="7"/><rect x="13" y="4" width="7" height="7"/><rect x="4" y="13" width="7" height="7"/><rect x="13" y="13" width="7" height="7"/></svg>'
ICON_PULSE    = '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 12h4l2-6 4 12 2-6h6"/></svg>'
ICON_CERT     = '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="10" r="5"/><path d="M9 14l-1 7 4-2 4 2-1-7"/></svg>'
ICON_NODES    = '<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><path d="M7 6l4 5M17 6l-4 5M7 18l4-5M17 18l-4-5"/></svg>'


TRUSTED_BY = [
    "Mubadala",
    "Emirates NBD",
    "Aramco Digital",
    "Qatar Energy",
    "STC Group",
    "Etihad Aviation",
]


SERVICE_TEASERS = [
    {
        "title": "Threat Detection & Response",
        "summary": "24/7 SOC operations enriched by behavioral analytics and threat intelligence tuned to regional adversary campaigns.",
        "icon": ICON_RADAR,
        "anchor": "threat-detection",
    },
    {
        "title": "Cloud Security",
        "summary": "CSPM, CWPP, and identity-first controls across AWS, Azure, and OCI — engineered for sovereign and regulated workloads.",
        "icon": ICON_CLOUD,
        "anchor": "cloud-security",
    },
    {
        "title": "Infrastructure Protection",
        "summary": "Hardened reference architectures for hybrid estates, OT/IT convergence, and critical national infrastructure.",
        "icon": ICON_SHIELD,
        "anchor": "infrastructure-protection",
    },
    {
        "title": "Incident Response",
        "summary": "Retainer-backed forensics, containment, and recovery. Hours to mobilize. Days to restore. Weeks to root-cause.",
        "icon": ICON_SIREN,
        "anchor": "incident-response",
    },
    {
        "title": "Zero Trust Architecture",
        "summary": "Identity, device, and workload trust scored continuously — enforced at every hop, audited end-to-end.",
        "icon": ICON_LOCK_N,
        "anchor": "zero-trust",
    },
    {
        "title": "Security Consulting",
        "summary": "Board-level posture reviews, regulator-aligned roadmaps, and M&A diligence delivered by named principals.",
        "icon": ICON_COMPASS,
        "anchor": "consulting",
    },
]


HOME_STATS = [
    {"value": "99.97",  "suffix": "%",  "label": "Critical alert triage SLA across enterprise SOC engagements"},
    {"value": "−72",    "suffix": "%",  "label": "Average reduction in mean time to detect after 90 days"},
    {"value": "140",    "suffix": "+",  "label": "Active engagements across banking, government, and energy"},
    {"value": "24/7",   "suffix": "",   "label": "Continuous monitoring from our regional security operations centers"},
]


HOME_FEATURES = [
    {
        "title": "Data sovereignty by design",
        "body":  "All telemetry, case data, and forensic artifacts remain in your regulatory jurisdiction — UAE, KSA, or Qatar — by default.",
        "icon":  ICON_GRID,
    },
    {
        "title": "Threat intelligence with regional context",
        "body":  "Our analysts maintain dedicated coverage of adversary groups targeting GCC financial services, energy, and government sectors.",
        "icon":  ICON_PULSE,
    },
    {
        "title": "Regulator-aligned reporting",
        "body":  "Evidence packages mapped to UAE IA, SAMA CSF, NCA ECC, and ISO 27001 — produced on schedule, accepted on first review.",
        "icon":  ICON_CERT,
    },
    {
        "title": "Integrated, not bolted-on",
        "body":  "Detection, response, identity, and governance share one telemetry plane — so every control reinforces the next.",
        "icon":  ICON_NODES,
    },
]


# ---------------------- About page content ---------------------------------

COMPANY_VALUES = [
    {
        "title": "Engineering over theater",
        "body":  "Security must work in production, not on a slide. We measure success by reduction in real risk, not volume of policies issued.",
    },
    {
        "title": "Discretion as a default",
        "body":  "Our clients are critical institutions. We operate quietly, document carefully, and never use engagements as marketing material without explicit consent.",
    },
    {
        "title": "Operator-led",
        "body":  "Every engagement is led by a named principal with operational scars, not a sales-engineered presentation deck.",
    },
    {
        "title": "Regional first, global fluent",
        "body":  "We understand the regulatory texture of the Gulf — and the global threat landscape that touches it.",
    },
]


EXPERTISE_PILLARS = [
    {
        "tag":   "01",
        "title": "Adversary simulation",
        "body":  "Red team, purple team, and continuous adversary emulation grounded in MITRE ATT&CK, mapped to the campaigns most likely to target your sector.",
    },
    {
        "tag":   "02",
        "title": "Cloud-native security",
        "body":  "Reference architectures for AWS, Azure, and OCI — including landing zones, identity federation, and detection pipelines that scale to billions of events.",
    },
    {
        "tag":   "03",
        "title": "OT / IT convergence",
        "body":  "Defense for operational environments where downtime is unacceptable: utilities, refineries, ports, transportation, and manufacturing.",
    },
    {
        "tag":   "04",
        "title": "Governance & assurance",
        "body":  "Programs that survive audit — SAMA, NCA, CBUAE, ISO 27001, SOC 2, PCI-DSS — without compromising operational tempo.",
    },
]


LEADERSHIP = [
    {
        "name":  "Hala Al-Faraj",
        "role":  "Chief Executive Officer",
        "bio":   "Two decades across sovereign cyber programs and Big-Four advisory. Founded Sectrix to bring engineering rigor to enterprise defense in the GCC.",
        "initials": "HF",
    },
    {
        "name":  "Yousef Mahmoud",
        "role":  "Chief Technology Officer",
        "bio":   "Former principal engineer on regional SOC platforms. Holds patents in detection pipeline scaling and analyst workflow automation.",
        "initials": "YM",
    },
    {
        "name":  "Dr. Sara Bennani",
        "role":  "Head of Threat Intelligence",
        "bio":   "Tracked APT activity across the Gulf for a decade. Published author on adversary tradecraft against critical infrastructure.",
        "initials": "SB",
    },
    {
        "name":  "Omar Rahimi",
        "role":  "Head of Incident Response",
        "bio":   "Led containment on twelve nation-state intrusions across banking and energy. Specializes in destructive-malware recovery.",
        "initials": "OR",
    },
]


TIMELINE = [
    {"year": "2019", "title": "Founded in Dubai", "body": "Sectrix is established with a charter to engineer defense for Gulf enterprises."},
    {"year": "2020", "title": "First Tier-1 bank engagement", "body": "Designed and deployed continuous detection across a regional bank's hybrid estate."},
    {"year": "2021", "title": "Regional SOC operational", "body": "24/7 security operations center commissioned with multi-country analyst coverage."},
    {"year": "2022", "title": "Sovereign-cloud reference architecture", "body": "Published reference designs for regulated workloads on sovereign cloud platforms."},
    {"year": "2023", "title": "Riyadh & Doha offices", "body": "Expanded operations across KSA and Qatar with local incident-response capability."},
    {"year": "2024", "title": "140+ active engagements", "body": "Sectrix now defends institutions across banking, government, energy, and telecom."},
    {"year": "2026", "title": "Threat intelligence practice", "body": "Dedicated regional threat intelligence team formalized as a standalone practice area."},
]


CULTURE_PILLARS = [
    {"tag": "01", "title": "Operator-led", "body": "Engineers and analysts run the work — and the hiring. Sales is downstream of trust."},
    {"tag": "02", "title": "Discretion as default", "body": "Our clients are critical institutions. We protect their confidentiality before our own visibility."},
    {"tag": "03", "title": "Compounded mastery", "body": "Deep specialization is rewarded. We pay for craft and protect time to maintain it."},
    {"tag": "04", "title": "GCC at heart", "body": "Built in Dubai, operating across the Gulf. We&rsquo;re here because the work is here."},
]


# ---------------------- Services (long-form) -------------------------------

SERVICE_DETAIL = [
    {
        "anchor": "threat-detection",
        "tag":    "01",
        "title":  "Threat Detection & Response",
        "icon":   ICON_RADAR,
        "intro":  "24/7 security operations enriched by behavioral analytics and a threat intelligence layer tuned to adversary campaigns targeting the GCC.",
        "capabilities": [
            "Tier 1 – 3 SOC operations from regional facilities",
            "Detection engineering aligned to MITRE ATT&CK",
            "Behavioral analytics across identity, endpoint, and network",
            "Threat hunting on a continuous, hypothesis-driven cadence",
            "Use-case lifecycle management with measurable coverage scoring",
        ],
        "outcome": "Median dwell time under 18 minutes for high-confidence alerts.",
    },
    {
        "anchor": "cloud-security",
        "tag":    "02",
        "title":  "Cloud Security",
        "icon":   ICON_CLOUD,
        "intro":  "Cloud-native security for workloads on AWS, Azure, and OCI — including sovereign-cloud deployments where data residency and regulator alignment are non-negotiable.",
        "capabilities": [
            "Landing zone and account-factory hardening",
            "Cloud security posture management (CSPM) at scale",
            "Workload protection (CWPP) and container runtime defense",
            "Identity federation, just-in-time access, secrets management",
            "Detection pipelines designed for cloud-native telemetry",
        ],
        "outcome": "Cloud estates audit-ready against SAMA, NCA, and CBUAE cloud controls.",
    },
    {
        "anchor": "infrastructure-protection",
        "tag":    "03",
        "title":  "Infrastructure Protection",
        "icon":   ICON_SHIELD,
        "intro":  "Hardened reference architectures for hybrid enterprise estates, OT/IT convergence, and critical national infrastructure where downtime is unacceptable.",
        "capabilities": [
            "Network segmentation and microsegmentation strategy",
            "Privileged access management for hybrid environments",
            "OT visibility, anomaly detection, and protocol-aware monitoring",
            "Secure remote access for industrial control systems",
            "Edge and branch protection across distributed estates",
        ],
        "outcome": "Resilient architectures that contain blast radius and pass independent attestation.",
    },
    {
        "anchor": "incident-response",
        "tag":    "04",
        "title":  "Incident Response",
        "icon":   ICON_SIREN,
        "intro":  "Retainer-backed digital forensics, containment, and recovery. Mobilized in hours, restored in days, root-caused in weeks.",
        "capabilities": [
            "1-hour mobilization SLA on retainer",
            "Endpoint and cloud forensics with chain-of-custody discipline",
            "Containment and eradication aligned to NIST SP 800-61",
            "Destructive-malware recovery and backup integrity validation",
            "Regulator-grade post-incident reporting and lessons learned",
        ],
        "outcome": "Recovery measured in days, not weeks. Reports accepted on first review.",
    },
    {
        "anchor": "zero-trust",
        "tag":    "05",
        "title":  "Zero Trust Architecture",
        "icon":   ICON_LOCK_N,
        "intro":  "Identity-, device-, and workload-trust scored continuously and enforced at every hop — built on standards, audited end-to-end.",
        "capabilities": [
            "Identity-first zero trust reference architecture",
            "Continuous device posture and conditional access",
            "Workload identity, service mesh, and east-west enforcement",
            "Policy-as-code with full audit traceability",
            "Phased migration plans that retire legacy perimeters safely",
        ],
        "outcome": "Implicit-trust pathways eliminated; access becomes explicit, scored, and revocable.",
    },
    {
        "anchor": "consulting",
        "tag":    "06",
        "title":  "Security Consulting",
        "icon":   ICON_COMPASS,
        "intro":  "Board-level posture reviews, regulator-aligned strategy, and M&A diligence — delivered by named principals with operational scars.",
        "capabilities": [
            "Cyber maturity assessments benchmarked against sector peers",
            "Regulator-aligned roadmaps (SAMA, NCA, CBUAE, ISO 27001, SOC 2)",
            "vCISO advisory for periods of leadership transition",
            "M&A cyber due diligence and post-merger integration",
            "Board-level reporting that translates risk into business language",
        ],
        "outcome": "A defensible, measurable security program — explainable to the board and the regulator.",
    },
]
