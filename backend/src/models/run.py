from datetime import datetime
from sqlalchemy import String,ForeignKey,UniqueConstraint,DateTime,JSON,Double
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class AlignmentRun(Base):
    __tablename__='alignment_runs'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(140),unique=True)
    collection_id:Mapped[int]=mapped_column(ForeignKey('shape_collections.id'))
    retained:Mapped[int]=mapped_column(default=3)
    tolerance:Mapped[float]=mapped_column(Double,default=1e-12)
    status:Mapped[str]=mapped_column(String(20),default='queued')
    snapshot:Mapped[dict]=mapped_column(JSON,default=dict)
    result:Mapped[dict]=mapped_column(JSON,default=dict)
    error:Mapped[str]=mapped_column(String(600),default='')
    source_run_id:Mapped[int|None]=mapped_column(ForeignKey('alignment_runs.id'),nullable=True,index=True)
    recalculation_key:Mapped[str|None]=mapped_column(String(64),unique=True,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
