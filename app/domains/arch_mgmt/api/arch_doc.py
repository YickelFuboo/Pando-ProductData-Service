from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.domains.arch_mgmt.services.arch_doc_service import ArchDocService

router = APIRouter()


@router.get("/versions/{version_id}/doc", response_class=PlainTextResponse)
async def get_version_arch_doc(
    version_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """根据当前架构元素生成该版本的完整架构设计 Markdown 文档"""
    try:
        content = await ArchDocService.build_arch_doc(db, version_id)
        return content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成架构文档失败: {str(e)}",
        )
