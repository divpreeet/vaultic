# vaultic
vaultic is a terminal tool made in python, that is a password manager that stores your passwords in randomly fetched memes!

## what it does
- store, retrieve and manage password
- generate a strong password
- embed your passwords int a meme
- extract and get your password from the same image.

## how it works
i tried to keep this workflow pretty simple, first you make a vault, by entering a master password of your choice, then clicking the create vault meme and unlock button, then to store a serivce, you go on store and you enter or generate a password, the app then derives and encryption key and your password is then encrypted, and then vaultic encoded the encrypted bytes of your secret into the image's pixel data, and visually the image looks the same to the naked eye! note, the entire vault is stored in the meme, and both, the meme and master password are required to unlock your "vault", so the meme image stores multiple passwords and is the vault!

## install
```bash
python3 -m venv .venv
source .venv/bin/activate # on macos/linux
.\venv\Scripts\activate.ps1 # on windows
```

then just run!
```bash
vaultic
```

## security
- if you forget the master password, it **cannot** be recovered. and the vault needs to be reset by going into ```~/.vaultic/``` and deleting the contents

## development
```bash
git clone https://github.com/divpreeet/vaultic.git
cd vaultic
python3 -m venv .venv
source .venv/bin/activate # macos, linux
.\venv\Scripts\activate.ps1 # windows
pip install -e .
vaultic
```
