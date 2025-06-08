import sys
import asyncio
from sqlalchemy import text
from db import get_connection

async def clear_table(table_name: str):
    query = text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
    
    async with get_connection() as session:
        await session.execute(query)
        await session.commit()

    return {"message": f"Table '{table_name}' has been cleared."}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python delete_table.py <table_name>")
        sys.exit(1)

    table = sys.argv[1]
    asyncio.run(clear_table(table))
