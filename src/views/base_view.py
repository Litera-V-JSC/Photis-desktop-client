import flet as ft


class BaseView(ft.View):
    def __init__(self, page: ft.Page, view_route: str, on_exit_view_path: str=''):
        self.on_exit_view_path = on_exit_view_path
        super().__init__(route=view_route)
        self.page = page

    def on_exit(self, e=None):
        self.page.go(self.on_exit_view_path)
