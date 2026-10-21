import psycopg2

conn = psycopg2.connect(
   host="localhost",
   database="cb_booking_db",
   user="postgres",
   password="database@01",
   port="5432"
)