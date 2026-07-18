from app.models.company import Company
from app.models.document import ComplianceDocument
from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.models.whatsapp_session import WhatsAppSession

document_models = [
    Company,
    ComplianceDocument,
    Order,
    Product,
    User,
    WhatsAppSession,
]
