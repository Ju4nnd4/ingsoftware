import urwid
import os

class DomiciliarioView(urwid.WidgetWrap):
    def __init__(self, main):
        self.main = main
        self.carpeta_pedidos = "pedidos pendientes"  # Carpeta donde se guardan los pedidos pendientes
        self.carpeta_aceptados = "pedidos aceptados"  # Carpeta donde se guardan los pedidos aceptados
        self.direcciones_aceptadas = []  # Lista para almacenar direcciones de pedidos aceptados

        # Crear la carpeta de pedidos aceptados si no existe
        if not os.path.exists(self.carpeta_aceptados):
            os.makedirs(self.carpeta_aceptados)

        # Cargar los pedidos pendientes y aceptados
        self.pedidos_pendientes = self.cargar_pedidos(self.carpeta_pedidos)
        self.pedidos_aceptados = self.cargar_pedidos(self.carpeta_aceptados)

        # Crear botones para pedidos pendientes y aceptados
        self.botones_pendientes = self.crear_botones(self.pedidos_pendientes, self.mostrar_pedido)
        self.botones_aceptados = self.crear_botones(self.pedidos_aceptados, self.mostrar_pedido_aceptado)

        # Diseño de la interfaz
        self.pedidos_pendientes_frame = urwid.LineBox(urwid.Pile([
            urwid.Text("Pedidos Pendientes", align='center'),
            urwid.Divider(),
            *self.botones_pendientes
        ]))

        self.pedidos_aceptados_frame = urwid.LineBox(urwid.Pile([
            urwid.Text("Pedidos Aceptados", align='center'),
            urwid.Divider(),
            *self.botones_aceptados
        ]))

        columns = urwid.Columns([
            ('weight', 1, self.pedidos_pendientes_frame),
            ('weight', 1, self.pedidos_aceptados_frame)
        ])

        pile = urwid.Pile([
            urwid.Divider(),
            urwid.Text("Menú de Domiciliario", align='center'),
            urwid.Divider(),
            columns,
            urwid.Divider(),
            urwid.Button("Salir", on_press=self.salir)
        ])

        super().__init__(urwid.Filler(pile, valign='top'))

    def cargar_pedidos(self, carpeta):
        """Carga los nombres de los archivos de pedidos en la carpeta especificada."""
        if not os.path.exists(carpeta):
            return []  # Si la carpeta no existe, no hay pedidos

        # Obtener todos los archivos que comienzan con "pedido" y terminan con ".txt"
        pedidos = [f for f in os.listdir(carpeta) if f.startswith("pedido") and f.endswith(".txt")]
        return pedidos

    def crear_botones(self, pedidos, callback):
        """Crea botones para los pedidos."""
        botones = []
        for pedido in pedidos:
            boton = urwid.Button(f"Pedido: {pedido}", on_press=callback, user_data=pedido)
            botones.append(boton)
        return botones

    def mostrar_pedido(self, button, nombre_pedido):
        """Muestra el contenido del pedido pendiente en un recuadro emergente."""
        ruta_pedido = os.path.join(self.carpeta_pedidos, nombre_pedido)
        try:
            with open(ruta_pedido, "r", encoding="utf-8") as f:
                contenido = f.read()
        except FileNotFoundError:
            contenido = "El pedido no pudo ser cargado."

        # Dividir el contenido en líneas para mostrarlo correctamente
        lineas = contenido.split("\n")
        texto_pedido = [urwid.Text(linea) for linea in lineas]  # Crear una lista de widgets Text

        # Crear un ListBox para permitir el desplazamiento si el contenido es muy largo
        lista_pedido = urwid.ListBox(urwid.SimpleFocusListWalker(texto_pedido))

        # Crear el recuadro emergente con el contenido del pedido
        popup_content = urwid.Pile([
            urwid.Text(f"Contenido de {nombre_pedido}:\n", align='center'),
            urwid.LineBox(urwid.BoxAdapter(lista_pedido, height=10)),  # Limitar la altura del contenido
            urwid.Divider(),
            urwid.Button("Aceptar Pedido", on_press=self.aceptar_pedido, user_data=nombre_pedido),
            urwid.Button("Cerrar", on_press=self.cerrar_popup)
        ])

        self.popup = urwid.Overlay(
            urwid.LineBox(popup_content),
            self.main.loop.widget,
            align='center',
            width=("relative", 80),  # Ancho del popup (80% del ancho de la pantalla)
            valign='middle',
            height=("relative", 80)  # Altura del popup (80% del alto de la pantalla)
        )

        # Mostrar el popup
        self.main.loop.widget = self.popup

    def aceptar_pedido(self, button, nombre_pedido):
        """Acepta un pedido y lo mueve a la carpeta de pedidos aceptados."""
        ruta_pedido = os.path.join(self.carpeta_pedidos, nombre_pedido)
        ruta_aceptado = os.path.join(self.carpeta_aceptados, nombre_pedido)

        # Mover el archivo a la carpeta de pedidos aceptados
        os.rename(ruta_pedido, ruta_aceptado)

        # Actualizar las listas de pedidos
        self.pedidos_pendientes.remove(nombre_pedido)
        self.pedidos_aceptados.append(nombre_pedido)

        # Actualizar la interfaz en tiempo real
        self.actualizar_interfaz()

        # Cerrar el popup
        self.cerrar_popup()

    def actualizar_interfaz(self):
        """Actualiza la interfaz para reflejar los cambios en los pedidos."""
        # Actualizar los botones de pedidos pendientes y aceptados
        self.botones_pendientes = self.crear_botones(self.pedidos_pendientes, self.mostrar_pedido)
        self.botones_aceptados = self.crear_botones(self.pedidos_aceptados, self.mostrar_pedido_aceptado)

        # Actualizar los frames de la interfaz
        self.pedidos_pendientes_frame.original_widget = urwid.Pile([
            urwid.Text("Pedidos Pendientes", align='center'),
            urwid.Divider(),
            *self.botones_pendientes
        ])

        self.pedidos_aceptados_frame.original_widget = urwid.Pile([
            urwid.Text("Pedidos Aceptados", align='center'),
            urwid.Divider(),
            *self.botones_aceptados
        ])

    def mostrar_pedido_aceptado(self, button, nombre_pedido):
        """Muestra el contenido de un pedido aceptado en un recuadro emergente."""
        ruta_pedido = os.path.join(self.carpeta_aceptados, nombre_pedido)
        try:
            with open(ruta_pedido, "r", encoding="utf-8") as f:
                contenido = f.read()
        except FileNotFoundError:
            contenido = "El pedido no pudo ser cargado."

        # Dividir el contenido en líneas para mostrarlo correctamente
        lineas = contenido.split("\n")
        texto_pedido = [urwid.Text(linea) for linea in lineas]  # Crear una lista de widgets Text

        # Crear un ListBox para permitir el desplazamiento si el contenido es muy largo
        lista_pedido = urwid.ListBox(urwid.SimpleFocusListWalker(texto_pedido))

        # Crear el recuadro emergente con el contenido del pedido
        popup_content = urwid.Pile([
            urwid.Text(f"Contenido de {nombre_pedido}:\n", align='center'),
            urwid.LineBox(urwid.BoxAdapter(lista_pedido, height=10)),  # Limitar la altura del contenido
            urwid.Divider(),
            urwid.Button("Cerrar", on_press=self.cerrar_popup)
        ])

        self.popup = urwid.Overlay(
            urwid.LineBox(popup_content),
            self.main.loop.widget,
            align='center',
            width=("relative", 80),  # Ancho del popup (80% del ancho de la pantalla)
            valign='middle',
            height=("relative", 80)  # Altura del popup (80% del alto de la pantalla)
        )

        # Mostrar el popup
        self.main.loop.widget = self.popup

    def cerrar_popup(self, button=None):
        """Cierra el recuadro emergente y regresa al menú de domiciliario."""
        self.main.loop.widget = self

    def salir(self, button):
        """Regresa a la pantalla de inicio de sesión."""
        self.main.mostrar_login()