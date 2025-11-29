import os
import pickle
import tempfile
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
import httpx

load_dotenv()
from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from reader3 import Book, BookMetadata, ChapterContent, TOCEntry, process_epub, save_to_pickle

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Where are the book folders located? Use /data on Railway with volume
BOOKS_DIR = os.getenv("BOOKS_DIR", ".")

# BlackBox AI API key from environment
BLACKBOX_API_KEY = os.getenv("BLACKBOX_API_KEY", "")

@lru_cache(maxsize=10)
def load_book_cached(folder_name: str) -> Optional[Book]:
    """
    Loads the book from the pickle file.
    Cached so we don't re-read the disk on every click.
    """
    file_path = os.path.join(BOOKS_DIR, folder_name, "book.pkl")
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "rb") as f:
            book = pickle.load(f)
        return book
    except Exception as e:
        print(f"Error loading book {folder_name}: {e}")
        return None

@app.get("/", response_class=HTMLResponse)
async def library_view(request: Request):
    """Lists all available processed books."""
    books = []

    # Scan directory for folders ending in '_data' that have a book.pkl
    if os.path.exists(BOOKS_DIR):
        for item in os.listdir(BOOKS_DIR):
            full_path = os.path.join(BOOKS_DIR, item)
            if item.endswith("_data") and os.path.isdir(full_path):
                # Try to load it to get the title
                book = load_book_cached(item)
                if book:
                    books.append({
                        "id": item,
                        "title": book.metadata.title,
                        "author": ", ".join(book.metadata.authors),
                        "chapters": len(book.spine)
                    })

    return templates.TemplateResponse("library.html", {"request": request, "books": books})

@app.get("/read/{book_id}", response_class=HTMLResponse)
async def redirect_to_first_chapter(book_id: str):
    """Helper to just go to chapter 0."""
    return await read_chapter(book_id=book_id, chapter_index=0)

@app.get("/read/{book_id}/{chapter_index}", response_class=HTMLResponse)
async def read_chapter(request: Request, book_id: str, chapter_index: int):
    """The main reader interface."""
    book = load_book_cached(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if chapter_index < 0 or chapter_index >= len(book.spine):
        raise HTTPException(status_code=404, detail="Chapter not found")

    current_chapter = book.spine[chapter_index]

    # Calculate Prev/Next links
    prev_idx = chapter_index - 1 if chapter_index > 0 else None
    next_idx = chapter_index + 1 if chapter_index < len(book.spine) - 1 else None

    return templates.TemplateResponse("reader.html", {
        "request": request,
        "book": book,
        "current_chapter": current_chapter,
        "chapter_index": chapter_index,
        "book_id": book_id,
        "prev_idx": prev_idx,
        "next_idx": next_idx
    })

@app.get("/read/{book_id}/images/{image_name}")
async def serve_image(book_id: str, image_name: str):
    """
    Serves images specifically for a book.
    The HTML contains <img src="images/pic.jpg">.
    The browser resolves this to /read/{book_id}/images/pic.jpg.
    """
    # Security check: ensure book_id is clean
    safe_book_id = os.path.basename(book_id)
    safe_image_name = os.path.basename(image_name)

    img_path = os.path.join(BOOKS_DIR, safe_book_id, "images", safe_image_name)

    if not os.path.exists(img_path):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(img_path)

@app.post("/api/chat")
async def chat(request: Request):
    """Send chat request to BlackBox AI API and return complete response."""
    if not BLACKBOX_API_KEY:
        return {"error": "BLACKBOX_API_KEY not configured"}

    data = await request.json()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.blackbox.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {BLACKBOX_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": data.get("model", "blackboxai/anthropic/claude-sonnet-4.5"),
                "messages": data["messages"],
                "stream": False
            },
            timeout=120.0
        )

    result = response.json()

    # Extract the response content
    try:
        content = result["choices"][0]["message"]["content"]
        return {"response": content}
    except (KeyError, IndexError):
        return {"error": "Invalid response from API", "details": result}


@app.post("/api/upload")
async def upload_epub(file: UploadFile = File(...)):
    """Handle EPUB file upload and processing."""
    if not file.filename.endswith('.epub'):
        return JSONResponse(
            status_code=400,
            content={"error": "Only .epub files are allowed"}
        )

    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Generate output directory name from book title
        base_name = os.path.splitext(file.filename)[0]
        output_dir = os.path.join(BOOKS_DIR, f"{base_name}_data")

        # Process the EPUB
        book_obj = process_epub(tmp_path, output_dir)
        save_to_pickle(book_obj, output_dir)

        # Cleanup temp file
        os.unlink(tmp_path)

        # Clear the LRU cache so new book appears
        load_book_cached.cache_clear()

        return JSONResponse(content={
            "success": True,
            "title": book_obj.metadata.title,
            "id": f"{base_name}_data"
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8123))
    print(f"Starting server at http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
