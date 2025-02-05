import urwid
import re
import uuid  # Para generar IDs únicos

class AdminView(urwid.WidgetWrap):
    def __init__(self, main):
        self.main = main
        self.cargar_inventario()
        # Inicializar el widget envuelto con un widget temporal
        super().__init__(urwid.Text("Cargando..."))
        self.mostrar_menu()

    def cargar_inventario(self):
        self.inventario = {}
        try:
            with open("inventario.txt", "r", encoding="utf-8") as file:
                for linea in file:
                    linea = re.sub(r"[^\x20-\x7E]", "", linea)
                    id_producto, nombre, precio_compra, precio_venta, cantidad = linea.strip().split(": ")
                    self.inventario[id_producto] = {
                        "nombre": nombre,
                        "precio_compra": float(precio_compra),
                        "precio_venta": float(precio_venta),
                        "cantidad": int(cantidad)
                    }
        except FileNotFoundError:
            self.inventario = {}

    def guardar_inventario(self):
        with open("inventario.txt", "w", encoding="utf-8") as file:
            for id_producto, datos in self.inventario.items():
                file.write(f"{id_producto}: {datos['nombre']}: {datos['precio_compra']}: {datos['precio_venta']}: {datos['cantidad']}\n")

    def mostrar_menu(self, *args):
        pile = urwid.Pile([
            urwid.Divider(),
            urwid.Text("Menú de Administrador", align='center'),
            urwid.Divider(),
            urwid.Button("Ver inventario", on_press=self.ver_inventario),
            urwid.Button("Agregar producto", on_press=self.agregar_producto),
            urwid.Button("Borrar producto", on_press=self.borrar_producto),
            urwid.Button("Cambiar precio de venta", on_press=self.cambiar_precio_venta),  # Cambio de nombre
            urwid.Divider(),
            urwid.Button("Volver al inicio", on_press=self.volver_al_inicio),
        ])
        # Actualizar el widget envuelto y el widget principal
        self._wrapped_widget = urwid.Filler(pile, valign='top')
        self.main.loop.widget = self._wrapped_widget  # Actualizar el widget principal

    def ver_inventario(self, button):
        if not self.inventario:
            contenido = "El inventario está vacío."
        else:
            contenido = "\n".join([
                f"ID: {id_producto} | Nombre: {datos['nombre']} | "
                f"Precio de compra: {datos['precio_compra']} | "
                f"Precio de venta: {datos['precio_venta']} | "
                f"Cantidad: {datos['cantidad']}"
                for id_producto, datos in self.inventario.items()
            ])
        
        body = urwid.Pile([
            urwid.Text(f"Inventario:\n{contenido}", align='center'),
            urwid.Divider(),
            urwid.Button("Volver", on_press=self.volver)  # Usar self.volver
        ])

        self.main.loop.widget = urwid.Overlay(
            urwid.LineBox(urwid.Filler(body)),
            self.main.loop.widget,
            align='center',
            width=80,  # Aumentar el ancho para mostrar más información
            height=min(20, len(self.inventario) + 7),
            valign='middle'
        )

    def agregar_producto(self, button):
        self.nombre_edit = urwid.Edit("Nombre del producto: ")
        self.precio_compra_edit = urwid.Edit("Precio de compra: ")
        self.precio_venta_edit = urwid.Edit("Precio de venta: ")
        self.cantidad_edit = urwid.Edit("Cantidad: ")
    
        self.main.loop.widget = urwid.Overlay(
            urwid.LineBox(urwid.Pile([
                urwid.Text("Agregar producto", align='center'),
                urwid.Divider(),
                self.nombre_edit,
                self.precio_compra_edit,
                self.precio_venta_edit,
                self.cantidad_edit,
                urwid.Divider(),
                urwid.Button("Guardar", on_press=self.guardar_producto),
                urwid.Button("Volver", on_press=self.volver)  # Usar self.volver
            ])),
            self.main.loop.widget,
            align='center',
            width=40,
            height=14,  # Aumentar la altura para los nuevos campos
            valign='middle'
        )

    def guardar_producto(self, button):
        nombre = self.nombre_edit.edit_text.strip()
        precio_compra = self.precio_compra_edit.edit_text.strip()
        precio_venta = self.precio_venta_edit.edit_text.strip()
        cantidad = self.cantidad_edit.edit_text.strip()

        if not nombre:
            self.mostrar_mensaje("Error: Nombre vacío.")
            return
        
        try:
            precio_compra = float(precio_compra)
            precio_venta = float(precio_venta)
            cantidad = int(cantidad)
            id_producto = str(uuid.uuid4())  # Generar un ID único
            self.inventario[id_producto] = {
                "nombre": nombre,
                "precio_compra": precio_compra,
                "precio_venta": precio_venta,
                "cantidad": cantidad
            }
            self.guardar_inventario()
            self.mostrar_mensaje(f"'{nombre}' agregado al inventario.")
        except ValueError:
            self.mostrar_mensaje("Error: Los precios deben ser números y la cantidad un entero.")

    def borrar_producto(self, button):
        if not self.inventario:
            self.mostrar_mensaje("Inventario vacío.")
            return
    
        items = []
        for id_producto, datos in self.inventario.items():
            button = urwid.Button(
                f"ID: {id_producto} | Nombre: {datos['nombre']} | "
                f"Precio de compra: {datos['precio_compra']} | "
                f"Precio de venta: {datos['precio_venta']} | "
                f"Cantidad: {datos['cantidad']}"
            )
            urwid.connect_signal(button, 'click', self.confirmar_borrar, id_producto)
            items.append(button)
    
        lista = urwid.ListBox(urwid.SimpleFocusListWalker(items))
    
        body = urwid.Pile([
            urwid.Text("Seleccione el producto a borrar", align='center'),
            urwid.Divider(),
            urwid.BoxAdapter(lista, height=10),
            urwid.Divider(),
            urwid.Button("Volver", on_press=self.volver)  # Usar self.volver
        ])
    
        self.main.loop.widget = urwid.Overlay(
            urwid.LineBox(urwid.Filler(body, valign='top')),
            self.main.loop.widget,
            align='center',
            width=80,  # Aumentar el ancho para mostrar más información
            height=15,
            valign='middle'
        )

    def confirmar_borrar(self, button, id_producto):
        if id_producto in self.inventario:
            nombre = self.inventario[id_producto]["nombre"]
            del self.inventario[id_producto]
            self.guardar_inventario()
            self.mostrar_mensaje(f"'{nombre}' eliminado del inventario.")
        else:
            self.mostrar_mensaje("Error: El producto no existe en el inventario.")

    def cambiar_precio_venta(self, button):
        if not self.inventario:
            self.mostrar_mensaje("Inventario vacío.")
            return
    
        items = []
        for id_producto, datos in self.inventario.items():
            button = urwid.Button(
                f"ID: {id_producto} | Nombre: {datos['nombre']} | "
                f"Precio de venta actual: {datos['precio_venta']}"
            )
            urwid.connect_signal(button, 'click', self.seleccionar_producto_para_cambiar_precio_venta, id_producto)
            items.append(button)
    
        lista = urwid.ListBox(urwid.SimpleFocusListWalker(items))
    
        body = urwid.Pile([
            urwid.Text("Seleccione el producto para cambiar el precio de venta", align='center'),
            urwid.Divider(),
            urwid.BoxAdapter(lista, height=10),
            urwid.Divider(),
            urwid.Button("Volver", on_press=self.volver)  # Usar self.volver
        ])
    
        self.main.loop.widget = urwid.Overlay(
            urwid.LineBox(urwid.Filler(body, valign='top')),
            self.main.loop.widget,
            align='center',
            width=80,  # Aumentar el ancho para mostrar más información
            height=15,
            valign='middle'
        )

    def seleccionar_producto_para_cambiar_precio_venta(self, button, id_producto):
        self.id_producto_seleccionado = id_producto
        self.nuevo_precio_venta_edit = urwid.Edit(f"Nuevo precio de venta para {self.inventario[id_producto]['nombre']}: ")
    
        self.main.loop.widget = urwid.Overlay(
            urwid.LineBox(urwid.Pile([
                urwid.Text(f"Cambiar precio de venta de {self.inventario[id_producto]['nombre']}", align='center'),
                urwid.Divider(),
                self.nuevo_precio_venta_edit,
                urwid.Divider(),
                urwid.Button("Guardar", on_press=self.guardar_nuevo_precio_venta),
                urwid.Button("Volver", on_press=self.volver)  # Usar self.volver
            ])),
            self.main.loop.widget,
            align='center',
            width=40,
            height=10,
            valign='middle'
        )

    def guardar_nuevo_precio_venta(self, button):
        nuevo_precio_venta = self.nuevo_precio_venta_edit.edit_text.strip()
    
        if not nuevo_precio_venta:
            self.mostrar_mensaje("Error: Precio vacío.")
            return
    
        try:
            nuevo_precio_venta = float(nuevo_precio_venta)
            if self.id_producto_seleccionado in self.inventario:
                self.inventario[self.id_producto_seleccionado]["precio_venta"] = nuevo_precio_venta
                self.guardar_inventario()
                self.mostrar_mensaje(
                    f"Precio de venta de '{self.inventario[self.id_producto_seleccionado]['nombre']}' "
                    f"actualizado a {nuevo_precio_venta}."
                )
            else:
                self.mostrar_mensaje("Error: El producto no existe en el inventario.")
        except ValueError:
            self.mostrar_mensaje("Error: El precio debe ser un número.")

    def mostrar_mensaje(self, mensaje):
        mensaje_box = urwid.Overlay(
            urwid.LineBox(urwid.Filler(urwid.Pile([
                urwid.Text(f"\n{mensaje}\n", align='center'),
                urwid.Button("Volver", on_press=self.volver)  # Usar self.volver
            ]), valign='middle')),
            self.main.loop.widget,
            align='center',
            width=30,
            height=5,
            valign='middle'
        )
        
        self.main.loop.widget = mensaje_box

    def volver(self, button):
        self.mostrar_menu()  # Regenera el menú principal

    def volver_al_inicio(self, button):
        self.main.mostrar_login()