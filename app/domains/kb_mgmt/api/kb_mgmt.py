from fastapi import APIRouter,Depends,HTTPException,Query,status
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.domains.kb_mgmt.schemes.kb_mgmt import CreateVersionKb,UpdateVersionKb,VersionKbInfo,VersionKbListResponse
from app.domains.kb_mgmt.services.kb_mgmt_service import KbMgmtService


router=APIRouter()


@router.get("/categories")
async def get_categories():
    """获取知识库分类枚举（业务知识、方案知识、编码知识、测试知识、问题案例知识）"""
    return {"categories":await KbMgmtService.list_categories()}


@router.get("/versions/{version_id}",response_model=VersionKbListResponse)
async def list_version_kbs(
    version_id:str,
    user_id:str=Query(...,description="用户ID"),
    db:AsyncSession=Depends(get_db),
):
    """获取某版本下按分类分组的知识库列表"""
    try:
        return await KbMgmtService.list_by_version(db,version_id)
    except ValueError as e:
        if "版本不存在" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))


@router.post("/versions/{version_id}/items",response_model=VersionKbInfo)
async def add_kb_to_version(
    version_id:str,
    data:CreateVersionKb,
    user_id:str=Query(...,description="用户ID"),
    db:AsyncSession=Depends(get_db),
):
    """将知识库绑定到版本并归属到某分类"""
    try:
        rec=await KbMgmtService.add_kb_to_version(db,version_id,data)
        if not rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="版本不存在")
        return KbMgmtService._to_info(rec)
    except ValueError as e:
        if "重复绑定" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))


@router.put("/versions/{version_id}/items/{item_id}",response_model=VersionKbInfo)
async def update_version_kb(
    version_id:str,
    item_id:str,
    data:UpdateVersionKb,
    user_id:str=Query(...,description="用户ID"),
    db:AsyncSession=Depends(get_db),
):
    """修改版本下某条知识库绑定的分类"""
    try:
        rec=await KbMgmtService.update_version_kb(db,version_id,item_id,data)
        if not rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="绑定记录不存在")
        return KbMgmtService._to_info(rec)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))


@router.delete("/versions/{version_id}/items/{item_id}")
async def remove_kb_from_version(
    version_id:str,
    item_id:str,
    user_id:str=Query(...,description="用户ID"),
    db:AsyncSession=Depends(get_db),
):
    """解除版本与知识库的绑定"""
    ok=await KbMgmtService.remove_kb_from_version(db,version_id,item_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="绑定记录不存在")
    return {"message":"已解除绑定"}


@router.get("/versions/{version_id}/items/{item_id}",response_model=VersionKbInfo)
async def get_version_kb_item(
    version_id:str,
    item_id:str,
    user_id:str=Query(...,description="用户ID"),
    db:AsyncSession=Depends(get_db),
):
    """获取版本下某条知识库绑定详情"""
    rec=await KbMgmtService.get_by_id(db,version_id,item_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="绑定记录不存在")
    return KbMgmtService._to_info(rec)
