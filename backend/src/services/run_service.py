import json
import hashlib
from pathlib import Path
from sqlalchemy import select,func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from redis import Redis
from src.config.settings import REDIS_URL,ARTIFACTS_DIR
from src.models import AlignmentRun
from src.services.collection_service import get_collection
from src.services.template_service import get_template
from src.services.specimen_service import list_specimens
from src.services.deformation import analyze_alignment,snapshot_fingerprint
from src.constants.enums import RunStatus
redis=Redis.from_url(REDIS_URL)
ACTIVE_STATUSES=(RunStatus.QUEUED,RunStatus.RUNNING)
def list_runs(db):return db.scalars(select(AlignmentRun).order_by(AlignmentRun.id.desc())).all()
def get_run(db,id):
    r=db.get(AlignmentRun,id)
    if not r:raise HTTPException(404,'对齐研究不存在')
    return r

def build_snapshot(db,collection_id):
    """Freeze the current collection, template version and every current specimen."""
    c=get_collection(db,collection_id);t=get_template(db,c.template_id)
    return {'collection':{k:getattr(c,k) for k in ('id','code','name','protocol','source_file','template_id')},'template':{k:getattr(t,k) for k in ('id','code','name','labels','points','convention')},'specimens':[{k:getattr(s,k) for k in ('id','code','name','points','source_note')} for s in list_specimens(db,c.id)]}

def _ensure_active_capacity(db):
    if db.scalar(select(func.count()).select_from(AlignmentRun).where(AlignmentRun.status.in_(ACTIVE_STATUSES)))>=3:raise HTTPException(429,'已有3项活动任务，请等待')

def _enqueue(db,r):
    db.add(r);db.commit()
    try:redis.lpush('shapes:runs',str(r.id))
    except Exception:pass
    return r

def create_run(db,data):
    get_collection(db,data.collection_id)
    if db.scalar(select(AlignmentRun).where(AlignmentRun.name==data.name)):raise HTTPException(409,'研究名称重复')
    _ensure_active_capacity(db)
    r=AlignmentRun(**data.model_dump(),snapshot=build_snapshot(db,data.collection_id),status=RunStatus.QUEUED);return _enqueue(db,r)

def _unique_recalculation_name(db,source):
    base=f'{source.name} · 复算'
    if not db.scalar(select(AlignmentRun).where(AlignmentRun.name==base)):return base
    n=2
    while db.scalar(select(AlignmentRun).where(AlignmentRun.name==f'{base} {n}')):n+=1
    return f'{base} {n}'

