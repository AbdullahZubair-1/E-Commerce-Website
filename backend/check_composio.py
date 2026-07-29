from composio import Composio

# Paste your real Composio API key here (from the dashboard's API Keys section)
API_KEY = "ak_zL65SJ9POOBEFjTQOUKG"

client = Composio(api_key=API_KEY)
accounts = client.connected_accounts.list(toolkit_slugs=["googlesheets"])

for account in accounts.items:
    print("Connection name:", getattr(account, "name", None))
    print("Connected account ID:", account.id)
    print("User ID:", getattr(account, "user_id", None))
    print("Status:", account.status)
    print("---")