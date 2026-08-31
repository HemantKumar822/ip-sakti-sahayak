import asyncio
import json
import os
import sys

# Add the project root to sys.path so we can import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

# Load env before other imports to ensure config gets the right values
load_dotenv()

from src.api.routes import process_query
from src.models.request import QueryRequest


async def test_live() -> None:
    # A standard query that should hit the database and generate an answer
    req = QueryRequest(
        query_text="What is the process for applying for a patent in India under the Patents Act?",
        session_id="test-live-session",
    )

    print(
        f"Testing live API query with model: {os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')}..."
    )
    try:
        response = await process_query(req)
        print("\n--- RESPONSE ---")
        print(json.dumps(response.model_dump(), indent=2))
    except Exception as e:  # noqa: BLE001
        print(f"Error during live query: {e}")


if __name__ == "__main__":
    asyncio.run(test_live())
