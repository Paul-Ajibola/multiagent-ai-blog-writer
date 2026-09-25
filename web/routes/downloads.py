from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from web.config import OUTPUTS_DIR

router = APIRouter()


@router.get("/api/runs/{run_id}/download")
def download_markdown(run_id: str):
    safe_run_id = "".join(
        character for character in run_id if character.isalnum() or character in {"-", "_"}
    )

    if safe_run_id != run_id:
        raise HTTPException(status_code=400, detail="Invalid run ID.")

    output_file = OUTPUTS_DIR / safe_run_id / "blog.md"

    if not output_file.is_file():
        raise HTTPException(status_code=404, detail="Generated Markdown file was not found.")

    return FileResponse(
        path=output_file,
        media_type="text/markdown",
        filename=f"generated-blog-{safe_run_id[:8]}.md",
    )