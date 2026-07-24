import os
from dotenv import load_dotenv

load_dotenv()

# ecom-backend owns writes to universal_events and reads experiments for the flag.
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://ecom_role:ecom_pw@localhost:5432/copilot"
)

# Superuser connection used only by migrations (creates roles + grants).
ADMIN_DATABASE_URL = os.getenv(
    "ADMIN_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/copilot"
)

PORT = int(os.getenv("PORT", "3002"))
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
EXPERIMENT_ID = os.getenv("EXPERIMENT_ID", "exp_1")
ECOM_WEB_URL = os.getenv("ECOM_WEB_URL", "http://localhost:5173")
SEED_PROFILE = os.getenv("SEED_PROFILE", "scale")
