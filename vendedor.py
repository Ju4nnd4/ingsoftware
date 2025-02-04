import urwid

class VendedorView(urwid.WidgetWrap):
    def __init__(self, main):
        self.main = main
        self.cargar_inventario()
        self.mostrar_menu()

    def cargar_inventario(self):
        self.inventario = {}
        try:
            with open("inventario.txt", "r") as file:
                for linea in file:
                    verdura, precio, cantidad = linea.strip().split(": ")
                    self.inventario[verdura] = {
                        "precio": float(precio),
                        "cantidad": int(cantidad)
                    }
        except FileNotFoundError:
            self.inventario = {}

    def mostrar_menu(self):
        pile = urwid.Pile([
            urwid.Divider(),
            urwid.Text("Menú de Vendedor", align='center'),
            urwid.Divider(),
            urwid.Button("Ver inventario", on_press=self.ver_inventario),
            urwid.Divider(),
            urwid.Button("Salir", on_press=self.main.mostrar_login)
        ])
        self._w = urwid.Filler(pile, valign='top')

    def ver_inventario(self, button):
        contenido = "\n".join([
            f"{verdura}: Precio: {datos['precio']}, Cantidad: {datos['cantidad']}"
            for verdura, datos in self.inventario.items()
        ])
        self.mostrar_mensaje(f"Inventario:\n{contenido}")

    def mostrar_mensaje(self, mensaje):
        self.main.loop.widget = urwid.Overlay(
            urwid.LineBox(urwid.Text(f"\n{mensaje}\n", align='center')),
            self.main.loop.widget,
            align='center',
            width=30,
            height=5,
            valign='middle'  # Añadimos el argumento valign
        )
        self.mostrar_menu()