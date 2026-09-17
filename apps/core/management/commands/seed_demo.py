"""Populate the database with realistic demo content.

Run:  python manage.py seed_demo

Re-runnable and non-destructive: rows are created only when their slug is
absent. Site content is editable from the admin and this command runs on every
container start, so it must never overwrite what an editor has changed.
"""
from datetime import date

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.case_studies.models import CaseStudy
from apps.careers.models import JobOpening
from apps.services.models import Service

from apps.core.content import SERVICE_DETAIL, SERVICE_TEASERS
from apps.core.icons import ICONS


CASE_STUDIES = [
    {
        "title": "Reducing dwell time by 72% at a Tier-1 GCC bank",
        "client_name": "Confidential — Tier-1 GCC Bank",
        "sector": "banking",
        "region": "UAE",
        "summary": "Re-engineered the detection pipeline and SOC playbooks across the bank's hybrid estate, taking mean time to detect from 64 minutes to under 18.",
        "challenge": "The bank's existing SIEM produced over 2,400 alerts per analyst per day with no scoring model. Critical signals were buried; analyst burnout was rising; the regulator had flagged inconsistent triage discipline.",
        "approach": "Rebuilt the detection use-case library against MITRE ATT&CK, introduced a confidence-and-business-impact scoring model, and migrated tier-1 triage to a single console. Embedded two Sectrex principals into the SOC for the first 60 days.",
        "outcome": "Alert volume per analyst fell by 81%. Mean time to detect dropped from 64 minutes to 17 on high-confidence alerts. The regulator's follow-up examination closed with zero findings against detection capability.",
        "headline_metric": "−72%",
        "headline_metric_label": "Mean time to detect",
        "tags": ["SOC", "SAMA", "MITRE ATT&CK"],
        "published_at": date(2025, 9, 1),
        "display_order": 10,
    },
    {
        "title": "Sovereign-cloud landing zone for a national agency",
        "client_name": "Sovereign Agency · GCC",
        "sector": "government",
        "region": "KSA",
        "summary": "Designed and operationalized a sovereign-cloud landing zone meeting NCA ECC controls — onboarding 14 mission systems in nine months.",
        "challenge": "The agency needed to migrate regulated workloads to a sovereign cloud platform while satisfying NCA ECC controls and maintaining segregated environments for classification tiers.",
        "approach": "Co-designed a multi-account landing zone with policy-as-code, federated identity, segregated detection pipelines per classification tier, and a regulator-aligned evidence model. Trained the agency's own engineers to operate it.",
        "outcome": "14 mission systems onboarded in nine months. Zero ECC findings on independent attestation. The reference architecture has since been adopted as the agency's internal standard.",
        "headline_metric": "14",
        "headline_metric_label": "Mission systems onboarded",
        "tags": ["Cloud", "NCA ECC", "Sovereign"],
        "published_at": date(2025, 6, 15),
        "display_order": 20,
    },
    {
        "title": "Containing a destructive-malware incident at a regional energy operator",
        "client_name": "Confidential — Regional Energy Operator",
        "sector": "energy",
        "region": "GCC",
        "summary": "Mobilized within four hours, contained lateral movement within twelve, and restored production operations within six business days.",
        "challenge": "A destructive payload entered the corporate estate via a compromised contractor laptop and began encrypting endpoints across multiple sites. The OT network was at risk; production downtime was measured in millions of dollars per day.",
        "approach": "Sectrex Incident Response mobilized on retainer within four hours. Isolated affected segments, validated OT integrity, ran parallel forensic and recovery tracks, and rebuilt identity-trust posture before reconnecting workloads.",
        "outcome": "OT network never breached. Corporate environment restored in six business days. Root cause traced to a single contractor credential. Lessons-learned report accepted by the regulator on first review.",
        "headline_metric": "6 days",
        "headline_metric_label": "Operations restored",
        "tags": ["Incident Response", "OT", "Forensics"],
        "published_at": date(2025, 3, 20),
        "display_order": 30,
    },
    {
        "title": "Zero Trust rollout across a multinational telecom",
        "client_name": "Regional Telecom Group",
        "sector": "telecom",
        "region": "GCC",
        "summary": "Retired 600+ implicit-trust pathways across five countries and 38,000 employees over an 18-month phased rollout.",
        "challenge": "The group's existing perimeter model couldn't accommodate hybrid workforce, M&A integrations, and partner ecosystems. Implicit-trust pathways had accumulated for over a decade.",
        "approach": "Established an identity-first zero trust architecture, phased the migration by business function, and operationalized continuous device posture across the workforce. Built a policy-as-code platform owned by the group's own engineers.",
        "outcome": "600+ legacy trust pathways retired. Audit findings on access controls fell 84%. Group now operates with explicit, scored, and revocable access across all five countries.",
        "headline_metric": "−84%",
        "headline_metric_label": "Reduction in access-related audit findings",
        "tags": ["Zero Trust", "Identity", "Multi-country"],
        "published_at": date(2025, 1, 10),
        "display_order": 40,
    },
    {
        "title": "Cyber due diligence for a USD 1.2B acquisition",
        "client_name": "GCC Holding Group",
        "sector": "banking",
        "region": "UAE",
        "summary": "Pre-close cyber diligence and 90-day post-close remediation plan that materially repriced the deal.",
        "challenge": "A regional holding company was acquiring a fintech target whose security disclosures were thin. Board needed an independent view before close and a credible integration plan after.",
        "approach": "Conducted a focused pre-close assessment covering identity, exposed surface area, third-party risk, and unresolved incidents. Produced a 90-day post-close remediation plan with named owners and budgeted controls.",
        "outcome": "Two material findings surfaced that repriced the acquisition by 6%. Post-close, the integration plan completed on schedule with zero regulator escalations.",
        "headline_metric": "6%",
        "headline_metric_label": "Material valuation adjustment surfaced pre-close",
        "tags": ["M&A", "Diligence", "Advisory"],
        "published_at": date(2024, 11, 5),
        "display_order": 50,
    },
    {
        "title": "Continuous adversary simulation for a sovereign healthcare network",
        "client_name": "Sovereign Healthcare Network",
        "sector": "healthcare",
        "region": "Qatar",
        "summary": "Continuous purple-team operations across 14 hospitals — tripling control coverage in the first year.",
        "challenge": "The network's annual penetration test left 11 months of blind time. Threat groups targeting healthcare had been observed in regional traffic; the board wanted continuous, not periodic, assurance.",
        "approach": "Deployed a continuous adversary simulation program with weekly emulation cycles aligned to MITRE ATT&CK techniques observed in healthcare-targeted campaigns. Detection engineering integrated directly into the cycle.",
        "outcome": "Control coverage across high-priority techniques tripled in twelve months. Five live detection gaps closed during the first quarter. Annual external test now produces zero novel findings.",
        "headline_metric": "3×",
        "headline_metric_label": "Increase in control coverage in twelve months",
        "tags": ["Red Team", "Purple Team", "MITRE ATT&CK"],
        "published_at": date(2024, 8, 22),
        "display_order": 60,
    },
]


