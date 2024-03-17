from FINALCODE import app
from beaker import localnet, client

app.build().export("./artifacts")

accounts = localnet.kmd.get_accounts()
sender = accounts[0]

app_client = client.ApplicationClient(
    client = localnet.get_algod_client(),
    app = app,
    sender = sender.address,
    signer = sender.signer,
)

app_client.create()

return_value = app_client.call(app.read_state).return_value
print(f"The default state is:  {return_value}")