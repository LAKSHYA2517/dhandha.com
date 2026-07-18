import logging
from datetime import datetime, timezone

from beanie import PydanticObjectId
from beanie.operators import In
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import CurrentUser, get_current_user
from app.models.company import Company
from app.models.order import Order
from app.models.product import Product
from app.schemas.product import OrderCreateRequest, ProductCreateRequest, ProductUpdateRequest
from app.services.whatsapp_service import send_whatsapp_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/products", tags=["products"])
orders_router = APIRouter(prefix="/api/orders", tags=["orders"])

# Ties product listing to the platform's core compliance score — matches the
# same >=50 threshold Phase 1 used for "compliant" status.
MIN_RCI_TO_LIST = 50.0


async def _get_own_company(current_user: CurrentUser) -> Company:
    company = await Company.find_one(Company.user_id == current_user.id)
    if not company:
        raise HTTPException(status_code=400, detail="Create a company profile first")
    return company


@router.post("", status_code=201)
async def create_product(payload: ProductCreateRequest, current_user: CurrentUser = Depends(get_current_user)):
    if current_user.role not in ("seller", "admin"):
        raise HTTPException(status_code=403, detail="Only sellers can list products")

    company = await _get_own_company(current_user)

    if (company.current_rci_score or 0) < MIN_RCI_TO_LIST:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Your company's RCI score ({company.current_rci_score or 0}) is below the minimum "
                f"required to list products ({MIN_RCI_TO_LIST}). Run a compliance check to improve it."
            ),
        )

    product = Product(company_id=company.id, user_id=current_user.id, **payload.model_dump())
    await product.insert()
    return {"success": True, "product": product}


@router.get("")
async def list_marketplace(current_user: CurrentUser = Depends(get_current_user)):
    products = await Product.find(Product.is_active == True, Product.quantity_available > 0).to_list()  # noqa: E712
    # ObjectIds embed their creation timestamp — sorting by id descending
    # surfaces the newest listings first without needing a separate field.
    products.sort(key=lambda p: p.id, reverse=True)

    company_ids = list({p.company_id for p in products})
    companies = await Company.find(In(Company.id, company_ids)).to_list() if company_ids else []
    company_map = {c.id: c for c in companies}

    results = []
    for p in products:
        seller = company_map.get(p.company_id)
        results.append({
            "id": str(p.id),
            "name": p.name,
            "description": p.description,
            "category": p.category,
            "price": p.price,
            "currency": p.currency,
            "quantity_available": p.quantity_available,
            "image_url": f"/uploads/{p.image_path}" if p.image_path else None,
            "seller": {
                "company_id": str(p.company_id),
                "name": seller.name if seller else "Unknown",
                "country": seller.country if seller else None,
                "industry": seller.industry if seller else None,
                "current_rci_score": seller.current_rci_score if seller else None,
                "compliance_status": seller.compliance_status if seller else False,
                "rci_breakdown": seller.rci_breakdown if seller else {},
                "rci_subcomponents": seller.rci_subcomponents if seller else {},
                "latest_ai_explanation": seller.latest_ai_explanation if seller else None,
            },
        })

    return {"success": True, "products": results}


@router.get("/mine")
async def list_my_products(current_user: CurrentUser = Depends(get_current_user)):
    company = await _get_own_company(current_user)
    products = await Product.find(Product.company_id == company.id).to_list()
    return {"success": True, "products": products}


@router.put("/{product_id}")
async def update_product(
    product_id: PydanticObjectId,
    payload: ProductUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    company = await _get_own_company(current_user)
    product = await Product.get(product_id)
    if not product or product.company_id != company.id:
        raise HTTPException(status_code=404, detail="Product not found")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc)
    await product.set(updates)
    return {"success": True, "product": product}


@router.delete("/{product_id}")
async def delete_product(product_id: PydanticObjectId, current_user: CurrentUser = Depends(get_current_user)):
    company = await _get_own_company(current_user)
    product = await Product.get(product_id)
    if not product or product.company_id != company.id:
        raise HTTPException(status_code=404, detail="Product not found")

    await product.set({"is_active": False, "updated_at": datetime.now(timezone.utc)})
    return {"success": True}


@router.post("/{product_id}/order", status_code=201)
async def order_product(
    product_id: PydanticObjectId,
    payload: OrderCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    product = await Product.get(product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")

    buyer_company = await Company.find_one(Company.user_id == current_user.id)
    if buyer_company and buyer_company.id == product.company_id:
        raise HTTPException(status_code=400, detail="You cannot order your own product")

    if payload.quantity > product.quantity_available:
        raise HTTPException(status_code=400, detail=f"Only {product.quantity_available} units available")

    total_price = round(payload.quantity * product.price, 2)
    order = Order(
        product_id=product.id,
        product_name=product.name,
        seller_company_id=product.company_id,
        buyer_user_id=current_user.id,
        quantity=payload.quantity,
        unit_price=product.price,
        total_price=total_price,
        currency=product.currency,
        shipping_address=payload.shipping_address.model_dump(),
    )
    await order.insert()

    await product.set({
        "quantity_available": product.quantity_available - payload.quantity,
        "updated_at": datetime.now(timezone.utc),
    })

    await _notify_seller_of_order(product, order, payload.shipping_address, current_user)

    return {"success": True, "order": order}


async def _notify_seller_of_order(product: Product, order: Order, shipping_address, buyer: CurrentUser) -> None:
    seller_company = await Company.get(product.company_id)
    if not seller_company or not seller_company.whatsapp_number:
        return  # no WhatsApp number on file for this seller — nothing to notify

    address_lines = [shipping_address.address_line1]
    if shipping_address.address_line2:
        address_lines.append(shipping_address.address_line2)
    address_lines.append(f"{shipping_address.city}, {shipping_address.state} {shipping_address.postal_code}")
    address_lines.append(shipping_address.country)
    address_block = "\n".join(address_lines)

    message = (
        f"🛒 New Order Received!\n\n"
        f"Product: {product.name}\n"
        f"Quantity: {order.quantity}\n"
        f"Amount: {order.currency} {order.total_price}\n\n"
        f"Shipping to:\n{shipping_address.full_name} ({shipping_address.phone})\n{address_block}\n\n"
        f"Buyer: {buyer.name} ({buyer.email})"
    )

    try:
        await send_whatsapp_message(seller_company.whatsapp_number, message)
    except Exception:
        # A failed vendor notification shouldn't roll back a successful order.
        logger.exception("Failed to notify seller %s of new order %s", seller_company.id, order.id)


@orders_router.get("/mine")
async def my_orders(current_user: CurrentUser = Depends(get_current_user)):
    orders = await Order.find(Order.buyer_user_id == current_user.id).sort(-Order.created_at).to_list()
    return {"success": True, "orders": orders}


@orders_router.get("/received")
async def received_orders(current_user: CurrentUser = Depends(get_current_user)):
    company = await _get_own_company(current_user)
    orders = await Order.find(Order.seller_company_id == company.id).sort(-Order.created_at).to_list()
    return {"success": True, "orders": orders}
