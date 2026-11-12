from src.services import run_service as service
def index(db):return service.list_runs(db)
def create(db,data):return service.create_run(db,data)
def detail(db,id):return service.get_run(db,id)
def trace(db,id):return service.run_page(db,id)
def recalculate(db,id,data):return service.create_recalculation(db,id,data)