def recalculation_key(source_run_id,snapshot,retained,tolerance):
    """Same source plus identical frozen inputs means the same recalculation."""
    material={'source_run_id':source_run_id,'retained':retained,'tolerance':tolerance,'snapshot':snapshot}
    return hashlib.sha256(json.dumps(material,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def create_recalculation(db,source_run_id,data):
    source=get_run(db,source_run_id)
    if source.status!=RunStatus.COMPLETED or not source.result:raise HTTPException(409,'只能从已完成的冻结研究发起复算')
    retained=data.retained if data.retained is not None else source.retained
    tolerance=data.tolerance if data.tolerance is not None else source.tolerance
    snapshot=build_snapshot(db,source.collection_id)
    key=recalculation_key(source.id,snapshot,retained,tolerance)
    existing=db.scalar(select(AlignmentRun).where(AlignmentRun.recalculation_key==key))
    if existing:return existing,True
    if data.name and db.scalar(select(AlignmentRun).where(AlignmentRun.name==data.name)):raise HTTPException(409,'研究名称重复')
    _ensure_active_capacity(db)
    r=AlignmentRun(name=data.name or _unique_recalculation_name(db,source),collection_id=source.collection_id,retained=retained,tolerance=tolerance,snapshot=snapshot,status=RunStatus.QUEUED,source_run_id=source.id,recalculation_key=key)
    try:return _enqueue(db,r),False
    except IntegrityError:
        # A concurrent identical request won the unique key; reuse its task.
        db.rollback();existing=db.scalar(select(AlignmentRun).where(AlignmentRun.recalculation_key==key))
        if existing:return existing,True
        raise

def provenance_chain(db,run):
    """All runs this recalculation descends from, nearest source first."""
    chain=[];current=run;seen={run.id}
    while current.source_run_id and current.source_run_id not in seen:
        parent=get_run(db,current.source_run_id)
        chain.append(parent);seen.add(parent.id);current=parent
    return chain

def compare_runs(db,run):
    """Differences between a recalculation and its immediate frozen source.

    Matching is by specimen code. A failed recalculation carries no metric rows,
    so the source result remains the only published one.
    """
    if not run.source_run_id:return None
    source=get_run(db,run.source_run_id)
    source_rows={s['code']:s for s in source.result.get('specimens',[])}
    current_rows={s['code']:s for s in run.snapshot.get('specimens',[])}
    result_rows={s['code']:s for s in run.result.get('specimens',[])} if run.status==RunStatus.COMPLETED else {}
    changed={code for code in set(source_rows)&set(current_rows) if source_rows[code].get('points')!=current_rows[code].get('points')}
    def metric(cur,key):return cur.get(key) if cur else None
    def delta(cur,prev,key):
        c,p=metric(cur,key),prev.get(key) if prev else None
        return c-p if c is not None and p is not None else None
    def row(code,prev,cur,status):
        known=current_rows.get(code) or source_rows.get(code) or {}
        out={'code':code,'name':known.get('name'),'status':status,'points_changed':code in changed}
        out.update(gpa_distance=metric(cur,'gpa_distance'),gpa_distance_previous=metric(prev,'gpa_distance'),gpa_distance_delta=delta(cur,prev,'gpa_distance'),residual=metric(cur,'residual'),residual_previous=metric(prev,'residual'),residual_delta=delta(cur,prev,'residual'))
        return out
    unchanged=[row(code,source_rows[code],result_rows.get(code),'matched') for code in sorted(set(current_rows)&set(source_rows))]
    added=[row(code,None,result_rows.get(code),'added') for code in sorted(set(current_rows)-set(source_rows))]
    removed=[row(code,source_rows[code],None,'removed') for code in sorted(set(source_rows)-set(current_rows))]
    labels_previous=list(source.snapshot.get('template',{}).get('labels',[]));labels_current=list(run.snapshot.get('template',{}).get('labels',[]))
    return {'source_run_id':source.id,'source_status':source.status,'result_available':bool(result_rows),'added':added,'removed':removed,'unchanged':unchanged,'label_order_changed':labels_previous!=labels_current,'labels_previous':labels_previous,'labels_current':labels_current,'template_changed':source.snapshot.get('template')!=run.snapshot.get('template'),'collection_changed':source.snapshot.get('collection')!=run.snapshot.get('collection'),'note':'同名裁片按code配对；新增/移除/标签顺序变化单独列出；失败复算不产生配准值，也不替换来源研究结果。'}

def run_page(db,id):
    r=get_run(db,id)
    return {'run':r,'comparison':compare_runs(db,r),'provenance':provenance_chain(db,r)}

def execute_run(db,id):
    r=get_run(db,id)
    if r.status not in ACTIVE_STATUSES:return
    r.status=RunStatus.RUNNING;db.commit()
    try:
        result=analyze_alignment(r.snapshot,r.retained,r.tolerance);Path(ARTIFACTS_DIR).mkdir(parents=True,exist_ok=True);Path(ARTIFACTS_DIR,f'run-{id}.json').write_text(json.dumps(result,ensure_ascii=False,allow_nan=False));r.result=result;r.status=RunStatus.COMPLETED;r.error='';db.commit()
    except Exception as exc:
        db.rollback();r=get_run(db,id);r.status=RunStatus.FAILED;r.error=str(exc)[:600];db.commit()
