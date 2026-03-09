from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.domains.arch_mgmt.models.decision import ArchDecisionStatus
from app.domains.arch_mgmt.schemes.decision import (
    ArchDecisionCreate,
    ArchDecisionUpdate,
    ArchDecisionInfo,
)
from app.domains.arch_mgmt.services import DecisionService

router = APIRouter()


@router.get("/decision-statuses")
async def get_decision_statuses(user_id: str = Query(..., description="用户ID")):
    """获取 ADR 状态枚举"""
    return {"statuses": ArchDecisionStatus.values()}


@router.post("/decisions", response_model=ArchDecisionInfo)
async def create_decision(
    data: ArchDecisionCreate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """新增架构决策记录（ADR）"""
    try:
        if data.status and data.status not in ArchDecisionStatus.values():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"status 不合法，合法值: {ArchDecisionStatus.values()}",
            )
        rec = await DecisionService.create_decision(db, data, user_id)
        return ArchDecisionInfo.model_validate(rec)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"新增架构决策失败: {str(e)}",
        )


@router.put("/decisions/{decision_id}", response_model=ArchDecisionInfo)
async def update_decision(
    decision_id: str,
    data: ArchDecisionUpdate,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """更新架构决策"""
    try:
        rec = await DecisionService.update_decision(db, decision_id, data)
        if not rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="架构决策不存在")
        return ArchDecisionInfo.model_validate(rec)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新架构决策失败: {str(e)}",
        )


@router.delete("/decisions/{decision_id}")
async def delete_decision(
    decision_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """删除架构决策"""
    try:
        success = await DecisionService.delete_decision(db, decision_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="架构决策不存在")
        return {"message": "架构决策已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除架构决策失败: {str(e)}",
        )


@router.get("/versions/{version_id}/decisions", response_model=list[ArchDecisionInfo])
async def list_decisions(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取版本的架构决策列表（ADR）"""
    try:
        recs = await DecisionService.list_decisions(db, version_id)
        return [ArchDecisionInfo.model_validate(r) for r in recs]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取架构决策列表失败: {str(e)}",
        )


@router.get("/decisions/{decision_id}", response_model=ArchDecisionInfo)
async def get_decision(
    decision_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取单条架构决策详情"""
    try:
        rec = await DecisionService.get_decision_by_id(db, decision_id)
        if not rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="架构决策不存在")
        return ArchDecisionInfo.model_validate(rec)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取架构决策失败: {str(e)}",
        )
