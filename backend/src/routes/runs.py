from fastapi import APIRouter,Depends
from fastapi.responses import JSONResponse
from src.config.database import get_db
from src.utils.auth import current_user,editor
from src.schemas.run import RunInput,RunOut,RunPage,RecalculationInput
from src.controllers import run_controller as controller
router=APIRouter(prefix='/runs',tags=['runs'])
@router.get('',response_model=list[RunOut])
def index(db=Depends(get_db),user=Depends(current_user)):return controller.index(db)
@router.post('',response_model=RunOut,status_code=201)
def create(data:RunInput,db=Depends(get_db),user=Depends(editor)):return controller.create(db,data)
@router.get('/{id}',response_model=RunOut)
def detail(id:int,db=Depends(get_db),user=Depends(current_user)):return controller.detail(db,id)
@router.get('/{id}/trace',response_model=RunPage)
def trace(id:int,db=Depends(get_db),user=Depends(current_user)):return controller.trace(db,id)
@router.post('/{id}/recalculations',response_model=RunOut)
def recalculate(id:int,data:RecalculationInput|None=None,db=Depends(get_db),user=Depends(editor)):
    run,reused=controller.recalculate(db,id,data or RecalculationInput())
    return JSONResponse(status_code=200 if reused else 201,content=RunOut.model_validate(run).model_dump(mode='json'))
