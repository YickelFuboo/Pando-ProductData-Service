from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.domains.git_auth_mgmt.schemes.git_auth_mgmt import (
    GitAuthResponse,
    GitAuthListResponse,
    GitAuthProvider,
)
from app.domains.git_auth_mgmt.services.git_auth_mgmt_service import GitAuthMgmtService

router = APIRouter()


@router.post("/{provider}", response_model=GitAuthResponse)
async def save_git_auth(
    provider: str,
    user_id: str,
    access_token: str,
    version_id: Optional[str] = Query(None, description="版本ID，不传则配置该 provider 的默认鉴权"),
    db: AsyncSession = Depends(get_db),
):
    """保存/更新指定类型 Git 仓的鉴权信息，可按 version_id 区分不同版本"""
    try:
        if provider not in GitAuthProvider.values():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"provider 不合法 {provider}, 合法值为: {GitAuthProvider.values()}",
            )
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="access_token 不能为空",
            )
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id 不能为空",
            )
        git_auth = await GitAuthMgmtService.save_git_auth(
            db, user_id, provider, access_token, version_id
        )
        return GitAuthResponse.model_validate(git_auth)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存 {provider} 鉴权信息失败: {str(e)}",
        )


@router.delete("/{provider}")
async def delete_git_auth(
    provider: str,
    user_id: str,
    version_id: Optional[str] = Query(None, description="版本ID，不传则删除该 provider 的默认鉴权"),
    db: AsyncSession = Depends(get_db),
):
    """删除指定类型 Git 仓的鉴权信息"""
    try:
        success = await GitAuthMgmtService.delete_git_auth(db, user_id, provider, version_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到 {provider} 对应鉴权(version_id={version_id})",
            )
        return {"message": f"成功删除 {provider} 鉴权信息"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除 {provider} 鉴权信息失败: {str(e)}",
        )


@router.get("/", response_model=GitAuthListResponse)
async def get_user_git_auths(
    user_id: str,
    version_id: Optional[str] = Query(None, description="版本ID，不传则返回该用户所有鉴权（含默认与各版本）"),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的 Git 鉴权列表，可按 version_id 过滤"""
    try:
        items = await GitAuthMgmtService.get_user_git_auths(db, user_id, version_id)
        return GitAuthListResponse(
            items=[GitAuthResponse.model_validate(i) for i in items],
            total=len(items),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取 Git 鉴权信息失败: {str(e)}",
        )
