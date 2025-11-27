from nicegui import ui


def search_input(placeholder: str = "Search Message") -> ui.input:
    """Reusable search input component."""
    return ui.input(placeholder=placeholder).classes(
        'w-full text-white border-white').props(
        'outlined dense dark clearable')
