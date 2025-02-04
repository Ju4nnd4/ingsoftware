import urwid

import urwid
from admin import AdminView
from vendedor import VendedorView
from domiciliario import DomiciliarioView

# Datos de cuentas válidas (simuladas)
cuentas_validas = [
    {"usuario": "admin", "contraseña": "123", "rol": "admin"},
    {"usuario": "vendedor", "contraseña": "456", "rol": "vendedor"},
    {"usuario": "domiciliario", "contraseña": "456", "rol": "domiciliario"}
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
        for cuenta in cuentas_validas:
            if cuenta["usuario"] == usuario and cuenta["contraseña"] == contraseña:
                self.main.mostrar_menu(cuenta["rol"])
                return
        
        self.error.set_text(('error', "Credenciales incorrectas. Intente nuevamente"))
        self.usuario.set_edit_text("")
        self.contraseña.set_edit_text("")

class MainApp:
    def __init__(self):
        self.login_view = LoginView(self)
        self.loop = urwid.MainLoop(
            self.login_view,
            palette,
            unhandled_input=lambda k: exit_program(None) if k in ('q', 'Q') else None
        )
        self.mostrar_login()

    def mostrar_login(self):
        self.loop.widget = self.login_view

    def mostrar_menu(self, rol):
        if rol == "admin":
            self.loop.widget = AdminView(self)
        elif rol == "vendedor":
            self.loop.widget = VendedorView(self)
        elif rol == "domiciliario":
            self.loop.widget = DomiciliarioView(self)

def exit_program(button):
    raise urwid.ExitMainLoop()

if __name__ == '__main__':
    app = MainApp()
    app.loop.run()

