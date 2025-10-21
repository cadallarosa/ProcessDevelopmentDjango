#!/usr/bin/env python
"""Clear the akta_node_ids table"""
import pymysql

try:
    # Connect to database
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='cdallarosa',
        password='$ystImmun3!2022',
        database='djangoP1_db'
    )

    cursor = conn.cursor()

    # Clear table
    print("Clearing akta_node_ids table...")
    cursor.execute("TRUNCATE TABLE akta_node_ids")
    conn.commit()

    # Verify
    cursor.execute("SELECT COUNT(*) FROM akta_node_ids")
    count = cursor.fetchone()[0]
    print(f"✅ Table cleared. Remaining records: {count}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
