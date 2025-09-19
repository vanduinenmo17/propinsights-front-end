import anvil.email
import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.users
import anvil.secrets
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from datetime import datetime

@anvil.server.callable
def add_message(firstName, lastName, email, message):
  app_tables.contact_us.add_row(
    first_name=firstName,
    last_name=lastName,
    email=email, 
    message=message, 
    created=datetime.now()
  )

  # Send yourself an email each time a contact us message is submitted
  anvil.email.send(to="mvd@canvas-antler.com",
    subject=f"Message from {firstName} {lastName}",
    text=f"""
  A new person has filled out the Contact Us form!

  First Name: {firstName}
  Last Name; {lastName}
  Email address: {email}
  Message:
  {message}
  """)