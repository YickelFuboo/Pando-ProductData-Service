from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.domains.arch_mgmt.models.architecture import (
    ArchOverviewSectionKey,
    ArchElementType,
    ArchDependencyType,
)
from app.domains.arch_mgmt.schemes.architecture import (
    ArchOverviewCreate,
    ArchOverviewUpdate,
    ArchOverviewInfo,
    ArchElementCreate,
    ArchElementUpdate,
    ArchElementInfo,
    ArchElementTree,
    ArchDependencyCreate,
    ArchDependencyUpdate,
    ArchDependencyInfo,
)
from app.domains.arch_mgmt.services import ArchitectureService


router = APIRouter()


@router.get("/overview-section-keys")
async def get_overview_section_keys(user_id: str = Query(..., description="用户ID")):
    """获取标准架构说明节键（Arc42 风格）；也支持自定义 key"""
    return {"section_keys": ArchOverviewSectionKey.ordered_values()}


@router.get("/element-types")
async def get_element_types(user_id: str = Query(..., description="用户ID")):
    """获取支持的架构元素类型（C4/Arc42）"""
    return {"types": ArchElementType.values()}


@router.get("/dependency-types")
async def get_dependency_types(user_id: str = Query(..., description="用户ID")):
    """获取建议的依赖关系类型"""
    return {"types": ArchDependencyType.values()}


# ==================== Overview ====================

@router.post("/overview", response_model=ArchOverviewInfo)
async def create_overview(
    data: ArchOverviewCreate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """新增某版本的指定节架构说明（section_key 默认 main，可传 Arc42 节键）"""
    try:
        overview = await ArchitectureService.create_overview(db, data, user_id)
        return ArchOverviewInfo.model_validate(overview)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建架构概览失败: {str(e)}",
        )


@router.put("/versions/{version_id}/overview", response_model=ArchOverviewInfo)
async def update_overview(
    version_id: str,
    data: ArchOverviewUpdate,
    user_id: str = Query(..., description="用户ID"),
    section_key: str = Query("main", description="节键"),
    db: AsyncSession = Depends(get_db),
):
    """更新某版本指定节的架构说明"""
    try:
        overview = await ArchitectureService.update_overview(db, version_id, section_key, data)
        if not overview:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该版本下未找到该节架构说明")
        return ArchOverviewInfo.model_validate(overview)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新架构概览失败: {str(e)}",
        )


@router.get("/versions/{version_id}/overviews", response_model=list[ArchOverviewInfo])
async def list_overviews(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取某版本下所有架构说明节"""
    try:
        overviews = await ArchitectureService.list_overviews(db, version_id)
        return [ArchOverviewInfo.model_validate(o) for o in overviews]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取架构概览列表失败: {str(e)}",
        )


@router.get("/versions/{version_id}/overview", response_model=Optional[ArchOverviewInfo])
async def get_overview(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    section_key: str = Query("main", description="节键，如 main 或 context_and_scope"),
    db: AsyncSession = Depends(get_db),
):
    """获取某版本指定节的架构说明"""
    try:
        overview = await ArchitectureService.get_overview(db, version_id, section_key)
        return ArchOverviewInfo.model_validate(overview) if overview else None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取架构概览失败: {str(e)}",
        )


# ==================== Element ====================

@router.post("/elements", response_model=ArchElementInfo)
async def create_element(
    data: ArchElementCreate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """新增架构元素（C4/Arc42 构建块）"""
    try:
        if data.element_type not in ArchElementType.values():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"element_type 不合法，合法值: {ArchElementType.values()}",
            )
        elem = await ArchitectureService.create_element(db, data, user_id)
        return ArchElementInfo.model_validate(elem)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"新增架构元素失败: {str(e)}",
        )


@router.put("/elements/{element_id}", response_model=ArchElementInfo)
async def update_element(
    element_id: str,
    data: ArchElementUpdate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """更新架构元素"""
    try:
        elem = await ArchitectureService.update_element(db, element_id, data)
        if not elem:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="架构元素不存在")
        return ArchElementInfo.model_validate(elem)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新架构元素失败: {str(e)}",
        )


@router.delete("/elements/{element_id}")
async def delete_element(
    element_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """删除架构元素"""
    try:
        success = await ArchitectureService.delete_element(db, element_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="架构元素不存在")
        return {"message": "架构元素已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除架构元素失败: {str(e)}",
        )


@router.get("/versions/{version_id}/elements", response_model=list[ArchElementInfo])
async def list_elements(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    parent_id: Optional[str] = Query(None, description="父元素ID，不传则返回全部"),
    element_type: Optional[str] = Query(None, description="按类型过滤"),
    db: AsyncSession = Depends(get_db),
):
    """获取版本的架构元素列表"""
    try:
        elements = await ArchitectureService.get_elements(db, version_id, parent_id, element_type)
        return [ArchElementInfo.model_validate(e) for e in elements]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取架构元素列表失败: {str(e)}",
        )


@router.get("/versions/{version_id}/elements/tree", response_model=list[ArchElementTree])
async def list_elements_tree(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取版本的架构元素树（层级结构）"""
    try:
        tree = await ArchitectureService.get_elements_tree(db, version_id)
        return tree
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取架构元素树失败: {str(e)}",
        )


@router.get("/elements/{element_id}", response_model=ArchElementInfo)
async def get_element(
    element_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取单个架构元素详情"""
    try:
        elem = await ArchitectureService.get_element_by_id(db, element_id)
        if not elem:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="架构元素不存在")
        return ArchElementInfo.model_validate(elem)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取架构元素失败: {str(e)}",
        )


# ==================== Dependency ====================

@router.post("/dependencies", response_model=ArchDependencyInfo)
async def create_dependency(
    data: ArchDependencyCreate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """新增架构依赖关系（element → element）"""
    try:
        dep = await ArchitectureService.create_dependency(db, data, user_id)
        if not dep:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="源元素或目标元素不存在或不属于同一版本",
            )
        return ArchDependencyInfo.model_validate(dep)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"新增架构依赖失败: {str(e)}",
        )


@router.put("/dependencies/{dependency_id}", response_model=ArchDependencyInfo)
async def update_dependency(
    dependency_id: str,
    data: ArchDependencyUpdate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """更新架构依赖"""
    try:
        dep = await ArchitectureService.update_dependency(db, dependency_id, data)
        if not dep:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="架构依赖不存在")
        return ArchDependencyInfo.model_validate(dep)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新架构依赖失败: {str(e)}",
        )


@router.delete("/dependencies/{dependency_id}")
async def delete_dependency(
    dependency_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """删除架构依赖"""
    try:
        success = await ArchitectureService.delete_dependency(db, dependency_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="架构依赖不存在")
        return {"message": "架构依赖已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除架构依赖失败: {str(e)}",
        )


@router.get("/versions/{version_id}/dependencies", response_model=list[ArchDependencyInfo])
async def list_dependencies(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取版本的架构依赖列表"""
    try:
        deps = await ArchitectureService.get_dependencies(db, version_id)
        return [ArchDependencyInfo.model_validate(d) for d in deps]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取架构依赖列表失败: {str(e)}",
        )


