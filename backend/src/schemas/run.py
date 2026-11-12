from pydantic import BaseModel,Field,ConfigDict
from datetime import datetime
class RunInput(BaseModel):
    name:str=Field(min_length=2,max_length=140)
    collection_id:int
    retained:int=Field(default=3,ge=1,le=5,strict=True)
    tolerance:float=Field(default=1e-12,ge=1e-14,le=1e-6,allow_inf_nan=False,strict=True)
class RecalculationInput(BaseModel):
    """Optional request fields; omitted values inherit the frozen source run."""
    name:str|None=Field(default=None,min_length=2,max_length=140)
    retained:int|None=Field(default=None,ge=1,le=5,strict=True)
    tolerance:float|None=Field(default=None,ge=1e-14,le=1e-6,allow_inf_nan=False,strict=True)
class ComparisonSpecimen(BaseModel):
    code:str
    name:str|None=None
    status:str
    points_changed:bool=False
    gpa_distance:float|None=None
    gpa_distance_previous:float|None=None
    gpa_distance_delta:float|None=None
    residual:float|None=None
    residual_previous:float|None=None
    residual_delta:float|None=None
class RunComparison(BaseModel):
    source_run_id:int
    source_status:str
    result_available:bool
    added:list[ComparisonSpecimen]
    removed:list[ComparisonSpecimen]
    unchanged:list[ComparisonSpecimen]
    label_order_changed:bool
    labels_previous:list[str]
    labels_current:list[str]
    template_changed:bool
    collection_changed:bool
    note:str
class RunOut(RunInput):
    id:int
    status:str
    snapshot:dict
    result:dict
    error:str
    source_run_id:int|None=None
    recalculation_key:str|None=None
    created_at:datetime
    model_config=ConfigDict(from_attributes=True)
class RunPage(BaseModel):
    """Run detail plus comparison and provenance chain."""
    run:RunOut
    comparison:RunComparison|None=None
    provenance:list[RunOut]=[]
