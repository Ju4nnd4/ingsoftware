import urwid

class AdminView(urwid.WidgetWrap):
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

    def guardar_inventario(self):
        with open("inventario.txt", "w") as file:
            for verdura, datos in self.inventario.items():
                file.write(f"{verdura}: {datos['precio']}: {datos['cantidad']}\n")

    def mostrar_menu(self, *args):
        pile = urwid.Pile([
            urwid.Divider(),
            urwid.Text("Menú de Administrador", align='center'),
            urwid.Divider(),
            urwid.Button("Ver inventario", on_press=self.ver_inventario),
            urwid.Button("Agregar verdura", on_press=self.agregar_verdura),
            urwid.Button("Borrar verdura", on_press=self.borrar_verdura),
            urwid.Divider(),
            urwid.Button("Salir", on_press=self.main.mostrar_login)
        ])
        self._w = urwid.Filler(pile, valign='top')

    def ver_inventario(self, button):
        if not self.inventario:
            contenido = "El inventario está vacío."
        else:
            contenido = "\n".join([
                f"{verdura}: Precio: {datos['precio']}, Cantidad: {datos['cantidad']}"
                for verdura, datos in self.inventario.items()
            ])
        
        body = urwid.Pile([
            urwid.Text(f"Inventario:\n{contenido}", align='center'),
            urwid.Divider(),
            urwid.Button("Volver", on_press=self.mostrar_menu)
        ])

        self.main.loop.widget = urwid.Overlay(
            urwid.LineBox(urwid.Filler(body)),
            self.main.loop.widget,
            align='center',
            width=50,
            height=min(15, len(self.inventario) + 7),
            valign='middle'
        )

    def agregar_verdura(self, button):
        self.nombre_edit = urwid.Edit("Nombre de la verdura: ")
        self.precio_edit = urwid.Edit("Precio: ")
        self.cantidad_edit = urwid.Edit("Cantidad: ")

        self.main.loop.widget = urwid.Overlay(
            urwid.LineBox(urwid.Pile([
                urwid.Text("Agregar verdura", align='center'),
                urwid.Divider(),
                self.nombre_edit,
                self.precio_edit,
                self.cantidad_edit,
                urwid.Divider(),
                urwid.Button("Guardar", on_press=self.guardar_verdura),
                urwid.Button("Cancelar", on_press=self.mostrar_menu)
            ])),
            self.main.loop.widget,
            align='center',
            width=40,
            height=12,
            valign='middle'
        )

    def guardar_verdura(self, button):
        nombre = self.nombre_edit.edit_text.strip()
        precio = self.precio_edit.edit_text.strip()
        cantidad = self.cantidad_edit.edit_text.strip()

        if not nombre:
            self.mostrar_mensaje("Error: Nombre vacío.")
            return
        
        try:
            precio = float(precio)
            cantidad = int(cantidad)
            self.inventario[nombre] = {"precio": precio, "cantidad": cantidad}
            self.guardar_inventario()
            self.mostrar_mensaje(f"'{nombre}' agregada al inventario.")
        except ValueError:
            self.mostrar_mensaje("Error: El precio debe ser un número y la cantidad un entero.")

    def borrar_verdura(self, button):
        if not self.inventario:
            self.mostrar_mensaje("Inventario vacío.")
            return

        items = [urwid.Text(f"{verdura} - Precio: {datos['precio']} - Cantidad: {datos['cantidad']}") for verdura, datos in self.inventario.items()]
        lista = urwid.ListBox(urwid.SimpleFocusListWalker(items))
        self.verduras_lista = list(self.inventario.keys())

        self.main.loop.widget = urwid.Overlay(
            urwid.LineBox(urwid.Pile([
                urwid.Text("Seleccione la verdura a borrar", align='center'),
                urwid.Divider(),
                lista,
                urwid.Divider(),
                urwid.Button("Borrar", on_press=self.confirmar_borrar, user_data=lista),
                urwid.Button("Cancelar", on_press=self.mostrar_menu)
            ])),
            self.main.loop.widget,
            align='center',
            width=50,
            height=15,
            valign='middle'
        )

    def confirmar_borrar(self, button, lista):
        focus_widget, index = lista.get_focus()
        if index is not None:
            nombre = self.verduras_lista[index]
            del self.inventario[nombre]
            self.guardar_inventario()
            self.mostrar_mensaje(f"'{nombre}' eliminada del inventario.")
        else:
            self.mostrar_mensaje("No se seleccionó ninguna verdura.")

    def mostrar_mensaje(self, mensaje):
        mensaje_box = urwid.Overlay(
            urwid.LineBox(urwid.Filler(urwid.Text(f"\n{mensaje}\n", align='center'))),
            self.main.loop.widget,
            align='center',
            width=30,
            height=5,
            valign='middle'  
        )
        
        self.main.loop.widget = mensaje_box
        self.main.loop.set_alarm_in(1, self.mostrar_menu)

    def regresar_menu(self, loop, data):
        self.mostrar_menu()
