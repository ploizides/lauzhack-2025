"""
Allow running backend as a module: python -m backend
"""

import uvicorn
import sys
from pathlib import Path

# Add the project root to the path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
