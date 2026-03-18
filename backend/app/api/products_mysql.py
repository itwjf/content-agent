"""
商品管理模块 - MySQL版本
用于替换内存存储，实现数据持久化
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product_models import Product
from app.schemas.schemas import ProductCreate, ProductResponse
from app.services.product_service import ProductService

router = APIRouter()


@router.post("/products", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    """创建商品"""
    try:
        db_product = product_service.create_product(product)
        return ProductResponse(
            id=db_product.id,
            sku_id=db_product.sku_id,
            name=db_product.name,
            category=db_product.category,
            brand=db_product.brand,
            spec=db_product.spec,
            price=db_product.price,
            original_price=db_product.original_price,
            ingredients=db_product.ingredients or [],
            effects=db_product.effects or [],
            description=db_product.description,
            selling_points=db_product.selling_points or [],
            created_at=db_product.created_at,
            updated_at=db_product.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    """获取商品列表"""
    products = product_service.get_products(skip=skip, limit=limit)
    return [
        ProductResponse(
            id=p.id,
            sku_id=p.sku_id,
            name=p.name,
            category=p.category,
            brand=p.brand,
            spec=p.spec,
            price=p.price,
            original_price=p.original_price,
            ingredients=p.ingredients or [],
            effects=p.effects or [],
            description=p.description,
            selling_points=p.selling_points or [],
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in products
    ]


@router.get("/products/{sku_id}", response_model=ProductResponse)
async def get_product(
    sku_id: str,
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    """获取单个商品"""
    product = product_service.get_product(sku_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    return ProductResponse(
        id=product.id,
        sku_id=product.sku_id,
        name=product.name,
        category=product.category,
        brand=product.brand,
        spec=product.spec,
        price=product.price,
        original_price=product.original_price,
        ingredients=product.ingredients or [],
        effects=product.effects or [],
        description=product.description,
        selling_points=product.selling_points or [],
        created_at=product.created_at,
        updated_at=product.updated_at
    )


@router.put("/products/{sku_id}", response_model=ProductResponse)
async def update_product(
    sku_id: str,
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    """更新商品"""
    updated_product = product_service.update_product(sku_id, product)
    if not updated_product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    return ProductResponse(
        id=updated_product.id,
        sku_id=updated_product.sku_id,
        name=updated_product.name,
        category=updated_product.category,
        brand=updated_product.brand,
        spec=updated_product.spec,
        price=updated_product.price,
        original_price=updated_product.original_price,
        ingredients=updated_product.ingredients or [],
        effects=updated_product.effects or [],
        description=updated_product.description,
        selling_points=updated_product.selling_points or [],
        created_at=updated_product.created_at,
        updated_at=updated_product.updated_at
    )


@router.delete("/products/{sku_id}")
async def delete_product(
    sku_id: str,
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    """删除商品"""
    success = product_service.delete_product(sku_id)
    if not success:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    return {"message": "商品已删除"}