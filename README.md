# reader 3

![reader3](reader3.png)

A lightweight, self-hosted EPUB reader with built-in AI chat. Upload EPUB books and read them alongside an LLM that has context of the current chapter.

## Features

- Upload EPUB files directly from the web interface
- Clean, distraction-free reading experience
- Built-in AI chat sidebar (uses BlackBox AI for Claude/GPT/Gemini access)
- Table of contents navigation
- Works locally or deployed to the cloud

## Local Usage

The project uses [uv](https://docs.astral.sh/uv/).

1. Create a `.env` file with your BlackBox AI API key:
   ```
   BLACKBOX_API_KEY=your-api-key-here
   ```

2. Run the server:
   ```bash
   uv run server.py
   ```

3. Visit [localhost:8123](http://localhost:8123/) and upload an EPUB!

You can also process EPUBs via CLI:
```bash
uv run reader3.py book.epub
```

## Deploy to Railway

1. Push this repo to GitHub

2. Create a new project on [railway.app](https://railway.app) and connect your repo

3. Add a **Volume** (for persistent book storage):
   - Click "+ New" → "Volume"
   - Mount path: `/data`

4. Set environment variables in Railway:
   ```
   BLACKBOX_API_KEY=your-api-key
   BOOKS_DIR=/data
   ```

5. Deploy! Railway will auto-build using the Dockerfile.

**Cost**: ~$0.25/month for storage, compute covered by $5 free credit.

## License

MIT
