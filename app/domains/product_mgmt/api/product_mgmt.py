from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.domains.product_mgmt.schemes.product_mgmt import (
    CreateProduct,
    UpdateProduct,
    ProductInfo,
    ProductWithVersionsInfo,
    CreateVersion,
    UpdateVersion,
    VersionInfo,
)
from app.domains.product_mgmt.services.product_mgmt import ProductMgmtService


router = APIRouter()


@router.post("", response_model=ProductInfo)
async def create_product(
    data: CreateProduct,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """新增产品"""
    try:
        record = await ProductMgmtService.create_product(db, user_id, data)
        return ProductInfo.model_validate(record)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"新增产品失败: {str(e)}",
        )


@router.get("/list")
async def get_product_list(
    user_id: str = Query(..., description="用户ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: str = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
):
    """查询产品列表（含每个产品下的版本子列表）"""
    try:
        products, versions_by_product, total = await ProductMgmtService.get_product_and_version_list(
            db, user_id, page, page_size, keyword
        )
        items = [
            ProductWithVersionsInfo(
                **ProductInfo.model_validate(p).model_dump(),
                versions=[VersionInfo.model_validate(v) for v in versions_by_product.get(p.id, [])],
            )
            for p in products
        ]
        return {"items": items, "total": total}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询产品列表失败: {str(e)}",
        )


@router.get("/{product_id}", response_model=ProductInfo)
async def get_product(
    product_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """查询产品详情"""
    try:
        record = await ProductMgmtService.get_product_by_id(db, product_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品不存在")
        if record.create_user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限查看该产品")
        return ProductInfo.model_validate(record)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询产品失败: {str(e)}",
        )


@router.put("/{product_id}", response_model=ProductInfo)
async def update_product(
    product_id: str,
    data: UpdateProduct,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """修改产品"""
    try:
        record = await ProductMgmtService.update_product(db, product_id, user_id, data)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品不存在")
        return ProductInfo.model_validate(record)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"修改产品失败: {str(e)}",
        )


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """删除产品"""
    try:
        success = await ProductMgmtService.delete_product(db, product_id, user_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品不存在")
        return {"message": "产品删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除产品失败: {str(e)}",
        )


@router.post("/versions", response_model=VersionInfo)
async def create_version(
    data: CreateVersion,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """新增版本"""
    try:
        record = await ProductMgmtService.create_version(db, user_id, data)
        return VersionInfo.model_validate(record)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"新增版本失败: {str(e)}",
        )


@router.get("/versions/{version_id}", response_model=VersionInfo)
async def get_version(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """查询版本详情"""
    try:
        record = await ProductMgmtService.get_version_by_id(db, version_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="版本不存在")
        if record.create_user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限查看该版本")
        return VersionInfo.model_validate(record)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询版本失败: {str(e)}",
        )


@router.put("/versions/{version_id}", response_model=VersionInfo)
async def update_version(
    version_id: str,
    data: UpdateVersion,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """修改版本"""
    try:
        record = await ProductMgmtService.update_version(db, version_id, user_id, data)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="版本不存在")
        return VersionInfo.model_validate(record)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"修改版本失败: {str(e)}",
        )


@router.delete("/versions/{version_id}")
async def delete_version(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """删除版本"""
    try:
        success = await ProductMgmtService.delete_version(db, version_id, user_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="版本不存在")
        return {"message": "版本删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除版本失败: {str(e)}",
        )
