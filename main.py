from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Static, Input, Button
from textual.reactive import reactive
from meme import meme, download

class pwdManager(App):
    css_path = "styles.css"
    msg = reactive("welcome to vaultic")
    meme_path = reactive("")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Static("vaultic", id="title")

        with Container():
            yield Static(self.msg, id="status", classes="box")
            yield Button("load a random meme", id="meme-btn", classes="buttons")
            yield Input(placeholder="enter the name of the service (eg: gmail)", id="service")
            yield Input(placeholder="enter your password", password=True, id="password")
            yield Button("store your password", id="store-btn", classes="buttons")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "meme-btn":
            meme_url = meme()
            
            if meme_url:
                self.meme_path = download(meme_url, "meme.jpg")
                self.msg = "loaded random meme!"
            else:
                self.msg = "failed to load random meme"
        
        elif event.button.id == "store-btn":
            if not self.meme_path:
                self.msg = "please load a random meme first!"
                return

            service = self.query_one("#service", Input).value
            password = self.query_one("#password", Input).value

            if not service or not password:
                self.msg = "please fill all the fields first!"
                return

            # steg logic here
            self.msg = "store the password"
    
    def watch_msg(self, new_value: str) -> None:
        try:
            status = self.get_widget_by_id("status")
            status.update(new_value)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    app = pwdManager()
    app.run()