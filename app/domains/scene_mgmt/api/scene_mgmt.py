from typing import Optional
from fastapi import APIRouter,Depends,HTTPException,Query,status
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.domains.scene_mgmt.models.scene import SceneFlowType
from app.domains.scene_mgmt.schemes.scene_mgmt import CreateScene,CreateSceneFlow,SceneFlowInfo,SceneInfo,SceneTree,UpdateScene,UpdateSceneFlow
from app.domains.scene_mgmt.services.scene_mgmt import SceneMgmtService


router=APIRouter()


@router.get("/flow-types")
async def get_flow_types(user_id:str=Query(...,description="用户ID")):
    return {"types":SceneFlowType.values()}


@router.post("",response_model=SceneInfo)
async def create_scene(
    data:CreateScene,
    user_id:str=Query(...,description="用户ID"),
    db:AsyncSession=Depends(get_db),
):
    try:
        rec=await SceneMgmtService.create_scene(db,user_id,data)
        return SceneInfo.model_validate(rec)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"新增场景失败: {str(e)}")


@router.put("/{scene_id}",response_model=SceneInfo)
async def update_scene(
    scene_id:str,
    data:UpdateScene,
    user_id:str=Query(...,description="用户ID"),
    db:AsyncSession=Depends(get_db),
):
    try:
        rec=await SceneMgmtService.update_scene(db,scene_id,user_id,data)
        if not rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="场景不存在")
        return SceneInfo.model_validate(rec)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"更新场景失败: {str(e)}")


@router.delete("/{scene_id}")
async def delete_scene(
    scene_id:str,
    user_id:str=Query(...,description="用户ID"),
    db:AsyncSession=Depends(get_db),
):
    try:
        ok=await SceneMgmtService.delete_scene(db,scene_id,user_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="场景不存在")
        return {"message":"场景已删除"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"删除场景失败: {str(e)}")


@router.get("/versions/{version_id}",response_model=list[SceneInfo])
async def list_scenes(
    version_id:str,
    user_id:str=Query(...,description="用户ID"),
    parent_id:Optional[str]=Query(None,description="父场景ID，不传返回全部"),
    db:AsyncSession=Depends(get_db),
):
    try:
        recs=await SceneMgmtService.list_scenes(db,version_id,user_id,parent_id)
        return [SceneInfo.model_validate(r) for r in recs]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"获取场景列表失败: {str(e)}")


@router.get("/versions/{version_id}/tree",response_model=list[SceneTree])
async def list_scenes_tree(
    version_id:str,
    user_id:str=Query(...,description="用户ID"),
    db:AsyncSession=Depends(get_db),
):
    try:
        return await SceneMgmtService.get_scenes_tree(db,version_id,user_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"获取场景树失败: {str(e)}")


@router.get("/{scene_id}",response_model=SceneInfo)
async def get_scene(
    scene_id:str,
    user_id:str=Query(...,description="用户ID"),
    db:AsyncSession=Depends(get_db),
):
    try:
        rec=await SceneMgmtService.get_scene_by_id(db,scene_id)
        if not rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="场景不存在")
        return SceneInfo.model_validate(rec)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"获取场景失败: {str(e)}")


@router.post("/{scene_id}/flows",response_model=SceneFlowInfo)
async def create_scene_flow(
    scene_id:str,
    data:CreateSceneFlow,
    user_id:str=Query(...,description="用户ID"),
    db:AsyncSession=Depends(get_db),
):
    try:
        rec=await SceneMgmtService.create_flow(db,scene_id,user_id,data)
        if not rec:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="场景不存在或关联架构元素不合法")
        return await SceneMgmtService.to_flow_info(db,rec)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"新增场景流程失败: {str(e)}")


@router.put("/flows/{flow_id}",response_model=SceneFlowInfo)
async def update_scene_flow(
    flow_id:str,
    data:UpdateSceneFlow,
    user_id:str=Query(...,description="用户ID"),
    db:AsyncSession=Depends(get_db),
):
    try:
        rec=await SceneMgmtService.update_flow(db,flow_id,user_id,data)
        if not rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="场景流程不存在或关联架构元素不合法")
        return await SceneMgmtService.to_flow_info(db,rec)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"更新场景流程失败: {str(e)}")


@router.delete("/flows/{flow_id}")
async def delete_scene_flow(
    flow_id:str,
    user_id:str=Query(...,description="用户ID"),
    db:AsyncSession=Depends(get_db),
):
    try:
        ok=await SceneMgmtService.delete_flow(db,flow_id,user_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="场景流程不存在")
        return {"message":"场景流程已删除"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"删除场景流程失败: {str(e)}")


@router.get("/{scene_id}/flows",response_model=list[SceneFlowInfo])
async def list_scene_flows(
    scene_id:str,
    user_id:str=Query(...,description="用户ID"),
    flow_type:Optional[str]=Query(None,description="按流程类型过滤"),
    db:AsyncSession=Depends(get_db),
):
    try:
        flows=await SceneMgmtService.list_flows(db,scene_id,user_id,flow_type)
        return [await SceneMgmtService.to_flow_info(db,f) for f in flows]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"获取场景流程列表失败: {str(e)}")


@router.get("/flows/{flow_id}",response_model=SceneFlowInfo)
async def get_scene_flow(
    flow_id:str,
    user_id:str=Query(...,description="用户ID"),
    db:AsyncSession=Depends(get_db),
):
    try:
        rec=await SceneMgmtService.get_flow_by_id(db,flow_id)
        if not rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="场景流程不存在")
        return await SceneMgmtService.to_flow_info(db,rec)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"获取场景流程失败: {str(e)}")

