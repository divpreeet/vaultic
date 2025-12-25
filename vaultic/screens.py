from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Input, Button, ListView, ListItem
from textual.screen import Screen
from cryptography.exceptions import InvalidTag
from .vault import Vault
from .meme import meme as meme_url, download
from pathlib import Path
from .vault import default
from rich_pixels import Pixels
from PIL import Image
import secrets 
import string
import pyperclip

class HomeScreen(Screen):
    def __init__(self) -> None:
        super().__init__()
        self.unlocked = False

    def compose(self):

        with Vertical(id="root"):
            with Horizontal(id="topbar"):
                yield Static("Vaultic", id="title")
                yield Static("Preview", id="meme-title")

            with Horizontal(id="layout"):
                with Container(id="panel"):
                    yield Static("enter your master password to continue", id="subtitle")
                    yield Input(placeholder="master password", password=True, id="master")

                    with Vertical(id="menu-buttons"):
                        yield Button("create vault meme", id="create-vault", classes="buttons")
                        yield Button("unlock", id="unlock", classes="buttons")
                        yield Button("store a password", id="go-store", classes="buttons", disabled=True)
                        yield Button("retrieve a password", id="go-get", classes="buttons", disabled=True)
                    
                    yield Static("", id="status", classes="box")
                
                with Container(id="meme"):
                    with Vertical(id="meme-vert"):
                        yield Static("", id="meme-view")
                        with Horizontal(id="meme-row"):
                            yield Button("open meme", id="preview", classes="buttons")
                    
                

    def on_mount(self):
        exists = default().vault_file.exists()
        self.query_one("#create-vault", Button).disabled = exists
        if exists:
            self.query_one("#status", Static).update("vault exists, enter your master password and click unlock")
        else:
            self.query_one("#status", Static).update("no vault meme found, create one!")
        self.update_preview()

    def center_square(self, img: Image.Image) -> Image.Image:
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        return img.crop((left, top, left + side, top + side))

    def update_preview(self):
        vault_path = default().vault_file
        meme_view = self.query_one("#meme-view", Static)

        if not vault_path.exists():
            meme_view.update("no vault meme yet, create one!")
            return
        
        try:
            w = max(10, meme_view.size.width)
            h = max(10, meme_view.size.height)            

            # margin so no clip
            w -= 1
            h -= 1

            side = max(10, min(w, h))

            img = Image.open(vault_path).convert("RGB")
            img = self.center_square(img)
            meme_view.update(Pixels.from_image(img, resize=(side, side)))
        except Exception as e:
            print(e)
            meme_view.update(str(e))

    def on_resize(self):
        self.update_preview()


    def _set_unlocked(self, unlocked: bool) -> None:
        self.unlocked = unlocked
        self.query_one("#go-store", Button).disabled = not unlocked
        self.query_one("#go-get", Button).disabled = not unlocked

    def on_button_pressed(self, event: Button.Pressed) -> None:
        master = self.query_one("#master", Input).value
        if not master:
            self.query_one("#status", Static).update("enter master password!")
            return

        if event.button.id == "preview":
            path = default().vault_file.resolve()
            self.app.open_url(f"file://{path}")
            self.query_one("#status", Static).update("opened preview")
            return

        if event.button.id == "create-vault":
            try:
                url = meme_url()
                if not url:
                    self.query_one("#status", Static).update("failed to fetch meme")
                    return

                cover_path = Path.home() / ".vaultic" / "cover.png"
                out = download(url, str(cover_path))
                if not out:
                    self.query_one("#status", Static).update("failed to download meme")
                    return

                v = Vault(master)
                v.create_meme(cover_path)
                self._set_unlocked(False)
                self.query_one("#status", Static).update("vault meme created at ~/.vaultic/vault.png")
                self.query_one("#create-vault", Button).disabled = True
                self.update_preview()
            except Exception as e:
                self.query_one("#status", Static).update(str(e))
            return

        if event.button.id == "unlock":
            try:
                v = Vault(master)
                v.verify_master()
                self._set_unlocked(True)
                self.query_one("#status", Static).update("unlocked")
            except FileNotFoundError:
                self._set_unlocked(False)
                self.query_one("#status", Static).update("no vault meme found. create it first")
            except InvalidTag:
                self._set_unlocked(False)
                self.query_one("#status", Static).update("wrong master password")
            except Exception as e:
                self._set_unlocked(False)
                self.query_one("#status", Static).update(str(e))
            return

        if not self.unlocked:
            self.query_one("#status", Static).update("unlock first")
            return

        if event.button.id == "go-store":
            self.app.push_screen(StoreScreen(master))
        elif event.button.id == "go-get":
            self.app.push_screen(GetScreen(master))


