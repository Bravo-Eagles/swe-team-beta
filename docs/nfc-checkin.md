# NFC Tag Check-in

## What this is

Typical attendance software tries to use a QR code or link to have students prove they were present. The problem with this is that anyone in class can that link to a friend who isn't there and then the friend can mark themselves present.

Our solution is an NFC tag that the teacher can deploy. Each time a student taps it their phone, the tag create a brand new link that only works once. Forwarding it doesn't matter because by the time the friend opens it, the link has already been used.

Students don't need an app. Any NFC-capable phone opens the link in the browser automatically.

## How a tap works

Think of the tag as a ticket machine with a secret stamp:

1. **A numbered ticket.** The tag keeps a tap counter that goes up by one on
   every tap and can never go backwards.
2. **A sealed envelope.** The tag encrypts its own ID and the counter using a
   secret key, so nobody can read or change them.
3. **A stamp.** The tag signs the link with the same secret key. Only a tag
   that knows the key can make a valid signature.
4. **Our server checks it.** It opens the envelope, checks the stamp, and
   makes sure the ticket number is higher than the last one it saw.

The secret key is stored on the tag and on our server. It never appears in
the link.

We use **NXP NTAG 424 DNA** tags as they allow for dynamic URL utilization, meaning it creates a new signed link on every tap

## What the link looks like

```
https://<our app>/checkin?picc_data=5E5C236A25FA38D76D74724DC7C9893A&cmac=B76B3E5157143117
```

- `picc_data` (32 hex characters): the encrypted tag ID and tap counter
- `cmac` (16 hex characters): the signature

Both values are completely different on every tap.

## How we verify a tap (`src/nfc.py`)

`verify_tap(picc_data_hex, cmac_hex, key)` returns `(uid, counter)` for a
genuine link and raises `ValueError` if non-genuine. This is all done in 4 steps

| Step | What it does | What it catches |
|---|---|---|
| 1. Check the size | Converts the hex to bytes and checks the lengths | Made-up or edited links |
| 2. Decrypt | Opens `picc_data` with our key (AES) | — |
| 3. Check the format | The first byte must be `0xC7`, then reads the tag ID and counter | Links from a tag with a different key |
| 4. Check the signature | Rebuilds the signature with our key and compares (CMAC) | Real links with anything changed |

What it does **not** check: whether the link was already used. That needs to
remember the last counter for each tag, so it happens in the database code.

### Try it

With the factory key (all zeros), this real tap from our test tag should
verify:

```bash
uv run python -c "
from src.nfc import verify_tap
print(verify_tap('5E5C236A25FA38D76D74724DC7C9893A', 'B76B3E5157143117', bytes(16)))
"
```

Expected output: `('0461205abd2390', 1)` (tag ID, tap counter 1).

Change the last character of the second value to `8`, and it raises
`ValueError: signature does not match`.

## Setting up a tag

Done once per tag, from an iPhone, with the **NFC.cool Tools** app

1. Open **NFC Tools → Advanced → NTAG 424 DNA** and hold the phone to the tag.
   It should show **Originality: Genuine NXP**.
2. **Write URL:** enter the check-in link. For testing we use the demo server:
   `https://sdm.nfcdeveloper.com/tag?picc_data=00000000000000000000000000000000&cmac=0000000000000000`
3. **Enable SUN Verification:**
   - Protection: **Encrypted (UID private)**
   - Meta-read key: **Key 0**
   - File-read key: **Key 0**
   - Tap **Enable SUN** and hold the phone to the tag.
4. Check that the screen shows **SUN Authenticity: Authentic**.
5. Test: lock the app away, tap the tag with the phone, and open the link.
   The demo site should say **Cryptographic signature validated** with the
   tag's ID and counter.

⚠️ **Never change these settings.** They are permanent and can ruin the tag:
**LRP mode**, **Random UID**, and any file permission set to **Never**.

> **Planned:** Tag setup will move to a script that uses a USB NFC reader.
> The person setting up a tag will place it on the reader and run one
> command, which configures the tag and registers it for a class
> automatically. No phone app app needed.