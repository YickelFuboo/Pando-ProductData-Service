from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.domains.arch_mgmt.models.deployment import (
    ArchDeploymentUnitType,
)
from app.domains.arch_mgmt.schemes.deployment import (
    ArchDeploymentUnitCreate,
    ArchDeploymentUnitUpdate,
    ArchDeploymentUnitInfo,
    ArchArtifactToDeploymentCreate,
    ArchArtifactToDeploymentUpdate,
    ArchArtifactToDeploymentInfo,
)
from app.domains.arch_mgmt.services import DeploymentService

router = APIRouter()


@router.get("/deployment-unit-types")
async def get_deployment_unit_types(user_id: str = Query(..., description="用户ID")):
    """获取部署单元类型（cluster/node/namespace/pod/container 等）"""
    return {"types": ArchDeploymentUnitType.values()}


# ==================== DeploymentUnit ====================

@router.post("/deployment-units", response_model=ArchDeploymentUnitInfo)
async def create_deployment_unit(
    data: ArchDeploymentUnitCreate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """新增部署单元"""
    try:
        unit = await DeploymentService.create_deployment_unit(db, data, user_id)
        return ArchDeploymentUnitInfo.model_validate(unit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"新增部署单元失败: {str(e)}",
        )


@router.put("/deployment-units/{unit_id}", response_model=ArchDeploymentUnitInfo)
async def update_deployment_unit(
    unit_id: str,
    data: ArchDeploymentUnitUpdate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """更新部署单元"""
    try:
        unit = await DeploymentService.update_deployment_unit(db, unit_id, data)
        if not unit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部署单元不存在")
        return ArchDeploymentUnitInfo.model_validate(unit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新部署单元失败: {str(e)}",
        )


@router.delete("/deployment-units/{unit_id}")
async def delete_deployment_unit(
    unit_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """删除部署单元"""
    try:
        success = await DeploymentService.delete_deployment_unit(db, unit_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部署单元不存在")
        return {"message": "部署单元已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除部署单元失败: {str(e)}",
        )


@router.get("/versions/{version_id}/deployment-units", response_model=list[ArchDeploymentUnitInfo])
async def list_deployment_units(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    unit_type: Optional[str] = Query(None, description="按单元类型过滤"),
    parent_unit_id: Optional[str] = Query(None, description="按父单元ID过滤"),
    db: AsyncSession = Depends(get_db),
):
    """获取版本的部署单元列表"""
    try:
        units = await DeploymentService.list_deployment_units(db, version_id, unit_type, parent_unit_id)
        return [ArchDeploymentUnitInfo.model_validate(u) for u in units]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取部署单元列表失败: {str(e)}",
        )


@router.get("/deployment-units/{unit_id}", response_model=ArchDeploymentUnitInfo)
async def get_deployment_unit(
    unit_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取部署单元详情"""
    try:
        unit = await DeploymentService.get_deployment_unit_by_id(db, unit_id)
        if not unit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部署单元不存在")
        return ArchDeploymentUnitInfo.model_validate(unit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取部署单元失败: {str(e)}",
        )


# ==================== ArtifactToDeployment ====================

@router.post("/artifact-to-deployments", response_model=ArchArtifactToDeploymentInfo)
async def create_artifact_to_deployment(
    data: ArchArtifactToDeploymentCreate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """新增构建产物-部署单元映射"""
    try:
        artifact_deploy = await DeploymentService.create_artifact_to_deployment(db, data)
        if not artifact_deploy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="构建产物或部署单元不存在或不属于同一版本",
            )
        return ArchArtifactToDeploymentInfo.model_validate(artifact_deploy)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"新增构建产物-部署单元映射失败: {str(e)}",
        )


@router.put("/artifact-to-deployments/{artifact_deploy_id}", response_model=ArchArtifactToDeploymentInfo)
async def update_artifact_to_deployment(
    artifact_deploy_id: str,
    data: ArchArtifactToDeploymentUpdate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """更新构建产物-部署单元映射"""
    try:
        artifact_deploy = await DeploymentService.update_artifact_to_deployment(db, artifact_deploy_id, data)
        if not artifact_deploy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="构建产物-部署单元映射不存在")
        return ArchArtifactToDeploymentInfo.model_validate(artifact_deploy)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新构建产物-部署单元映射失败: {str(e)}",
        )


@router.delete("/artifact-to-deployments/{artifact_deploy_id}")
async def delete_artifact_to_deployment(
    artifact_deploy_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """删除构建产物-部署单元映射"""
    try:
        success = await DeploymentService.delete_artifact_to_deployment(db, artifact_deploy_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="构建产物-部署单元映射不存在")
        return {"message": "构建产物-部署单元映射已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除构建产物-部署单元映射失败: {str(e)}",
        )


@router.get("/versions/{version_id}/artifact-to-deployments", response_model=list[ArchArtifactToDeploymentInfo])
async def list_artifact_to_deployments(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    build_artifact_id: Optional[str] = Query(None, description="按构建产物ID过滤"),
    deployment_unit_id: Optional[str] = Query(None, description="按部署单元ID过滤"),
    db: AsyncSession = Depends(get_db),
):
    """获取版本的构建产物-部署单元映射列表"""
    try:
        mappings = await DeploymentService.list_artifact_to_deployments(db, version_id, build_artifact_id, deployment_unit_id)
        return [ArchArtifactToDeploymentInfo.model_validate(m) for m in mappings]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取构建产物-部署单元映射列表失败: {str(e)}",
        )
