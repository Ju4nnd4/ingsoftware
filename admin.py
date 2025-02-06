import tkinter as tk
from tkinter import filedialog
import re
import urwid


class AdminView(urwid.WidgetWrap):
    def __init__(self, main):
        self.main = main
        self.cargar_inventario()
        # Inicializar el widget envuelto con un widget temporal
        super().__init__(urwid.Text("Cargando..."))
        self.mostrar_menu()

    def cargar_inventario(self):
        self.inventario = {}
        self.ultimo_id = 0  # Inicializar el contador de IDs
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
                    # Actualizar el último ID
                    if int(id_producto) > self.ultimo_id:
                        self.ultimo_id = int(id_producto)
        except FileNotFoundError:
            self.inventario = {}

    def guardar_inventario(self):
        with open("inventario.txt", "w", encoding="utf-8") as file:
            for id_producto, datos in self.inventario.items():
                file.write(f"{id_producto}: {datos['nombre']}: {datos['precio_compra']}: {datos['precio_venta']}: {datos['cantidad']}\n")

    def generar_nuevo_id(self):
        self.ultimo_id += 1  # Incrementar el último ID
        return str(self.ultimo_id)

    def mostrar_menu(self, *args):
        pile = urwid.Pile([
            urwid.Divider(),
            urwid.Text("Menú de Administrador", align='center'),
            urwid.Divider(),
            urwid.Button("Ver inventario", on_press=self.ver_inventario),
            urwid.Button("Agregar producto", on_press=self.agregar_producto),
            urwid.Button("Borrar producto", on_press=self.borrar_producto),
            urwid.Button("Cambiar precio de venta", on_press=self.cambiar_precio_venta),
            urwid.Button("Generar pedido", on_press=self.generar_pedido),
            urwid.Button("Cargar pedido", on_press=self.cargar_pedido),
            urwid.Divider(),
            urwid.Button("Volver al inicio", on_press=self.volver_al_inicio),
        ])
        # Actualizar el widget envuelto y el widget principal
        self._wrapped_widget = urwid.Filler(pile, valign='top')
        self.main.loop.widget = self._wrapped_widget  # Actualizar el widget principal

    def ver_inventario(self, button):
        if not self.inventario:
            contenido = [urwid.Text("El inventario está vacío.", align='center')]
        else:
            contenido = [
                urwid.Text(
                    f"ID: {id_producto} | Nombre: {datos['nombre']} | "
                    f"Precio de compra: {datos['precio_compra']} | "
                    f"Precio de venta: {datos['precio_venta']} | "
                    f"Cantidad: {datos['cantidad']}" +
                    (" (!!!)" if datos['cantidad'] < 5 else ""),
                    align='left'
                )
                for id_producto, datos in self.inventario.items()
            ]
        
        # Crear un ListBox para permitir el desplazamiento vertical
        lista = urwid.ListBox(urwid.SimpleFocusListWalker(contenido))
        
        body = urwid.Pile([
            urwid.Text("Inventario:", align='center'),
            urwid.Divider(),
            urwid.BoxAdapter(lista, height=min(20, len(self.inventario) + 5)),  # Ajustar altura
            urwid.Divider(),
            urwid.Button("Volver", on_press=self.volver)  # Usar self.volver
        ])

        self.main.loop.widget = urwid.Overlay(
            urwid.LineBox(urwid.Filler(body, valign='top')),
            self.main.loop.widget,
            align='left',  # Cambia a 'center', 'right', o 'left' para mover el recuadro
            width=100,  # Aumentar el ancho
            height=min(30, len(self.inventario) + 10),  # Aumentar la altura
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
            id_producto = self.generar_nuevo_id()  # Generar un ID secuencial
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

    def generar_pedido(self, button):
        self.nombre_pedido_edit = urwid.Edit("Nombre del producto: ")
        self.precio_pedido_edit = urwid.Edit("Precio de compra: ")
        self.cantidad_pedido_edit = urwid.Edit("Cantidad: ")
    
        self.main.loop.widget = urwid.Overlay(
            urwid.LineBox(urwid.Pile([
                urwid.Text("Generar pedido", align='center'),
                urwid.Divider(),
                self.nombre_pedido_edit,
                self.precio_pedido_edit,
                self.cantidad_pedido_edit,
                urwid.Divider(),
                urwid.Button("Guardar", on_press=self.guardar_pedido),
                urwid.Button("Volver", on_press=self.volver)  # Usar self.volver
            ])),
            self.main.loop.widget,
            align='center',
            width=40,
            height=12,
            valign='middle'
        )

    def guardar_pedido(self, button):
        nombre = self.nombre_pedido_edit.edit_text.strip()
        precio = self.precio_pedido_edit.edit_text.strip()
        cantidad = self.cantidad_pedido_edit.edit_text.strip()

        if not nombre or not precio or not cantidad:
            self.mostrar_mensaje("Error: Todos los campos son obligatorios.")
            return
        
        try:
            precio = float(precio)
            cantidad = int(cantidad)
            with open("pedido.txt", "a", encoding="utf-8") as file:
                file.write(f"{nombre}: {precio}: {cantidad}\n")
            self.mostrar_mensaje(f"'{nombre}' agregado al pedido.")
        except ValueError:
            self.mostrar_mensaje("Error: El precio debe ser un número y la cantidad un entero.")

    def cargar_pedido(self, button):
        # Inicializar tkinter
        root = tk.Tk()
        root.withdraw()  # Ocultar la ventana principal de tkinter

        # Abrir el explorador de archivos para seleccionar un archivo de texto
        archivo_pedido = filedialog.askopenfilename(
            title="Seleccionar archivo de pedido",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )

        if not archivo_pedido:
            self.mostrar_mensaje("No se seleccionó ningún archivo.")
            return

        try:
            with open(archivo_pedido, "r", encoding="utf-8") as file:
                for linea in file:
                    linea = re.sub(r"[^\x20-\x7E]", "", linea)  # Limpiar caracteres no válidos
                    nombre, precio, cantidad = linea.strip().split(": ")
                    precio = float(precio)
                    cantidad = int(cantidad)
                    self.agregar_producto_desde_pedido(nombre, precio, cantidad)
            self.mostrar_mensaje("Pedido cargado exitosamente.")
        except FileNotFoundError:
            self.mostrar_mensaje("Error: No se encontró el archivo de pedido.")
        except ValueError:
            self.mostrar_mensaje("Error: Formato incorrecto en el archivo de pedido.")

    def agregar_producto_desde_pedido(self, nombre, precio_compra, cantidad):
        # Buscar si el producto ya existe en el inventario con el mismo precio de compra
        for id_producto, datos in self.inventario.items():
            if datos["nombre"] == nombre and datos["precio_compra"] == precio_compra:
                self.inventario[id_producto]["cantidad"] += cantidad
                self.guardar_inventario()
                return
        
        # Si no existe, agregar como un nuevo producto
        id_producto = self.generar_nuevo_id()  # Generar un ID secuencial
        self.inventario[id_producto] = {
            "nombre": nombre,
            "precio_compra": precio_compra,
            "precio_venta": precio_compra * 1.5,  # Precio de venta = Precio de compra * 1.5
            "cantidad": cantidad
        }
        self.guardar_inventario()

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