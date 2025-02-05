import urwid
import re
class AdminView(urwid.WidgetWrap):
    def __init__(self, main):
        self.main = main
        self.cargar_inventario()
        self.mostrar_menu()

    def cargar_inventario(self):
        self.inventario = {}
        try:
            with open("inventario.txt", "r", encoding="utf-8") as file:
                for linea in file:
                    linea = re.sub(r"[^\x20-\x7E]", "", linea)
                    verdura, precio, cantidad = linea.strip().split(": ")
                    self.inventario[verdura] = {
                        "precio": float(precio),
                        "cantidad": int(cantidad)
                    }
        except FileNotFoundError:
            self.inventario = {}

    def guardar_inventario(self):
        with open("inventario.txt", "w", encoding="utf-8") as file:
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
    
        # Crear una lista de botones, uno para cada verdura
        items = []
        for verdura, datos in self.inventario.items():
            # Crear un botón para cada verdura
            button = urwid.Button(f"{verdura} - Precio: {datos['precio']} - Cantidad: {datos['cantidad']}")
            # Asignar el manejador de eventos para borrar la verdura
            urwid.connect_signal(button, 'click', self.confirmar_borrar, verdura)
            items.append(button)
    
        # Crear un ListBox con los botones
        lista = urwid.ListBox(urwid.SimpleFocusListWalker(items))
    
        # Usar BoxAdapter para envolver el ListBox
        body = urwid.Pile([
            urwid.Text("Seleccione la verdura a borrar", align='center'),
            urwid.Divider(),
            urwid.BoxAdapter(lista, height=10),  # Ajusta la altura según sea necesario
            urwid.Divider(),
            urwid.Button("Cancelar", on_press=self.mostrar_menu)
        ])
    
        # Mostrar el overlay con el ListBox
        self.main.loop.widget = urwid.Overlay(
            urwid.LineBox(urwid.Filler(body, valign='top')),
            self.main.loop.widget,
            align='center',
            width=50,
            height=15,
            valign='middle'
        )
    def confirmar_borrar(self, button, verdura):
        # Eliminar la verdura del inventario
        if verdura in self.inventario:
            del self.inventario[verdura]
            self.guardar_inventario()
            self.mostrar_mensaje(f"'{verdura}' eliminada del inventario.")
        else:
            self.mostrar_mensaje("Error: La verdura no existe en el inventario.")

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
