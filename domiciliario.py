import urwid

class DomiciliarioView(urwid.WidgetWrap):
    def __init__(self, main):
        self.main = main
        pile = urwid.Pile([
            urwid.Divider(),
            urwid.Text("Menú de Domiciliario", align='center'),
            urwid.Divider(),
            urwid.Button("Opción 1 (Domiciliario)", on_press=lambda x: self.mensaje("Opción 1 (Domiciliario)")),
            urwid.Button("Opción 2 (Domiciliario)", on_press=lambda x: self.mensaje("Opción 2 (Domiciliario)")),
            urwid.Divider(),
            urwid.Button("Salir", on_press=self.main.mostrar_login)
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