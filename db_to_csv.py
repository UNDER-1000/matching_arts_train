import sys
import csv
import json
import asyncio
from sqlalchemy import text
from db import get_connection

async def export_table_to_csv(table_name: str):
    output_file = f"data/{table_name}.csv"
    query = text(f"SELECT * FROM {table_name}")

    async with get_connection() as session:
        result = await session.execute(query)
        rows = result.fetchall()

        if not rows:
            print(f"No data found in table '{table_name}'.")
            return

        # Write to CSV
        with open(output_file, mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(result.keys())  # Header
            keys = list(result.keys())
            for row in rows:
                row = list(row)
                if 'interactions' in keys:
                    i = keys.index('interactions')
                    row[i] = json.dumps(row[i])
                writer.writerow(row)

        print(f"✅ Exported {len(rows)} rows from '{table_name}' to '{output_file}'.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python db_to_csv.py <table_name>")
        sys.exit(1)

    table = sys.argv[1]
    asyncio.run(export_table_to_csv(table))
