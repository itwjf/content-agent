"""
商品管理模块 - Product API
"""
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.schemas import ProductCreate, ProductResponse

router = APIRouter()


# 模拟数据库（内存）- 后续可替换为真实 MySQL
products_db = {}


# 预置更多示例商品
def init_sample_products():
    """初始化示例商品"""
    sample_products = [
        {
            "sku_id": "12345",
            "name": "控油修护精华液",
            "category": "护肤品",
            "brand": "品牌A",
            "spec": "30ml",
            "price": 350,
            "original_price": 499,
            "ingredients": ["水杨酸", "烟酰胺", "透明质酸"],
            "effects": ["控油", "修护", "保湿"],
            "description": "专为油皮设计的控油修护精华，温和不刺激",
            "selling_points": ["油皮亲妈", "持久控油", "温和不刺激"]
        },
        {
            "sku_id": "67890",
            "name": "氨基酸洁面乳",
            "category": "护肤品",
            "brand": "品牌A",
            "spec": "100ml",
            "price": 129,
            "original_price": 199,
            "ingredients": ["氨基酸", "神经酰胺", "甘草酸二钾"],
            "effects": ["温和清洁", "补水", "舒缓"],
            "description": "氨基酸温和洁面，敏感肌可用",
            "selling_points": ["温和不刺激", "敏感肌适用", "泡沫丰富"]
        },
        {
            "sku_id": "11111",
            "name": "美白淡斑精华液",
            "category": "护肤品",
            "brand": "品牌B",
            "spec": "50ml",
            "price": 299,
            "original_price": 399,
            "ingredients": ["维生素C", "烟酰胺", "熊果苷"],
            "effects": ["美白", "淡斑", "提亮"],
            "description": "高浓度VC美白精华，28天提亮肤色",
            "selling_points": ["28天见效", "高浓度VC", "淡化色斑"]
        },
        {
            "sku_id": "22222",
            "name": "抗皱紧致面霜",
            "category": "护肤品",
            "brand": "品牌B",
            "spec": "50g",
            "price": 458,
            "original_price": 598,
            "ingredients": ["视黄醇", "胶原蛋白", "神经酰胺"],
            "effects": ["抗皱", "紧致", "滋润"],
            "description": "视黄醇抗皱面霜，淡化细纹紧致肌肤",
            "selling_points": ["淡化细纹", "紧致提拉", "滋润不油腻"]
        },
        {
            "sku_id": "33333",
            "name": "玻尿酸补水面膜",
            "category": "护肤品",
            "brand": "品牌C",
            "spec": "10片/盒",
            "price": 89,
            "original_price": 129,
            "ingredients": ["玻尿酸", "透明质酸", "甘油"],
            "effects": ["补水", "保湿", "滋润"],
            "description": "玻尿酸深层补水面膜，一片水润一整天",
            "selling_points": ["深层补水", "一片见效", "平价好用"]
        },
        {
            "sku_id": "44444",
            "name": "防晒隔离霜 SPF50+",
            "category": "彩妆",
            "brand": "品牌C",
            "spec": "40ml",
            "price": 168,
            "original_price": 218,
            "ingredients": ["二氧化钛", "氧化锌", "维生素E"],
            "effects": ["防晒", "隔离", "修饰肤色"],
            "description": "高倍防晒隔离霜，轻薄不油腻",
            "selling_points": ["SPF50+", "轻薄透气", "防晒隔离二合一"]
        },
        {
            "sku_id": "55555",
            "name": "修复护发精油",
            "category": "洗护",
            "brand": "品牌D",
            "spec": "100ml",
            "price": 79,
            "original_price": 99,
            "ingredients": ["摩洛哥坚果油", "荷荷巴油", "维生素E"],
            "effects": ["修复", "柔顺", "光泽"],
            "description": "修复干枯受损发质，一抹顺滑",
            "selling_points": ["修复分叉", "一抹顺滑", "不油腻"]
        },
        {
            "sku_id": "66666",
            "name": "眼部按摩仪",
            "category": "美容仪器",
            "brand": "品牌E",
            "spec": "1台",
            "price": 299,
            "original_price": 399,
            "ingredients": [],
            "effects": ["淡化黑眼圈", "缓解眼疲劳", "促进吸收"],
            "description": "微电流眼部按摩仪，淡化黑眼圈眼袋",
            "selling_points": ["微电流按摩", "淡化黑眼圈", "便携易用"]
        }
    ]

    for p in sample_products:
        if p["sku_id"] not in products_db:
            p["id"] = len(products_db) + 1
            products_db[p["sku_id"]] = p


# 初始化示例数据
init_sample_products()


@router.post("/products", response_model=ProductResponse)
async def create_product(product: ProductCreate):
    """创建商品"""
    if product.sku_id in products_db:
        raise HTTPException(status_code=400, detail="商品 SKU 已存在")

    product_dict = product.model_dump()
    product_dict["id"] = len(products_db) + 1
    products_db[product.sku_id] = product_dict

    return ProductResponse(
        id=product_dict["id"],
        sku_id=product.sku_id,
        name=product.name,
        category=product.category,
        brand=product.brand,
        spec=product.spec,
        price=product.price,
        original_price=product.original_price,
        ingredients=product.ingredients,
        effects=product.effects,
        description=product.description,
        selling_points=product.selling_points,
        created_at=None,  # 简化处理
        updated_at=None
    )


@router.get("/products", response_model=List[ProductResponse])
async def list_products():
    """获取商品列表"""
    return [
        ProductResponse(
            id=v["id"],
            sku_id=k,
            name=v["name"],
            category=v.get("category"),
            brand=v.get("brand"),
            spec=v.get("spec"),
            price=v["price"],
            original_price=v.get("original_price"),
            ingredients=v.get("ingredients", []),
            effects=v.get("effects", []),
            description=v.get("description"),
            selling_points=v.get("selling_points", []),
            created_at=None,
            updated_at=None
        )
        for k, v in products_db.items()
    ]


@router.get("/products/{sku_id}", response_model=ProductResponse)
async def get_product(sku_id: str):
    """获取单个商品"""
    if sku_id not in products_db:
        raise HTTPException(status_code=404, detail="商品不存在")

    product = products_db[sku_id]
    return ProductResponse(
        id=product["id"],
        sku_id=sku_id,
        name=product["name"],
        category=product.get("category"),
        brand=product.get("brand"),
        spec=product.get("spec"),
        price=product["price"],
        original_price=product.get("original_price"),
        ingredients=product.get("ingredients", []),
        effects=product.get("effects", []),
        description=product.get("description"),
        selling_points=product.get("selling_points", []),
        created_at=None,
        updated_at=None
    )


@router.delete("/products/{sku_id}")
async def delete_product(sku_id: str):
    """删除商品"""
    if sku_id not in products_db:
        raise HTTPException(status_code=404, detail="商品不存在")

    del products_db[sku_id]
    return {"message": "商品已删除"}



