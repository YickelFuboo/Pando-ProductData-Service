from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.domains.arch_mgmt.models.interfaces import (
    ArchInterfaceCategory,
    ArchPhysicalInterfaceType,
    ArchElementInterfaceRelationType,
)
from app.domains.arch_mgmt.schemes.interfaces import (
    ArchInterfaceCreate,
    ArchInterfaceUpdate,
    ArchInterfaceInfo,
    ArchElementInterfaceCreate,
    ArchElementInterfaceUpdate,
    ArchElementInterfaceInfo,
)
from app.domains.arch_mgmt.services import InterfacesService

router = APIRouter()


@router.get("/interface-categories")
async def get_interface_categories(user_id: str = Query(..., description="用户ID")):
    """获取接口类别（logical/physical）"""
    return {"categories": ArchInterfaceCategory.values()}


@router.get("/physical-interface-types")
async def get_physical_interface_types(user_id: str = Query(..., description="用户ID")):
    """获取物理接口类型（rest_api/grpc/message_queue 等）"""
    return {"types": ArchPhysicalInterfaceType.values()}


@router.get("/element-interface-relation-types")
async def get_element_interface_relation_types(user_id: str = Query(..., description="用户ID")):
    """获取元素-接口关系类型（provides/uses）"""
    return {"types": ArchElementInterfaceRelationType.values()}


# ==================== Interface ====================

@router.post("/interfaces", response_model=ArchInterfaceInfo)
async def create_interface(
    data: ArchInterfaceCreate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """新增接口（逻辑接口或物理接口）"""
    try:
        interface = await InterfacesService.create_interface(db, data, user_id)
        if not interface:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="父接口不存在或不属于同一版本，或字段验证失败",
            )
        return ArchInterfaceInfo.model_validate(interface)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"新增接口失败: {str(e)}",
        )


@router.put("/interfaces/{interface_id}", response_model=ArchInterfaceInfo)
async def update_interface(
    interface_id: str,
    data: ArchInterfaceUpdate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """更新接口"""
    try:
        interface = await InterfacesService.update_interface(db, interface_id, data)
        if not interface:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="接口不存在")
        return ArchInterfaceInfo.model_validate(interface)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新接口失败: {str(e)}",
        )


@router.delete("/interfaces/{interface_id}")
async def delete_interface(
    interface_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """删除接口"""
    try:
        success = await InterfacesService.delete_interface(db, interface_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="接口不存在")
        return {"message": "接口已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除接口失败: {str(e)}",
        )


@router.get("/versions/{version_id}/interfaces", response_model=list[ArchInterfaceInfo])
async def list_interfaces(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    interface_category: Optional[str] = Query(None, description="按接口类别过滤（logical/physical）"),
    interface_type: Optional[str] = Query(None, description="按物理接口类型过滤"),
    parent_id: Optional[str] = Query(None, description="按父接口ID过滤"),
    db: AsyncSession = Depends(get_db),
):
    """获取版本的接口列表"""
    try:
        interfaces = await InterfacesService.list_interfaces(db, version_id, interface_category, interface_type, parent_id)
        return [ArchInterfaceInfo.model_validate(i) for i in interfaces]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取接口列表失败: {str(e)}",
        )


@router.get("/interfaces/{interface_id}", response_model=ArchInterfaceInfo)
async def get_interface(
    interface_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取接口详情"""
    try:
        interface = await InterfacesService.get_interface_by_id(db, interface_id)
        if not interface:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="接口不存在")
        return ArchInterfaceInfo.model_validate(interface)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取接口失败: {str(e)}",
        )


# ==================== ElementInterface ====================

@router.post("/element-interfaces", response_model=ArchElementInterfaceInfo)
async def create_element_interface(
    data: ArchElementInterfaceCreate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """新增元素-接口关系（提供/使用）"""
    try:
        elem_iface = await InterfacesService.create_element_interface(db, data)
        if not elem_iface:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="元素或接口不存在或不属于同一版本",
            )
        return ArchElementInterfaceInfo.model_validate(elem_iface)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"新增元素-接口关系失败: {str(e)}",
        )


@router.put("/element-interfaces/{elem_iface_id}", response_model=ArchElementInterfaceInfo)
async def update_element_interface(
    elem_iface_id: str,
    data: ArchElementInterfaceUpdate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """更新元素-接口关系"""
    try:
        elem_iface = await InterfacesService.update_element_interface(db, elem_iface_id, data)
        if not elem_iface:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="元素-接口关系不存在")
        return ArchElementInterfaceInfo.model_validate(elem_iface)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新元素-接口关系失败: {str(e)}",
        )


@router.delete("/element-interfaces/{elem_iface_id}")
async def delete_element_interface(
    elem_iface_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """删除元素-接口关系"""
    try:
        success = await InterfacesService.delete_element_interface(db, elem_iface_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="元素-接口关系不存在")
        return {"message": "元素-接口关系已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除元素-接口关系失败: {str(e)}",
        )


@router.get("/versions/{version_id}/element-interfaces", response_model=list[ArchElementInterfaceInfo])
async def list_element_interfaces(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    element_id: Optional[str] = Query(None, description="按元素ID过滤"),
    interface_id: Optional[str] = Query(None, description="按接口ID过滤"),
    relation_type: Optional[str] = Query(None, description="按关系类型过滤"),
    db: AsyncSession = Depends(get_db),
):
    """获取版本的元素-接口关系列表"""
    try:
        relations = await InterfacesService.list_element_interfaces(db, version_id, element_id, interface_id, relation_type)
        return [ArchElementInterfaceInfo.model_validate(r) for r in relations]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取元素-接口关系列表失败: {str(e)}",
        )
