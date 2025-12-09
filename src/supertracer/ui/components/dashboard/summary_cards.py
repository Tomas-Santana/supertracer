from nicegui import ui

def summary_card(title: str, value: str, icon: str, color: str = 'blue') -> ui.label:
    with ui.card().classes('flex-1 min-w-[200px] p-4 bg-transparent border rounded-lg').style(f'border-color: {color}'):
        with ui.row().classes('items-center justify-between w-full'):
            with ui.column().classes('gap-1'):
                ui.label(title).classes('text-gray-400 text-sm font-medium uppercase')
                lbl = ui.label(value).classes('text-2xl font-bold text-white')
            ui.icon(icon, color=color).classes(f'text-3xl opacity-80')
    return lbl
