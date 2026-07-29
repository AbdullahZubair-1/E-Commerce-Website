from fastapi import APIRouter
from app.api.v1 import auth, profile, categories, brands, products, cart, orders, admin, chatbot, superadmin, social, admin_notifications, appointments

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(categories.router)
api_router.include_router(brands.router)
api_router.include_router(products.router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(admin.router)
api_router.include_router(chatbot.router)
api_router.include_router(superadmin.router)
api_router.include_router(social.router)
api_router.include_router(admin_notifications.router)
api_router.include_router(appointments.router)