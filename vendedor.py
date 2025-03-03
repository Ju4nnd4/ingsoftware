import urwid
import datetime
import re
import os
import warnings
import subprocess  # Para abrir el PDF
from urwid.widget import ColumnsWarning
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Ignorar warnings específicos de urwid
warnings.filterwarnings("ignore", category=ColumnsWarning)

class VendedorView(urwid.WidgetWrap):
    def __init__(self, main):
        self.main = main
        self.carrito = []
        self.total_venta = 0.0
        self.descuento = 0.0  # Porcentaje de descuento
        self.cargar_inventario()
        
        # Cargar el último ID de factura
        self.ultimo_id_factura = self.cargar_ultimo_id_factura()
        
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
            urwid.Button("Finalizar Venta", on_press=self.finalizar_venta_local),  # Venta local
            urwid.Button("Finalizar Venta a Domicilio", on_press=self.finalizar_venta_domicilio),  # Venta a domicilio
            urwid.Button("Cerrar Caja", on_press=self.cerrar_caja),
            urwid.Button("Volver al inicio", on_press=self.volver_al_inicio)
        ])
        
        super().__init__(urwid.Filler(pile, valign='top'))
    
    def cargar_ultimo_id_factura(self):
        """Carga el último ID de factura desde un archivo"""
        try:
            with open("ultima_factura.txt", "r", encoding="utf-8") as f:
                return int(f.read().strip())
        except FileNotFoundError:
            return 0  # Si el archivo no existe, empezamos desde 0

    def guardar_ultimo_id_factura(self):
        """Guarda el último ID de factura en un archivo"""
        with open("ultima_factura.txt", "w", encoding="utf-8") as f:
            f.write(str(self.ultimo_id_factura))

    def generar_id_factura(self):
        """Genera un nuevo ID de factura"""
        self.ultimo_id_factura += 1
        return self.ultimo_id_factura

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

    def finalizar_venta_local(self, button):
        """Finaliza una venta local"""
        if not self.carrito:
            self.mostrar_error("Carrito vacío")
            return
        
        # Preguntar por el descuento
        self.preguntar_descuento()

    def finalizar_venta_domicilio(self, button):
        """Finaliza una venta a domicilio"""
        if not self.carrito:
            self.mostrar_error("Carrito vacío")
            return
        
        # Preguntar los datos del cliente
        self.preguntar_datos_cliente()

    def preguntar_datos_cliente(self):
        """Pregunta los datos del cliente para una venta a domicilio"""
        self.nombre_cliente_edit = urwid.Edit("Nombre del cliente: ")
        self.direccion_cliente_edit = urwid.Edit("Dirección del cliente: ")
        
        self.popup_datos_cliente = urwid.Overlay(
            urwid.LineBox(urwid.Pile([
                urwid.Text("Ingrese los datos del cliente:", align='center'),
                self.nombre_cliente_edit,
                self.direccion_cliente_edit,
                urwid.Button("Continuar", on_press=self.guardar_datos_cliente),
                urwid.Button("Cancelar", on_press=self.cerrar_popup_datos_cliente)
            ])),
            self.main.loop.widget,
            align='center',
            width=40,
            height=10,
            valign='middle'
        )
        self.main.loop.widget = self.popup_datos_cliente

    def guardar_datos_cliente(self, button):
        """Guarda los datos del cliente y procede con la venta a domicilio"""
        nombre_cliente = self.nombre_cliente_edit.get_edit_text().strip()
        direccion_cliente = self.direccion_cliente_edit.get_edit_text().strip()
        
        if not nombre_cliente or not direccion_cliente:
            self.mostrar_error("Debe ingresar nombre y dirección del cliente.")
            return
        
        # Guardar los datos del cliente en pedidos.txt
        with open("pedidos.txt", "a", encoding="utf-8") as f:
            f.write(f"Cliente: {nombre_cliente}\n")
            f.write(f"Dirección: {direccion_cliente}\n")
            f.write("Productos:\n")
            for item in self.carrito:
                f.write(f"{item['nombre']} x{item['cantidad']}\n")
            f.write("=" * 50 + "\n")
        
        self.cerrar_popup_datos_cliente()
        self.preguntar_descuento()

    def cerrar_popup_datos_cliente(self, button=None):
        """Cierra el popup de datos del cliente"""
        self.main.loop.widget = self

    def preguntar_descuento(self):
        """Pregunta por el descuento"""
        self.descuento_edit = urwid.Edit("Descuento (%): ")
        
        self.popup_descuento = urwid.Overlay(
            urwid.LineBox(urwid.Pile([
                urwid.Text("Ingrese el porcentaje de descuento:"),
                self.descuento_edit,
                urwid.Button("Aplicar descuento", on_press=self.aplicar_descuento),
                urwid.Button("Sin descuento", on_press=self.sin_descuento)
            ])),
            self.main.loop.widget,
            align='center',
            width=40,
            height=8,
            valign='middle'
        )
        self.main.loop.widget = self.popup_descuento

    def aplicar_descuento(self, button):
        """Aplica el descuento a la venta"""
        try:
            self.descuento = float(self.descuento_edit.get_edit_text())
            if self.descuento < 0 or self.descuento > 100:
                raise ValueError
            self.cerrar_popup_descuento()
            self.procesar_venta()
        except ValueError:
            self.mostrar_error("Descuento inválido. Debe ser un número entre 0 y 100.")

    def sin_descuento(self, button):
        """No aplica descuento a la venta"""
        self.descuento = 0.0
        self.cerrar_popup_descuento()
        self.procesar_venta()

    def cerrar_popup_descuento(self, button=None):
        """Cierra el popup de descuento"""
        self.main.loop.widget = self

    def procesar_venta(self):
        """Procesa la venta con el descuento aplicado"""
        # Generar un ID de factura
        id_factura = self.generar_id_factura()
        
        # Calcular el total con descuento
        total_con_descuento = self.total_venta * (1 - self.descuento / 100)
        
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
            f.write(f"ID Factura: {id_factura}\n")
            f.write(f"Fecha: {fecha}\n")
            f.write(f"Descuento: {self.descuento}%\n")  # Guardar el descuento
            for item in self.carrito:
                f.write(f"Producto: {item['nombre']} x{item['cantidad']} - "
                    f"Total: ${item['precio_venta'] * item['cantidad']:.2f}\n")
            f.write(f"Total con descuento: ${total_con_descuento:.2f}\n")
            f.write("="*50 + "\n")
        
        # Guardar el último ID de factura
        self.guardar_ultimo_id_factura()
        
        # Generar factura en PDF
        if hasattr(self, 'nombre_cliente_edit') and hasattr(self, 'direccion_cliente_edit'):
            # Si es una venta a domicilio, guardar en la carpeta facturas_domicilios
            self.generar_factura_pdf(fecha, id_factura, total_con_descuento, "facturas_domicilios")
        else:
            # Si es una venta local, guardar en la carpeta facturas
            self.generar_factura_pdf(fecha, id_factura, total_con_descuento, "facturas")
        
        # Preguntar si desea abrir el PDF
        self.preguntar_abrir_pdf(id_factura)
        
        # Resetear carrito
        self.carrito = []
        self.actualizar_carrito_ui()
        self.mostrar_error("Venta finalizada exitosamente")

    def generar_factura_pdf(self, fecha, id_factura, total_con_descuento, carpeta):
        """Genera un PDF con la factura de la venta"""
        # Crear el archivo PDF
        nombre_archivo = f"{carpeta}/factura_{id_factura}.pdf"
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)
        
        c = canvas.Canvas(nombre_archivo, pagesize=letter)
        width, height = letter
        
        # Encabezado de la factura
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "Factura de Venta")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, f"ID Factura: {id_factura}")
        c.drawString(50, height - 90, f"Fecha: {fecha}")
        c.drawString(50, height - 110, f"Descuento: {self.descuento}%")
        
        # Si es una venta a domicilio, agregar datos del cliente
        if carpeta == "facturas_domicilios":
            c.drawString(50, height - 130, f"Cliente: {self.nombre_cliente_edit.get_edit_text().strip()}")
            c.drawString(50, height - 150, f"Dirección: {self.direccion_cliente_edit.get_edit_text().strip()}")
        
        # Detalles de la venta
        y = height - 170 if carpeta == "facturas_domicilios" else height - 140
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
        c.drawString(400, y - 20, f"${total_con_descuento:.2f}")
        
        # Guardar el PDF
        c.save()

    def preguntar_abrir_pdf(self, id_factura):
        """Pregunta al usuario si desea abrir el PDF de la factura"""
        nombre_archivo = f"facturas/factura_{id_factura}.pdf"
        self.popup_abrir_pdf = urwid.Overlay(
            urwid.LineBox(urwid.Pile([
                urwid.Text("¿Desea abrir el PDF de la factura?", align='center'),
                urwid.Button("Sí", on_press=lambda x: self.abrir_pdf(nombre_archivo)),
                urwid.Button("No", on_press=self.cerrar_popup_abrir_pdf)
            ])),
            self.main.loop.widget,
            align='center',
            width=40,
            height=8,
            valign='middle'
        )
        self.main.loop.widget = self.popup_abrir_pdf

    def abrir_pdf(self, nombre_archivo):
        """Abre el PDF de la factura"""
        if os.name == 'nt':  # Windows
            os.startfile(nombre_archivo)
        elif os.name == 'posix':  # Linux o macOS
            subprocess.run(["xdg-open", nombre_archivo])
        self.cerrar_popup_abrir_pdf()

    def cerrar_popup_abrir_pdf(self, button=None):
        """Cierra el popup de abrir PDF"""
        self.main.loop.widget = self

    def refrescar_inventario(self):
        """Actualiza la lista del inventario y su contenedor"""
        nuevo_inventario = self.crear_lista_inventario()
        nuevo_frame = urwid.LineBox(urwid.BoxAdapter(nuevo_inventario, 20))
        self.inventario_frame = nuevo_frame
        self
    
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
                            match = re.search(r"Total con descuento: \$(\d+\.\d+)", line)
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