class StoreScreen(Screen):
    def __init__(self, master: str) -> None:
        super().__init__()
        self.master = master

    def compose(self):
        with Container(id="panel"):
            yield Static("store password", id="title")
            yield Input(placeholder="service (eg: gmail)", id="service")

            with Horizontal(id="row"):
                yield Input(value="16", placeholder="length", id="pw_len")
                yield Button("generate", id="generate", classes="buttons")

            with Horizontal(id="pw-row"):
                yield Input(placeholder="password", password=True, id="password")
                yield Button("copy", id="copy-store", classes="buttons")

            yield Button("save", id="save", classes="buttons")
            yield Button("back", id="back", classes="buttons")
            yield Static("", id="status", classes="box")

    def gen_pwd(self, length: int) -> str:
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{};:,.?/"
        length = max(8, min(length, 64))

        picks = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*()-_=+[]{};:,.?/"),
        ]
        for i in range(length - len(picks)):
            letter = secrets.choice(alphabet)
            picks.append(letter)
        secrets.SystemRandom().shuffle(picks)
        return "".join(picks)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return

        if event.button.id == "generate":
            raw = self.query_one("#pw_len", Input).value.strip()
            try:
                if raw:
                    length = int(raw)
                else:
                    length = 16
            except ValueError:
                self.query_one("#status", Static).update("length must be a number")
                return
            pw = self.gen_pwd(length)
            self.query_one("#password", Input).value = pw
            self.query_one("#status", Static).update(f"generated {len(pw)}-char password")
            
            return

        if event.button.id == "copy-store":
            pw=self.query_one("#password", Input).value
            if not pw:
                self.query_one("#status", Static).update("nothing to copy")
                return
            try:
                pyperclip.copy(pw)
                self.query_one("#status", Static).update("copied password to clipboard")
            except Exception as e:
                print(e)
            return

        if event.button.id == "save":
            service = self.query_one("#service", Input).value
            password = self.query_one("#password", Input).value

            if not service or not password:
                self.query_one("#status", Static).update("fill service + password")
                return

            try:
                v = Vault(self.master)
                v.add_entry(service, password)
                self.query_one("#status", Static).update(
                    f"stored password for {service.strip().lower()}"
                )
            except FileNotFoundError:
                self.query_one("#status", Static).update("create vault meme first")
            except InvalidTag:
                self.query_one("#status", Static).update("wrong master password")
            except Exception as e:
                self.query_one("#status", Static).update(f"error: {e}")


