from textual.app import App
from textual.widgets import Header, Footer
from screens import HomeScreen

class Vaultic(App):
    CSS_PATH = "styles.tcss"
    def compose(self):
        yield Header(show_clock=True)
        yield Footer()
        
    def on_mount(self) -> None:
        self.push_screen(HomeScreen())

if __name__ == "__main__":
    Vaultic().run()
