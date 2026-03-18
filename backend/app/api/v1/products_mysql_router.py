"""
MySQL版本商品管理路由
"""
from fastapi import APIRouter
from app.api.products_mysql import router as mysql_products_router
from app.api.product_upload import router as product_upload_router

router = APIRouter()

router.include_router(mysql_products_router, prefix="/products", tags=["商品管理(MySQL)"])
router.include_router(product_upload_router, prefix="/products", tags=["商品管理(MySQL)"])