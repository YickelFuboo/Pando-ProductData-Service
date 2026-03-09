from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.domains.arch_mgmt.models.build import (
    ArchBuildArtifactType,
)
from app.domains.arch_mgmt.schemes.build import (
    ArchBuildArtifactCreate,
    ArchBuildArtifactUpdate,
    ArchBuildArtifactInfo,
    ArchBuildArtifactTree,
    ArchElementToArtifactCreate,
    ArchElementToArtifactUpdate,
    ArchElementToArtifactInfo,
    ArchArtifactToArtifactCreate,
    ArchArtifactToArtifactUpdate,
    ArchArtifactToArtifactInfo,
)
from app.domains.arch_mgmt.services import BuildService

router = APIRouter()


@router.get("/build-artifact-types")
async def get_build_artifact_types(user_id: str = Query(..., description="用户ID")):
    """获取构建产物类型（jar/war/docker_image/binary 等）"""
    return {"types": ArchBuildArtifactType.values()}


# ==================== BuildArtifact ====================

@router.post("/build-artifacts", response_model=ArchBuildArtifactInfo)
async def create_build_artifact(
    data: ArchBuildArtifactCreate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """新增构建产物"""
    try:
        artifact = await BuildService.create_build_artifact(db, data, user_id)
        return ArchBuildArtifactInfo.model_validate(artifact)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"新增构建产物失败: {str(e)}",
        )


@router.put("/build-artifacts/{artifact_id}", response_model=ArchBuildArtifactInfo)
async def update_build_artifact(
    artifact_id: str,
    data: ArchBuildArtifactUpdate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """更新构建产物"""
    try:
        artifact = await BuildService.update_build_artifact(db, artifact_id, data)
        if not artifact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="构建产物不存在")
        return ArchBuildArtifactInfo.model_validate(artifact)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新构建产物失败: {str(e)}",
        )


@router.delete("/build-artifacts/{artifact_id}")
async def delete_build_artifact(
    artifact_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """删除构建产物"""
    try:
        success = await BuildService.delete_build_artifact(db, artifact_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="构建产物不存在")
        return {"message": "构建产物已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除构建产物失败: {str(e)}",
        )


@router.get("/versions/{version_id}/build-artifacts", response_model=list[ArchBuildArtifactInfo])
async def list_build_artifacts(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    artifact_type: Optional[str] = Query(None, description="按产物类型过滤"),
    db: AsyncSession = Depends(get_db),
):
    """获取版本的构建产物列表"""
    try:
        artifacts = await BuildService.list_build_artifacts(db, version_id, artifact_type)
        return [ArchBuildArtifactInfo.model_validate(a) for a in artifacts]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取构建产物列表失败: {str(e)}",
        )


@router.get("/versions/{version_id}/build-artifacts/tree", response_model=list[ArchBuildArtifactTree])
async def list_build_artifacts_tree(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取版本的构建产物树结构（父节点是产物，子节点是输入）"""
    try:
        tree = await BuildService.get_build_artifacts_tree(db, version_id)
        return tree
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取构建产物树失败: {str(e)}",
        )


@router.get("/build-artifacts/{artifact_id}", response_model=ArchBuildArtifactInfo)
async def get_build_artifact(
    artifact_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取构建产物详情"""
    try:
        artifact = await BuildService.get_build_artifact_by_id(db, artifact_id)
        if not artifact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="构建产物不存在")
        return ArchBuildArtifactInfo.model_validate(artifact)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取构建产物失败: {str(e)}",
        )


# ==================== ElementToArtifact ====================

@router.post("/element-to-artifacts", response_model=ArchElementToArtifactInfo)
async def create_element_to_artifact(
    data: ArchElementToArtifactCreate,
    db: AsyncSession = Depends(get_db),
):
    """新增架构元素-构建产物映射"""
    try:
        element_artifact = await BuildService.create_element_to_artifact(db, data)
        if not element_artifact:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="架构元素或构建产物不存在或不属于同一版本",
            )
        return ArchElementToArtifactInfo.model_validate(element_artifact)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"新增架构元素-构建产物映射失败: {str(e)}",
        )


