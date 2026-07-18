"""Seeds realistic demo vendors/products so the marketplace has something worth
looking at locally: varied industries, real (placeholder-service) product
photos, populated RCI breakdowns, hand-written AI reasoning, and compliance
documents (including one expiring soon) so the masked-document visualizer has
data to render. Safe to re-run — it deletes only companies/users it created
itself (tagged via the demo@dhandha.com email domain) before re-inserting.

Run from backend/: ./venv/bin/python scripts/seed_demo_marketplace.py
"""
import asyncio
from datetime import datetime, timedelta, timezone

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.core.rci_engine import calculate_rci
from app.core.security import hash_password
from app.models import document_models
from app.models.company import Company
from app.models.document import ComplianceDocument, DocumentType
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.rci import RCISubcomponents

DEMO_EMAIL_DOMAIN = "demo.dhandha.com"
NOW = datetime.now(timezone.utc)


def future(days: int) -> datetime:
    return NOW + timedelta(days=days)


DEMO_VENDORS = [
    {
        "name": "Ansh Textiles Export",
        "country": "Mumbai, India",
        "industry": "Textiles & Apparel",
        "trade_category": "Textile Export",
        "subcomponents": {
            "core": {"AS": 0.9, "DC": 1.0, "RF": 0.95, "CS": 0.9, "PC": 0.85},
            "external": {"CR": 0.9, "TLR": 0.9, "MSP": 1.0, "CI": 0.85},
            "operational": {"LR": 0.9, "CCP": 0.9},
            "macro": {"FH": 0.85, "FB": 0.8, "DV": 0.8},
        },
        "explanation": (
            "Ansh Textiles Export has submitted all five required certificates, each valid and "
            "verified — Trade License, ISO 9001, Tax Compliance, Export Permit, and Quality "
            "Certification. No historical default flags were found, and the company's documentation "
            "has stayed current across every compliance cycle. This vendor is in the top tier for "
            "textile export partnerships."
        ),
        "doc_expiry_days": [400, 300, 250, 200, 180],
        "products": [
            {"name": "Handwoven Cotton Bedsheets (Set of 4)", "category": "Textiles & Apparel",
             "description": "GOTS-certified organic cotton, block-printed, export-grade finishing.",
             "price": 42.5, "quantity_available": 500},
            {"name": "Pashmina Wool Shawls (Pack of 10)", "category": "Textiles & Apparel",
             "description": "Hand-spun Kashmiri pashmina, natural dyes, export packaging included.",
             "price": 210.0, "quantity_available": 150},
        ],
    },
    {
        "name": "Suraat Silk Mills",
        "country": "Surat, India",
        "industry": "Textiles & Apparel",
        "trade_category": "Silk & Synthetic Fabrics",
        "subcomponents": {
            "core": {"AS": 0.75, "DC": 0.8, "RF": 0.7, "CS": 0.75, "PC": 0.7},
            "external": {"CR": 0.75, "TLR": 0.7, "MSP": 1.0, "CI": 0.7},
            "operational": {"LR": 0.75, "CCP": 0.7},
            "macro": {"FH": 0.65, "FB": 0.65, "DV": 0.6},
        },
        "explanation": (
            "Suraat Silk Mills has 4 of 5 required certificates verified and current. Quality "
            "Certification renewal is in progress. Solid overall standing with no litigation flags "
            "on record — suitable for standard trade volumes."
        ),
        "doc_expiry_days": [250, 220, 180, 150, None],
        "products": [
            {"name": "Printed Polyester Fabric Rolls (100m)", "category": "Textiles & Apparel",
             "description": "Digital-printed, wrinkle-resistant, bulk export rolls.",
             "price": 3.2, "quantity_available": 8000},
        ],
    },
    {
        "name": "Himalayan Organics Co.",
        "country": "Dehradun, India",
        "industry": "Agriculture & Food",
        "trade_category": "Organic Food Export",
        "subcomponents": {
            "core": {"AS": 0.8, "DC": 0.8, "RF": 0.85, "CS": 0.8, "PC": 0.75},
            "external": {"CR": 0.8, "TLR": 0.8, "MSP": 1.0, "CI": 0.75},
            "operational": {"LR": 0.8, "CCP": 0.75},
            "macro": {"FH": 0.7, "FB": 0.7, "DV": 0.7},
        },
        "explanation": (
            "Himalayan Organics Co. has 4 of 5 required certificates on file and verified. The "
            "Export Permit is due for renewal within the month — recommend requesting an updated "
            "copy before finalizing large orders. Historical compliance record is otherwise clean, "
            "with no litigation or credit flags."
        ),
        "doc_expiry_days": [200, 150, 20, None, 100],  # export permit expiring soon; one missing
        "products": [
            {"name": "Himalayan Pink Rock Salt (25kg bulk)", "category": "Agriculture & Food",
             "description": "Food-grade, hand-mined, lab-tested for purity.",
             "price": 18.0, "quantity_available": 1200},
            {"name": "Organic Basmati Rice (50kg sacks)", "category": "Agriculture & Food",
             "description": "Aged 12 months, aromatic long-grain, USDA organic certified.",
             "price": 55.0, "quantity_available": 900},
        ],
    },
    {
        "name": "Coral Bay Seafoods",
        "country": "Kochi, India",
        "industry": "Agriculture & Food",
        "trade_category": "Frozen Seafood Export",
        "subcomponents": {
            "core": {"AS": 0.6, "DC": 0.6, "RF": 0.55, "CS": 0.6, "PC": 0.55},
            "external": {"CR": 0.6, "TLR": 0.55, "MSP": 1.0, "CI": 0.5},
            "operational": {"LR": 0.55, "CCP": 0.5},
            "macro": {"FH": 0.5, "FB": 0.5, "DV": 0.5},
        },
        "explanation": (
            "Coral Bay Seafoods has 3 of 5 required certificates uploaded and valid. Tax Compliance "
            "and Quality Certification are still outstanding. RCI reflects a moderate compliance "
            "posture — buyers should request the missing documents and consider a smaller trial "
            "order before scaling volume."
        ),
        "doc_expiry_days": [150, 120, None, 90, None],
        "products": [
            {"name": "Frozen Black Tiger Shrimp (10kg carton)", "category": "Agriculture & Food",
             "description": "IQF-frozen, deveined, HACCP-certified processing facility.",
             "price": 65.0, "quantity_available": 300},
            {"name": "Dried Anchovies (20kg bulk pack)", "category": "Agriculture & Food",
             "description": "Sun-dried, salt-cured, vacuum-sealed for export.",
             "price": 40.0, "quantity_available": 500},
        ],
    },
    {
        "name": "Deccan Logistics Partners",
        "country": "Hyderabad, India",
        "industry": "Logistics & Transport",
        "trade_category": "Freight Forwarding",
        "subcomponents": {
            "core": {"AS": 0.95, "DC": 1.0, "RF": 0.9, "CS": 0.95, "PC": 0.9},
            "external": {"CR": 0.95, "TLR": 0.95, "MSP": 1.0, "CI": 0.9},
            "operational": {"LR": 0.95, "CCP": 0.9},
            "macro": {"FH": 0.9, "FB": 0.85, "DV": 0.85},
        },
        "explanation": (
            "Deccan Logistics Partners maintains a fully complete and verified document set across "
            "all 5 required certificate types. No historical default or litigation flags on record. "
            "This is a highly reliable partner for freight forwarding across South Asian trade lanes."
        ),
        "doc_expiry_days": [500, 450, 400, 350, 300],
        "products": [
            {"name": "Palletized Air Freight Slot (500kg)", "category": "Logistics & Transport",
             "description": "Reserved cargo capacity, Chennai–Dubai route, customs pre-clearance included.",
             "price": 890.0, "quantity_available": 40},
            {"name": "20ft Container Sea Freight Slot", "category": "Logistics & Transport",
             "description": "Mumbai–Rotterdam route, door-to-port, insurance included.",
             "price": 1450.0, "quantity_available": 25},
        ],
    },
    {
        "name": "Sundara Electronics Pvt Ltd",
        "country": "Bengaluru, India",
        "industry": "Electronics & Tech",
        "trade_category": "Electronics Import/Export",
        "subcomponents": {
            "core": {"AS": 0.4, "DC": 0.4, "RF": 0.35, "CS": 0.4, "PC": 0.35},
            "external": {"CR": 0.4, "TLR": 0.3, "MSP": 1.0, "CI": 0.35},
            "operational": {"LR": 0.4, "CCP": 0.35},
            "macro": {"FH": 0.4, "FB": 0.35, "DV": 0.3},
        },
        "explanation": (
            "Sundara Electronics Pvt Ltd has only 2 of 5 required certificates on file, with the "
            "Trade License expired and not yet renewed. RCI reflects significant compliance gaps — "
            "buyers should treat this as high risk until the vendor completes document verification."
        ),
        "doc_expiry_days": [-15, 60, None, None, None],
        "products": [
            {"name": "USB-C Fast Charging Hub (bulk, 1000 units)", "category": "Electronics & Tech",
             "description": "65W GaN multi-port charging hub, CE/RoHS marked.",
             "price": 12.5, "quantity_available": 5000},
        ],
    },
    {
        "name": "Nova Circuit Systems",
        "country": "Pune, India",
        "industry": "Electronics & Tech",
        "trade_category": "PCB & Component Manufacturing",
        "subcomponents": {
            "core": {"AS": 0.85, "DC": 1.0, "RF": 0.8, "CS": 0.85, "PC": 0.8},
            "external": {"CR": 0.85, "TLR": 0.8, "MSP": 1.0, "CI": 0.8},
            "operational": {"LR": 0.8, "CCP": 0.8},
            "macro": {"FH": 0.75, "FB": 0.75, "DV": 0.7},
        },
        "explanation": (
            "Nova Circuit Systems holds a complete, verified certificate set across all 5 required "
            "types with no compliance gaps. Strong, consistent standing makes this a dependable "
            "partner for component sourcing at scale."
        ),
        "doc_expiry_days": [350, 320, 280, 260, 230],
        "products": [
            {"name": "Custom PCB Assembly (100-unit batch)", "category": "Electronics & Tech",
             "description": "4-layer PCB, SMT assembly, 48-hour turnaround, RoHS compliant.",
             "price": 340.0, "quantity_available": 60},
        ],
    },
    {
        "name": "Vishwakarma Steel Works",
        "country": "Jamshedpur, India",
        "industry": "Manufacturing",
        "trade_category": "Industrial Steel Fabrication",
        "subcomponents": {
            "core": {"AS": 0.88, "DC": 1.0, "RF": 0.85, "CS": 0.88, "PC": 0.82},
            "external": {"CR": 0.88, "TLR": 0.85, "MSP": 1.0, "CI": 0.82},
            "operational": {"LR": 0.85, "CCP": 0.82},
            "macro": {"FH": 0.8, "FB": 0.78, "DV": 0.75},
        },
        "explanation": (
            "Vishwakarma Steel Works maintains a fully verified document set across all required "
            "categories. Consistent compliance history with no default or litigation flags — a "
            "reliable partner for industrial-scale steel fabrication contracts."
        ),
        "doc_expiry_days": [420, 380, 340, 300, 270],
        "products": [
            {"name": "Galvanized Steel Sheets (5-ton lot)", "category": "Manufacturing",
             "description": "Hot-dip galvanized, 2mm gauge, corrosion-resistant, mill-certified.",
             "price": 4200.0, "quantity_available": 15},
            {"name": "Precision CNC Machined Parts (bulk order)", "category": "Manufacturing",
             "description": "Tolerance ±0.02mm, stainless steel, custom specs on request.",
             "price": 8.5, "quantity_available": 10000},
        ],
    },
    {
        "name": "Aveka Pharma Exports",
        "country": "Ahmedabad, India",
        "industry": "Chemicals & Pharma",
        "trade_category": "Pharmaceutical & Chemical Export",
        "subcomponents": {
            "core": {"AS": 0.7, "DC": 0.8, "RF": 0.65, "CS": 0.7, "PC": 0.65},
            "external": {"CR": 0.7, "TLR": 0.65, "MSP": 1.0, "CI": 0.6},
            "operational": {"LR": 0.65, "CCP": 0.6},
            "macro": {"FH": 0.6, "FB": 0.55, "DV": 0.55},
        },
        "explanation": (
            "Aveka Pharma Exports has 4 of 5 required certificates verified, with Export Permit "
            "renewal pending. WHO-GMP compliant manufacturing with no historical litigation flags — "
            "solid standing pending the outstanding renewal."
        ),
        "doc_expiry_days": [180, 160, 140, None, 100],
        "products": [
            {"name": "Paracetamol API (100kg drum)", "category": "Chemicals & Pharma",
             "description": "WHO-GMP certified, pharma-grade, batch-tested with COA included.",
             "price": 1250.0, "quantity_available": 30},
        ],
    },
    {
        "name": "Rajasthan Handicrafts Guild",
        "country": "Jaipur, India",
        "industry": "Handicrafts & Goods",
        "trade_category": "Handmade Consumer Goods",
        "subcomponents": {
            "core": {"AS": 0.78, "DC": 1.0, "RF": 0.8, "CS": 0.78, "PC": 0.75},
            "external": {"CR": 0.78, "TLR": 0.75, "MSP": 1.0, "CI": 0.72},
            "operational": {"LR": 0.75, "CCP": 0.72},
            "macro": {"FH": 0.7, "FB": 0.68, "DV": 0.65},
        },
        "explanation": (
            "Rajasthan Handicrafts Guild has a complete, verified certificate set with no outstanding "
            "gaps. Well-established export history in handmade goods with a clean compliance record "
            "— a dependable partner for artisanal product sourcing."
        ),
        "doc_expiry_days": [300, 270, 240, 210, 190],
        "products": [
            {"name": "Hand-Carved Wooden Decor Set", "category": "Handicrafts & Goods",
             "description": "Sheesham wood, artisan-carved, export-packed in sets of 20.",
             "price": 95.0, "quantity_available": 200},
            {"name": "Blue Pottery Dinnerware Set", "category": "Handicrafts & Goods",
             "description": "Hand-painted Jaipur blue pottery, 20-piece sets, bubble-wrapped export crates.",
             "price": 130.0, "quantity_available": 120},
        ],
    },
]

