from textual.containers import Container, Vertical
from textual.widgets import Static, Input, Button, ListView, ListItem
from textual.screen import Screen
from cryptography.exceptions import InvalidTag
from vault import Vault

class HomeScreen(Screen):
    def compose(self):
        with Container(id="panel"):
            yield Static("Vaultic", id="title")
            yield Static("enter your master password to continue", id="subtitle")
            yield Input(placeholder="master password", password=True, id="master")
            
            with Vertical(id="menu-buttons"):
                yield Button("store a password", id="go-store", classes="buttons")
                yield Button("retrieve a password", id="go-get", classes="buttons")

            yield Static("", id="status", classes="box")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        master = self.query_one("#master", Input).value
        if not master:
            self.query_one("#status", Static).update("enter master password!")
            return
        try:
            v = Vault(master)
            v.verify_master()
        except InvalidTag:
            self.query_one("#status", Static).update("wrong master password")
            return
        except Exception as e:
            self.query_one("#status", Static).update(str(e))
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
            yield Input(placeholder="password", password=True, id="password")
            yield Button("save", id="save", classes="buttons")
            yield Button("back", id="back", classes="buttons")
            yield Static("", id="status", classes="box")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
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
            except InvalidTag:
                self.query_one("#status", Static).update(
                    "wrong master password"
                )
            except Exception as e:
                self.query_one("#status", Static).update("error")
                print(e)



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

            yield Button("reveal", id="reveal", classes="buttons")
            yield Input(
                placeholder="password will appear here", password=False, id="password_out")

            yield Button("back", id="back", classes="buttons")
            yield Static("", id="status", classes="box")

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
        except InvalidTag:
            self.query_one("#status", Static).update("wrong master password (or vault modified)")
        except Exception as e:
            self.query_one("#status", Static).update(str(e))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.sel_service = getattr(event.item, "service", None)
        self.query_one("#status", Static).update(f"selected: {self.sel_service}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return

        if event.button.id == "refresh":
            self.refresh_services()
            return

        if event.button.id == "reveal":
            if not self.sel_service or self.sel_service.startswith("—"):
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
                self.query_one("#status", Static).update("revealed")
            except InvalidTag:
                self.query_one("#status", Static).update("wrong master password")
            except Exception as e:
                self.query_one("#status", Static).update(f"error: {e}")
        


