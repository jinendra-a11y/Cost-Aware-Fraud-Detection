from ninja import NinjaAPI
from jobs.api import router as jobs_router

api = NinjaAPI(title="Expense Approval System")

# Mount your apps
api.add_router("/jobs/", jobs_router)