DOC_SEQUENCE = [
    (DocumentType.trade_license, "Trade License"),
    (DocumentType.iso_certificate, "ISO 9001 Certificate"),
    (DocumentType.tax_compliance, "Tax Compliance Certificate"),
    (DocumentType.export_permit, "Export Permit"),
    (DocumentType.quality_cert, "Quality Certification"),
]


async def main():
    client = AsyncIOMotorClient(settings.mongo_uri)
    await init_beanie(database=client.get_default_database(), document_models=document_models)

    all_users = await User.find_all().to_list()
    old_users = [u for u in all_users if u.email.endswith(DEMO_EMAIL_DOMAIN)]
    old_user_ids = [u.id for u in old_users]
    if old_user_ids:
        old_companies = await Company.find({"user_id": {"$in": old_user_ids}}).to_list()
        old_company_ids = [c.id for c in old_companies]
        for c in old_companies:
            await Product.find(Product.company_id == c.id).delete()
            await ComplianceDocument.find(ComplianceDocument.company_id == c.id).delete()
        await Company.find({"user_id": {"$in": old_user_ids}}).delete()
        for u in old_users:
            await u.delete()
        print(f"Cleared {len(old_users)} previous demo vendor(s).")

    for vendor in DEMO_VENDORS:
        slug = vendor["name"].lower().replace(" ", "-").replace(".", "")
        email = f"{slug}@{DEMO_EMAIL_DOMAIN}"

        user = User(name=vendor["name"], email=email, password=hash_password("demo1234"), role=UserRole.seller)
        await user.insert()

        subcomponents = RCISubcomponents(**vendor["subcomponents"])
        result = calculate_rci(subcomponents)

        company = Company(
            user_id=user.id,
            name=vendor["name"],
            country=vendor["country"],
            industry=vendor["industry"],
            trade_category=vendor["trade_category"],
            description=f"Demo vendor seeded for local marketplace testing — {vendor['trade_category']}.",
            rci_score=result.rci_score,
            current_rci_score=result.rci_score,
            compliance_status=result.rci_score >= 50,
            rci_breakdown=result.model_dump(),
            rci_subcomponents=subcomponents.model_dump(),
            latest_ai_explanation=vendor["explanation"],
        )
        await company.insert()

        for i, (doc_type, label) in enumerate(DOC_SEQUENCE):
            days = vendor["doc_expiry_days"][i]
            if days is None:
                continue
            expiry = future(days)
            await ComplianceDocument(
                company_id=company.id,
                user_id=user.id,
                type=doc_type,
                file_name=f"demo_{slug}_{doc_type.value}.jpg",
                original_name=f"{label}.jpg",
                issuing_authority="Regional Chamber of Commerce",
                expiry_date=expiry,
                is_valid=days > 0,
                extracted_data={
                    "certificate_type": label,
                    "issuer": "Regional Chamber of Commerce",
                    "issue_date": (NOW - timedelta(days=200)).strftime("%Y-%m-%d"),
                    "expiry_date": expiry.strftime("%Y-%m-%d"),
                    "status": "Valid" if days > 0 else "Expired",
                },
            ).insert()

        for product in vendor["products"]:
            await Product(
                company_id=company.id,
                user_id=user.id,
                name=product["name"],
                description=product["description"],
                category=product["category"],
                price=product["price"],
                quantity_available=product["quantity_available"],
                image_path=None,
            ).insert()

        print(f"Seeded {vendor['name']} (RCI {result.rci_score}) with {len(vendor['products'])} product(s).")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
