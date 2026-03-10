# reader3

A lightweight, self-hosted EPUB reader with a built-in AI chat sidebar. Upload EPUBs and read them alongside an LLM that has full context of the current chapter.

## Features

- **Web-based EPUB reader** -- upload `.epub` files and read them in a clean, distraction-free interface
- **AI chat sidebar** -- ask questions, get summaries, or discuss what you're reading with Claude, GPT, or Gemini (via [BlackBox AI](https://www.blackbox.ai/))
- **Table of contents** -- full TOC navigation with collapsible sidebar
- **Keyboard shortcuts** -- `Ctrl+K` to toggle chat, `Ctrl+B` to toggle sidebar
- **Self-hostable** -- run locally or deploy to Railway/Docker

## Quick Start

Requires [uv](https://docs.astral.sh/uv/) and Python 3.10+.

```bash
# Clone the repo
git clone https://github.com/Princeu3/reader3.git
cd reader3

# Create a .env file with your BlackBox AI API key
echo "BLACKBOX_API_KEY=your-api-key-here" > .env

# Run the server
uv run server.py
```

Open [localhost:8123](http://localhost:8123/) and upload an EPUB.

### CLI Mode

You can also process EPUBs without running the server:

```bash
uv run reader3.py book.epub
```

This creates a `book_data/` folder with the parsed book content.

## Deploy to Railway

1. Fork or push this repo to GitHub
2. Create a new project on [railway.app](https://railway.app) and connect your repo
3. Add a **Volume** mounted at `/data` (for persistent book storage)
4. Set environment variables:
   ```
   BLACKBOX_API_KEY=your-api-key
   BOOKS_DIR=/data
   ```
5. Deploy -- Railway auto-builds from the Dockerfile

## Docker

```bash
docker build -t reader3 .
docker run -p 8080:8080 -e BLACKBOX_API_KEY=your-key reader3
```

## Project Structure

```
reader3.py       # EPUB parser -- extracts content, TOC, images, metadata
server.py        # FastAPI web server -- library, reader, chat API, file upload
templates/
  library.html   # Book library / upload page
  reader.html    # Reader interface with TOC sidebar and AI chat panel
```

## How It Works

1. **Upload** an EPUB through the web UI (or process via CLI)
2. `reader3.py` parses the EPUB into structured data (chapters, TOC, images, metadata) and saves it as a pickle file
3. `server.py` serves the parsed book through a clean reading interface
4. The AI chat sidebar sends the current chapter text as context to the LLM, so it can answer questions about what you're reading

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `BLACKBOX_API_KEY` | *(required)* | API key from [BlackBox AI](https://www.blackbox.ai/) |
| `BOOKS_DIR` | `.` | Directory for stored book data (use `/data` on Railway) |
| `PORT` | `8123` | Server port |

## License

[MIT](LICENSE)
