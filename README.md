# wichteln

A modern web application for organizing secret santa style gift exchanges. Built with FastAPI and modern tooling.

## Features

- **Create Gift Exchanges**: Set up named exchanges with descriptions
- **Participant Management**: Add participants with email addresses
- **Smart Matching**: Automatic gift matching with constraint support
- **Unique Codes**: Each participant gets a unique code to look up their recipient
- **Email Integration**: Optional email delivery of codes (with fallback to console output)
- **Clean Web Interface**: Simple, responsive HTML interface

## Quick Start

1. **Install dependencies** (requires Python 3.10+):
   ```bash
   uv sync
   ```

2. **Run the application**:
   ```bash
   uv run uvicorn wichteln.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Open your browser** to `http://localhost:8000`

## How It Works

1. **Create an Exchange**: Start by creating a new secret santa exchange with a name and description
2. **Add Participants**: Add participants using the format `Name <email@example.com>` (one per line)
3. **Generate Matches**: The system automatically creates matches ensuring no one gets themselves
4. **Distribute Codes**: Participants receive unique codes via email (or printed to console if email not configured)
5. **Lookup Recipients**: Participants use their codes to find out who they're buying gifts for

## Email Configuration

To enable email delivery of codes, set these environment variables:

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

For Gmail:
1. Enable 2-factor authentication
2. Generate an "App Password" 
3. Use the app password as `SENDER_PASSWORD`

If email is not configured, codes will be printed to the console instead.

## Development

The project uses modern Python tooling:
- **uv** for dependency management
- **FastAPI** for the web framework
- **SQLAlchemy** for database operations
- **SQLite** for data storage (configurable)

To run tests:
```bash
uv run pytest
```

## Database

The application uses SQLite by default. To use a different database, set the `DATABASE_URL` environment variable:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
```

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: Server-rendered HTML with CSS
- **Deployment**: Can be deployed anywhere Python runs
- **Dependencies**: Managed with uv

## License

MIT