JOBS = [
    {
        "title": "Senior SOC Analyst (Tier 3)",
        "department": "soc",
        "employment_type": "full_time",
        "level": "senior",
        "location": "Dubai, UAE",
        "is_remote_friendly": False,
        "summary": "Own complex investigations across client environments; close the loop between detection and response.",
        "description": "You'll lead tier-3 investigations, mentor tier-1/2 analysts, and contribute to the detection engineering backlog. Expect to handle the alerts other analysts escalate, and to own the post-incident analysis that improves the detection model.",
        "requirements": [
            "5+ years in security operations, including tier-3 investigations",
            "Deep familiarity with MITRE ATT&CK and detection engineering",
            "Hands-on with at least one major SIEM and one EDR platform",
            "Strong written communication — you'll write findings the regulator will read",
        ],
        "nice_to_have": [
            "Experience operating in regulated environments (SAMA, NCA, CBUAE)",
            "GCFA, GCIH, or equivalent certifications",
            "Arabic-language fluency",
        ],
    },
    {
        "title": "Principal Cloud Security Engineer",
        "department": "cloud",
        "employment_type": "full_time",
        "level": "principal",
        "location": "Dubai, UAE",
        "is_remote_friendly": True,
        "summary": "Define and ship Sectrex's cloud security reference architectures across AWS, Azure, and OCI.",
        "description": "You'll set the technical direction for our cloud practice — landing zones, detection pipelines, workload protection — and ship those designs into client environments alongside our engagement teams.",
        "requirements": [
            "8+ years in cloud engineering with a security specialization",
            "Designed multi-account landing zones at enterprise scale",
            "Comfortable with policy-as-code (OPA, Sentinel, or equivalents)",
            "Track record shipping detection content for cloud-native telemetry",
        ],
        "nice_to_have": [
            "Experience with sovereign-cloud deployments",
            "AWS / Azure / OCI top-tier certifications",
            "Open-source contributions in the cloud-security space",
        ],
    },
    {
        "title": "Incident Response Lead",
        "department": "offensive",
        "employment_type": "full_time",
        "level": "lead",
        "location": "Riyadh, KSA",
        "is_remote_friendly": False,
        "summary": "Lead containment, forensics, and recovery on retainer engagements across the Kingdom.",
        "description": "You will be the named principal on incident retainers — first on the bridge, last off the call. You'll lead a small forensics team and coordinate directly with client CISOs, legal counsel, and regulators when required.",
        "requirements": [
            "10+ years in incident response across enterprise environments",
            "Led containment on at least one nation-state-grade intrusion",
            "Fluency in endpoint and cloud forensics with chain-of-custody discipline",
            "Calm under pressure, clear under scrutiny",
        ],
        "nice_to_have": [
            "Arabic-language fluency",
            "GCFA / GCFE / GREM",
            "Experience reporting to GCC regulators",
        ],
    },
    {
        "title": "Threat Intelligence Analyst — Regional Focus",
        "department": "threat_intel",
        "employment_type": "full_time",
        "level": "mid",
        "location": "Dubai, UAE",
        "is_remote_friendly": True,
        "summary": "Track adversary groups targeting GCC financial services, energy, and government sectors.",
        "description": "You'll own a portfolio of adversary groups, maintain campaign timelines, and produce intelligence products consumed by our SOC, our clients, and the regional community we contribute to.",
        "requirements": [
            "3+ years in threat intelligence at an enterprise or vendor",
            "Disciplined analytic tradecraft — you cite, hedge, and revise",
            "Hands-on with malware triage and infrastructure analysis",
            "Strong writing in English; ability to brief executives",
        ],
        "nice_to_have": [
            "Native or fluent Arabic",
            "Experience producing regulator-aligned threat assessments",
            "Open-source intelligence publication history",
        ],
    },
    {
        "title": "Offensive Security Engineer (Red Team)",
        "department": "offensive",
        "employment_type": "full_time",
        "level": "senior",
        "location": "Dubai, UAE",
        "is_remote_friendly": True,
        "summary": "Build and execute adversary emulation campaigns that meaningfully test client defenses.",
        "description": "You'll plan and execute red and purple team engagements grounded in current threat campaigns. The goal is not just to find paths — it's to improve detection. Every engagement closes with detection content shipped to the SOC.",
        "requirements": [
            "5+ years in offensive security with red-team engagement leadership",
            "Deep familiarity with C2 frameworks and modern adversary tradecraft",
            "Track record collaborating with blue teams to close gaps",
            "Strong writing — your reports are read by CISOs and boards",
        ],
        "nice_to_have": [
            "OSCP, OSEP, CRTO, or equivalent certifications",
            "Open-source tooling contributions",
            "Comfortable operating across hybrid and cloud-native estates",
        ],
    },
    {
        "title": "vCISO Advisor",
        "department": "grc",
        "employment_type": "full_time",
        "level": "principal",
        "location": "Dubai, UAE",
        "is_remote_friendly": True,
        "summary": "Serve as named virtual CISO for select client engagements during leadership transitions.",
        "description": "You'll act as the operational and strategic security leader for clients between permanent CISO appointments. The role spans board reporting, regulator engagement, program ownership, and team development.",
        "requirements": [
            "15+ years across enterprise security leadership roles",
            "Reported to executive committees and / or regulators",
            "Track record in the GCC or directly comparable markets",
            "Sector specialization in banking, energy, or government",
        ],
        "nice_to_have": [
            "Former CISO experience at a regulated enterprise",
            "Arabic-language fluency",
            "CISSP, CISM, or equivalent certifications",
        ],
    },
]