@router.put("/element-to-artifacts/{element_artifact_id}", response_model=ArchElementToArtifactInfo)
async def update_element_to_artifact(
    element_artifact_id: str,
    data: ArchElementToArtifactUpdate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """更新架构元素-构建产物映射"""
    try:
        element_artifact = await BuildService.update_element_to_artifact(db, element_artifact_id, data)
        if not element_artifact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="架构元素-构建产物映射不存在")
        return ArchElementToArtifactInfo.model_validate(element_artifact)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新架构元素-构建产物映射失败: {str(e)}",
        )


@router.delete("/element-to-artifacts/{element_artifact_id}")
async def delete_element_to_artifact(
    element_artifact_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """删除架构元素-构建产物映射"""
    try:
        success = await BuildService.delete_element_to_artifact(db, element_artifact_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="架构元素-构建产物映射不存在")
        return {"message": "架构元素-构建产物映射已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除架构元素-构建产物映射失败: {str(e)}",
        )


@router.get("/versions/{version_id}/element-to-artifacts", response_model=list[ArchElementToArtifactInfo])
async def list_element_to_artifacts(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    element_id: Optional[str] = Query(None, description="按架构元素ID过滤"),
    build_artifact_id: Optional[str] = Query(None, description="按构建产物ID过滤"),
    db: AsyncSession = Depends(get_db),
):
    """获取版本的架构元素-构建产物映射列表"""
    try:
        mappings = await BuildService.list_element_to_artifacts(db, version_id, element_id, build_artifact_id)
        return [ArchElementToArtifactInfo.model_validate(m) for m in mappings]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取架构元素-构建产物映射列表失败: {str(e)}",
        )


# ==================== ArtifactToArtifact ====================

@router.post("/artifact-to-artifacts", response_model=ArchArtifactToArtifactInfo)
async def create_artifact_to_artifact(
    data: ArchArtifactToArtifactCreate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """新增构建产物关系（多个输入产物构建成一个输出产物）"""
    try:
        artifact_to_artifact = await BuildService.create_artifact_to_artifact(db, data)
        if not artifact_to_artifact:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="输入或目标构建产物不存在或不属于同一版本",
            )
        return ArchArtifactToArtifactInfo.model_validate(artifact_to_artifact)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"新增构建产物关系失败: {str(e)}",
        )


@router.put("/artifact-to-artifacts/{artifact_to_artifact_id}", response_model=ArchArtifactToArtifactInfo)
async def update_artifact_to_artifact(
    artifact_to_artifact_id: str,
    data: ArchArtifactToArtifactUpdate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """更新构建产物关系"""
    try:
        artifact_to_artifact = await BuildService.update_artifact_to_artifact(db, artifact_to_artifact_id, data)
        if not artifact_to_artifact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="构建产物关系不存在")
        return ArchArtifactToArtifactInfo.model_validate(artifact_to_artifact)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新构建产物关系失败: {str(e)}",
        )


@router.delete("/artifact-to-artifacts/{artifact_to_artifact_id}")
async def delete_artifact_to_artifact(
    artifact_to_artifact_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """删除构建产物关系"""
    try:
        success = await BuildService.delete_artifact_to_artifact(db, artifact_to_artifact_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="构建产物关系不存在")
        return {"message": "构建产物关系已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除构建产物关系失败: {str(e)}",
        )


@router.get("/versions/{version_id}/artifact-to-artifacts", response_model=list[ArchArtifactToArtifactInfo])
async def list_artifact_to_artifacts(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    input_artifact_id: Optional[str] = Query(None, description="按输入构建产物ID过滤"),
    target_artifact_id: Optional[str] = Query(None, description="按目标构建产物ID过滤"),
    db: AsyncSession = Depends(get_db),
):
    """获取版本的构建产物关系列表"""
    try:
        relations = await BuildService.list_artifact_to_artifacts(db, version_id, input_artifact_id, target_artifact_id)
        return [ArchArtifactToArtifactInfo.model_validate(r) for r in relations]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取构建产物关系列表失败: {str(e)}",
        )
