import urwid
import datetime
import re
import os
import warnings
from urwid.widget import ColumnsWarning
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Ignorar warnings específicos de urwid
warnings.filterwarnings("ignore", category=ColumnsWarning)

class VendedorView(urwid.WidgetWrap):
    def __init__(self, main):
        self.main = main
        self.carrito = []
        self.total_ganancia = 0.0
        self.cargar_inventario()
        
        # Crear elementos de la UI
        self.inventario_frame = self.crear_inventario_frame()
        self.carrito_listbox = urwid.SimpleListWalker([])
        self.actualizar_carrito_ui()
        
        # Diseño principal
        self.columns = urwid.Columns([
            ('weight', 2, self.inventario_frame),
            ('weight', 1, urwid.LineBox(urwid.ListBox(self.carrito_listbox))),
        ])
        
        pile = urwid.Pile([
            urwid.Text("Vendedor - Sistema de Ventas", align='center'),
            urwid.Divider(),
            self.columns,
            urwid.Divider(),
            urwid.Button("Finalizar Venta", on_press=self.finalizar_venta),
            urwid.Button("Cerrar Caja", on_press=self.cerrar_caja),
            urwid.Button("Volver al inicio", on_press=self.volver_al_inicio)
        ])
        
        super().__init__(urwid.Filler(pile, valign='top'))
    
    def crear_inventario_frame(self):
        """Crea el contenedor del inventario para poder refrescarlo"""
        self.inventario_listbox = self.crear_lista_inventario()
        return urwid.LineBox(urwid.BoxAdapter(self.inventario_listbox, 20))
    
    def cargar_inventario(self):
        """Carga el inventario desde el archivo inventario.txt"""
        self.inventario = {}
        try:
            with open("inventario.txt", "r", encoding="utf-8") as file:
                for linea in file:
                    partes = linea.strip().split(": ")
                    if len(partes) >= 5:
                        id_producto = partes[0]
                        self.inventario[id_producto] = {
                            "nombre": partes[1],
                            "precio_compra": float(partes[2]),
                            "precio_venta": float(partes[3]),
                            "cantidad": int(partes[4])
                        }
        except FileNotFoundError:
            self.inventario = {}

    def crear_lista_inventario(self):
        """Crea la lista de productos disponibles en el inventario"""
        items = []
        for id_producto, datos in self.inventario.items():
            if datos['cantidad'] > 0:
                nombre_producto = datos['nombre']
                if datos['cantidad'] < 5:
                    nombre_producto += " (!!!)"
                btn = urwid.Button(
                    f"{id_producto}: {nombre_producto} - ${datos['precio_venta']} ({datos['cantidad']} disponibles)",
                    on_press=self.seleccionar_producto,
                    user_data=id_producto
                )
                items.append(btn)
        return urwid.ListBox(urwid.SimpleFocusListWalker(items))

    def seleccionar_producto(self, button, id_producto):
        """Muestra un popup para seleccionar la cantidad del producto"""
        producto = self.inventario[id_producto]
        self.producto_seleccionado = producto
        self.id_seleccionado = id_producto
        
        self.cantidad_edit = urwid.Edit("Cantidad a vender: ")
        
        self.popup = urwid.Overlay(
            urwid.LineBox(urwid.Pile([
                urwid.Text(f"Seleccionar cantidad para\n{producto['nombre']}"),
                self.cantidad_edit,
                urwid.Button("Agregar al carrito", on_press=self.agregar_al_carrito),
                urwid.Button("Cancelar", on_press=self.cerrar_popup)
            ])),
            self.main.loop.widget,
            align='center',
            width=40,
            height=8,
            valign='middle'
        )
        self.main.loop.widget = self.popup

    def agregar_al_carrito(self, button):
        """Agrega el producto seleccionado al carrito"""
        try:
            cantidad = int(self.cantidad_edit.get_edit_text())
            producto = self.inventario[self.id_seleccionado]
            
            if cantidad <= 0:
                raise ValueError
                
            if cantidad > producto['cantidad']:
                self.mostrar_error("Cantidad excede el inventario")
                return
                
            # Buscar si ya está en el carrito
            for item in self.carrito:
                if item['id'] == self.id_seleccionado:
                    item['cantidad'] += cantidad
                    break
            else:
                self.carrito.append({
                    'id': self.id_seleccionado,
                    'nombre': producto['nombre'],
                    'precio_venta': producto['precio_venta'],
                    'precio_compra': producto['precio_compra'],
                    'cantidad': cantidad
                })
            
            self.actualizar_carrito_ui()
            self.cerrar_popup(None)
            
        except ValueError:
            self.mostrar_error("Cantidad inválida")

    def actualizar_carrito_ui(self):
        """Actualiza la interfaz del carrito de compras"""
        self.carrito_listbox.clear()
        self.total_venta = 0.0
        
        for item in self.carrito:
            total_item = item['cantidad'] * item['precio_venta']
            self.total_venta += total_item  # Sumamos el total de la venta
            
            txt = urwid.Text(
                f"{item['nombre']} x{item['cantidad']}\n"
                f"Total: ${total_item:.2f}",
                align='left'
            )
            self.carrito_listbox.append(txt)
        
        # Agregar totales
        self.carrito_listbox.append(urwid.Divider())
        self.carrito_listbox.append(urwid.Text(f"Total de la venta: ${self.total_venta:.2f}", align='center'))

    def cerrar_popup(self, button):
        """Cierra el popup de selección de cantidad"""
        self.main.loop.widget = self

    def mostrar_error(self, mensaje):
        """Muestra un mensaje de error en un popup"""
        error_popup = urwid.Overlay(
            urwid.LineBox(urwid.Pile([
                urwid.Text(('error', mensaje), align='center'),
                urwid.Button("OK", on_press=self.cerrar_popup)
            ])),
            self.main.loop.widget,
            align='center',
            width=30,
            height=5,
            valign='middle'
        )
        self.main.loop.widget = error_popup

    def finalizar_venta(self, button):
        """Finaliza la venta, actualiza el inventario y guarda la transacción"""
        if not self.carrito:
            self.mostrar_error("Carrito vacío")
            return
            
        # Actualizar inventario
        for item in self.carrito:
            id_producto = item['id']
            self.inventario[id_producto]['cantidad'] -= item['cantidad']
            
        # Guardar inventario actualizado
        with open("inventario.txt", "w", encoding="utf-8") as f:
            for id_producto, datos in self.inventario.items():
                f.write(f"{id_producto}: {datos['nombre']}: {datos['precio_compra']}: "
                        f"{datos['precio_venta']}: {datos['cantidad']}\n")
        
        # Recargar y refrescar inventario
        self.cargar_inventario()
        self.refrescar_inventario()
        
        # Guardar venta en historial
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("ventas.txt", "a", encoding="utf-8") as f:
            f.write(f"Fecha: {fecha}\n")
            for item in self.carrito:
                f.write(f"Producto: {item['nombre']} x{item['cantidad']} - "
                    f"Total: ${item['precio_venta'] * item['cantidad']:.2f}\n")
            f.write(f"Total de la venta: ${self.total_venta:.2f}\n")  # Cambiamos a total de la venta
            f.write("="*50 + "\n")
        
        # Generar factura en PDF
        self.generar_factura_pdf(fecha)
        
        # Resetear carrito
        self.carrito = []
        self.actualizar_carrito_ui()
        self.mostrar_error("Venta finalizada exitosamente")

    def generar_factura_pdf(self, fecha):
        """Genera un PDF con la factura de la venta"""
        # Crear el archivo PDF
        nombre_archivo = f"facturas/factura_{fecha.replace(':', '-')}.pdf"
        if not os.path.exists("facturas"):
            os.makedirs("facturas")
        
        c = canvas.Canvas(nombre_archivo, pagesize=letter)
        width, height = letter
        
        # Encabezado de la factura
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "Factura de Venta")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, f"Fecha: {fecha}")
        
        # Detalles de la venta
        y = height - 100
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Producto")
        c.drawString(200, y, "Cantidad")
        c.drawString(300, y, "Precio Unitario")
        c.drawString(400, y, "Total")
        
        c.setFont("Helvetica", 12)
        y -= 20
        for item in self.carrito:
            c.drawString(50, y, item['nombre'])
            c.drawString(200, y, str(item['cantidad']))
            c.drawString(300, y, f"${item['precio_venta']:.2f}")
            c.drawString(400, y, f"${item['precio_venta'] * item['cantidad']:.2f}")
            y -= 20
        
        # Total de la venta
        c.setFont("Helvetica-Bold", 12)
        c.drawString(300, y - 20, "Total de la Venta:")
        c.drawString(400, y - 20, f"${self.total_venta:.2f}")
        
        # Guardar el PDF
        c.save()

    def refrescar_inventario(self):
        """Actualiza la lista del inventario y su contenedor"""
        nuevo_inventario = self.crear_lista_inventario()
        nuevo_frame = urwid.LineBox(urwid.BoxAdapter(nuevo_inventario, 20))
        self.inventario_frame = nuevo_frame
        self.columns.contents[0] = (self.inventario_frame, self.columns.contents[0][1])

    def cerrar_caja(self, button):
        """Cierra la caja y guarda las ventas del día en un archivo"""
        # Crear la carpeta 'diario' si no existe
        if not os.path.exists("diario"):
            os.makedirs("diario")
        
        # Obtener la fecha actual
        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
        nombre_archivo = f"diario/ventas_dia_{fecha_actual}.txt"
        
        # Leer el archivo de ventas y filtrar las del día actual
        ventas_del_dia = []
        total_ventas_dia = 0.0  # Variable para almacenar la suma total de ventas del día
        try:
            with open("ventas.txt", "r", encoding="utf-8") as f:
                ventas = f.read().split("=" * 50 + "\n")  # Separar por ventas
                for venta in ventas:
                    if f"Fecha: {fecha_actual}" in venta:
                        ventas_del_dia.append(venta.strip())
                        # Extraer el total de ventas de cada transacción usando una expresión regular
                        for line in venta.split("\n"):
                            match = re.search(r"Total de la venta: \$(\d+\.\d+)", line)
                            if match:
                                total_ventas_dia += float(match.group(1))  # Sumar el total de la venta
        except FileNotFoundError:
            self.mostrar_error("No hay ventas registradas hoy.")
            return
        
        # Guardar las ventas del día en un archivo con el formato deseado
        if ventas_del_dia:
            with open(nombre_archivo, "w", encoding="utf-8") as f:
                f.write("\n\n----------------------------------------------------------------\n\n".join(ventas_del_dia))
                f.write("\n\nTotal de ventas del día: ${:.2f}".format(total_ventas_dia))  # Escribir total ventas del día
            self.mostrar_error(f"Caja cerrada. Ventas guardadas en {nombre_archivo}.")
        else:
            self.mostrar_error("No hay ventas registradas hoy.")
        
    def volver_al_inicio(self, button):
        """Regresa a la pantalla de inicio de sesión"""
        self.main.mostrar_login()