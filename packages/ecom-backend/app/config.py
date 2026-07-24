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