class Command(BaseCommand):
    help = "Seed Services, Case Studies, and Job Openings with realistic demo content."

    def handle(self, *args, **options):
        self._seed_services()
        self._seed_case_studies()
        self._seed_jobs()
        self.stdout.write(self.style.SUCCESS("Demo content seeded."))

    @staticmethod
    def _icon_key_for(svg):
        """Reverse-map an inline SVG back to its icon registry key."""
        for key, markup in ICONS.items():
            if markup == svg:
                return key
        return "shield"

    def _seed_services(self):
        teasers = {t["anchor"]: t for t in SERVICE_TEASERS}
        for order, s in enumerate(SERVICE_DETAIL, start=1):
            teaser = teasers.get(s["anchor"], {})
            Service.objects.get_or_create(
                slug=s["anchor"],
                defaults={
                    "title":             s["title"],
                    "short_description": teaser.get("summary", s["intro"])[:240],
                    "description":       s["intro"],
                    "icon_key":          self._icon_key_for(s.get("icon", "")),
                    "capabilities":      s["capabilities"],
                    "anchor":            s["anchor"],
                    "tag":               s.get("tag", ""),
                    "intro":             s["intro"],
                    "outcome":           s.get("outcome", "")[:240],
                    "display_order":     order,
                    "is_published":      True,
                },
            )
        self.stdout.write(f"  · Services: {Service.objects.count()}")

    def _seed_case_studies(self):
        for cs in CASE_STUDIES:
            slug = slugify(f"{cs['client_name']}-{cs['title']}")[:180]
            CaseStudy.objects.get_or_create(slug=slug, defaults=cs)
        self.stdout.write(f"  · Case Studies: {CaseStudy.objects.count()}")

    def _seed_jobs(self):
        for j in JOBS:
            slug = slugify(j["title"])
            defaults = {**j, "apply_email": JobOpening._meta.get_field("apply_email").default}
            JobOpening.objects.get_or_create(slug=slug, defaults=defaults)
        self.stdout.write(f"  · Job Openings: {JobOpening.objects.count()}")
