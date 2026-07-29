# import psycopg2

# conn = psycopg2.connect("postgresql://chemisto:chemisto_pass@localhost:5432/chemisto_db")
# cur = conn.cursor()
# cur.execute("SELECT slug, name FROM sites")
# print("sites:", cur.fetchall())
# cur.execute("SELECT count(*) FROM products WHERE site_id IS NOT NULL")
# print("products with site_id:", cur.fetchone())
# cur.execute("SELECT count(*) FROM users WHERE site_id IS NOT NULL")
# print("users with site_id:", cur.fetchone())

import psycopg2

conn = psycopg2.connect("postgresql://chemisto:chemisto_pass@localhost:5432/chemisto_db")
cur = conn.cursor()
cur.execute("""
    SELECT p.name, p.is_active, s.slug
    FROM products p
    JOIN sites s ON p.site_id = s.id
    WHERE p.name ILIKE '%fries%' OR p.name ILIKE '%loaded%'
""")
for row in cur.fetchall():
    print(row)