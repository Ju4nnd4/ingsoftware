import urwid

# Datos de cuentas válidas (simuladas)
cuentas_validas = [
    {"usuario": "admin", "contraseña": "123"},
    {"usuario": "user", "contraseña": "456"}
]

# Paleta de colores
palette = [
    ('header', 'white', 'dark blue'),
    ('body', 'light gray', 'black'),
    ('button', 'black', 'light gray'),
    ('error', 'white', 'dark red')
]

class LoginView(urwid.WidgetWrap):
    def __init__(self, main):
        self.main = main
        self.usuario = urwid.Edit("Usuario: ")
        self.contraseña = urwid.Edit("Contraseña: ", mask='*')
        self.error = urwid.Text("", align='center')
        
        pile = urwid.Pile([
            urwid.Divider(),
            urwid.Text("Login", align='center'),
            urwid.Divider(),
            self.usuario,
            self.contraseña,
            urwid.Divider(),
            urwid.Button("Ingresar", on_press=self.verificar_login),
            urwid.Divider(),
            self.error
        ])
        
        super().__init__(urwid.Filler(pile, valign='top'))

    def verificar_login(self, button):
        usuario = self.usuario.edit_text
        contraseña = self.contraseña.edit_text
        
        # Verificar credenciales
        if any(c["usuario"] == usuario and c["contraseña"] == contraseña for c in cuentas_validas):
            self.main.mostrar_menu()
        else:
            self.error.set_text(('error', "Credenciales incorrectas. Intente nuevamente"))
            self.usuario.set_edit_text("")
            self.contraseña.set_edit_text("")

class MenuView(urwid.WidgetWrap):
    def __init__(self, main):
        self.main = main
        pile = urwid.Pile([
            urwid.Divider(),
            urwid.Text("Menú Principal", align='center'),
            urwid.Divider(),
            urwid.Button("Opción 1", on_press=lambda x: self.mensaje("Opción 1")),
            urwid.Button("Opción 2", on_press=lambda x: self.mensaje("Opción 2")),
            urwid.Button("Opción 3", on_press=lambda x: self.mensaje("Opción 3")),
            urwid.Divider(),
            urwid.Button("Salir", on_press=exit_program)
        ])
        super().__init__(urwid.Filler(pile, valign='top'))

    def mensaje(self, texto):
        self.main.loop.widget = urwid.Overlay(
            urwid.LineBox(urwid.Text(f"\n{texto} seleccionada\n", align='center')),
            self.main.loop.widget,
            align='center',
            width=30,
            height=5
        )

class MainApp:
    def __init__(self):
        self.login_view = LoginView(self)
        self.menu_view = MenuView(self)
        self.loop = urwid.MainLoop(
            self.login_view,
            palette,
            unhandled_input=lambda k: exit_program(None) if k in ('q', 'Q') else None
        )
        self.mostrar_login()

    def mostrar_login(self):
        self.loop.widget = self.login_view

    def mostrar_menu(self):
        self.loop.widget = self.menu_view

def exit_program(button):
    raise urwid.ExitMainLoop()

if __name__ == '__main__':
    app = MainApp()
    app.loop.run()