class GetScreen(Screen):
    def __init__(self, master: str) -> None:
        super().__init__()
        self.master = master
        self.sel_service: str | None = None

    def compose(self):
        with Container(id="panel"):
            yield Static("retrieve password", id="title")
            yield Static("saved services:", id="service_subtitle")
            yield ListView(id="services")

            with Vertical():
                yield Button("refresh list", id="refresh", classes="buttons")

            yield Static("confirm master password to reveal:", id="master_subtitle")
            yield Input(placeholder="master password", password=True, id="confirm")

            with Horizontal(id="reveal-row"):
                yield Button("reveal", id="reveal", classes="buttons")
                yield Button("copy", id="copy-get", classes="buttons")
                yield Button("update", id="update", classes="buttons")
                yield Button("delete", id="delete", classes="buttons")
            
                

            yield Input(placeholder="password will appear here", password=False, id="password_out")

            yield Button("back", id="back", classes="buttons")
            yield Static("", id="status", classes="box")
    
    def on_mount(self):
        self.refresh_services()

    def refresh_services(self) -> None:
        list_view = self.query_one("#services", ListView)
        list_view.clear()

        try:
            v = Vault(self.master)
            services = v.list_services()

            if not services:
                item = ListItem(Static("no saved services"))
                item.service = None
                list_view.append(item)
                self.query_one("#status", Static).update("no saved services")
                return

            for s in services:
                item = ListItem(Static(s))
                item.service = s
                list_view.append(item)

            self.query_one("#status", Static).update("select a service")
        except FileNotFoundError:
            self.query_one("#status", Static).update("create vault meme first")
        except InvalidTag:
            self.query_one("#status", Static).update("wrong master password (or vault modified)")
        except Exception as e:
            self.query_one("#status", Static).update(str(e))
    
    def on_resume(self):
        self.refresh_services()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.sel_service = getattr(event.item, "service", None)
        self.query_one("#password_out", Input).value = ""
        self.query_one("#status", Static).update(f"selected: {self.sel_service}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return

        if event.button.id == "refresh":
            self.refresh_services()
            return

        if event.button.id == "copy-get":
            pw = self.query_one("#password_out", Input).value 
            if not pw:
                self.query_one("#status", Static).update("nothing to copy (reveal first)")
                return
            try:
                pyperclip.copy(pw)
                self.query_one("#status", Static).update("copied to clipboard")
            except Exception as e:
                print(e)
            return

        if event.button.id == "reveal":
            if not self.sel_service:
                self.query_one("#status", Static).update("select a service first")
                return

            master_confirm = self.query_one("#confirm", Input).value
            if not master_confirm:
                self.query_one("#status", Static).update("enter master password to reveal")
                return

            try:
                v = Vault(master_confirm)
                entry = v.get_entry(self.sel_service)

                if not entry:
                    self.query_one("#status", Static).update("no entry found")
                    return

                self.query_one("#password_out", Input).value = entry["password"]
                self.query_one("#status", Static).update("revealed (will hide after 15 seconds)")
                self.set_timer(15, lambda: setattr(self.query_one("#password_out", Input), "value", ""))
                return

            except FileNotFoundError:
                self.query_one("#status", Static).update("create vault meme first")
            except InvalidTag:
                self.query_one("#status", Static).update("wrong master password")
            except Exception as e:
                self.query_one("#status", Static).update(f"error: {e}")

        if event.button.id == "delete":
            if not self.sel_service:
                self.query_one("#status", Static).update("please select a service to delete")

            master_confirm = self.query_one("#confirm", Input).value
            if not master_confirm:
                self.query_one("#status", Static).update("please enter the master password to delete the service")

            try:
                v = Vault(master_confirm)
                deleted = v.delete_entry(self.sel_service)
                deleted_name = self.sel_service
                if deleted:
                    self.sel_service = None
                    self.query_one("#status", Static).update(f"deleted password for {deleted_name}!")
                    self.query_one("#password_out", Input).value = ""
                    self.refresh_services()
                else:
                    self.query_one("#status", Static).update("service not found")
            except InvalidTag:
                self.query_one("#status", Static).update("wrong master password")
            except Exception as e:
                print(e)

        if event.button.id == "update":
            if not self.sel_service:
                self.query_one("#status", Static).update("select a service first")
                return
            self.app.push_screen(UpdateScreen(self.sel_service))
            return


class UpdateScreen(Screen):
    def __init__(self, service: str):
        super().__init__()
        self.service = service

    def compose(self):
        with Container(id="panel"):
            yield Static(f"update: {self.service}", id="title")

            yield Static("current password:", id="prev")
            current = Input(placeholder="(reveal to load)", id="current_pwd", disabled=True)
            yield current

            yield Static("new password:", id="new")
            yield Input(placeholder="enter new password", id="new_pwd", password=True)
           
            yield Static("confirm master password:", id="master_label")
            yield Input(placeholder="master password", id="confirm", password=True)

            with Horizontal(id="update-buttons"):
                yield Button("update", id="update", classes="buttons")
                yield Button("back", id="back", classes="buttons")
                yield Button("reveal", id="reveal", classes="buttons")
            
            yield Static("", id="status", classes="box")

    def on_mount(self):
        self.query_one("#current_pwd", Input).value = ""

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "reveal":
            master_confirm = self.query_one("#confirm", Input).value
            if not master_confirm:
                self.query_one("#status", Static).update("enter your master password first")
                return
            try:
                v = Vault(master_confirm)
                entry = v.get_entry(self.service)
                if not entry:
                    self.query_one("#status", Static).update("entry not found")
                    return
                self.query_one("#current_pwd", Input).value = entry["password"]
                self.query_one("#status", Static).update("current password revealed")
            except InvalidTag:
                self.query_one("#status", Static).update("wrong master password")
            except Exception as e:
                print(e)
            return

        if event.button.id == "back":
            self.app.pop_screen()
            return
            
        if event.button.id == "update":
            new_pw = self.query_one("#new_pwd", Input).value
            master_confirm = self.query_one("#confirm", Input).value

            if not new_pw:
                self.query_one("#status", Static).update("enter a new passsword")
                return
            if not master_confirm:
                self.query_one("#status", Static).update("enter your master password")
                return
            
            try:
                v = Vault(master_confirm)
                v.update_entry(self.service, new_pw)
                self.query_one("#status", Static).update(f"updated password for {self.service}")

                self.app.pop_screen()
            except InvalidTag:
                self.query_one("#status", Static).update("wrong master password")
            except Exception as e:
                print(e)