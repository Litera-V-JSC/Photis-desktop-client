from .base_view import BaseView
import flet as ft
from lib import utils
import json
import requests
import datetime
import base64

class ItemEditView(BaseView):
    def __init__(self, page: ft.Page, id, img, category, date, sum):
        super().__init__(page=page, view_route='/edititem', on_exit_view_path='/items')

        self.file_picker = ft.FilePicker(on_result=lambda e: utils.file_picked(self, e))
        self.page.overlay.append(self.file_picker)
        self.file_path = None
        self.id = id

        self.original_category = category
        self.original_sum = sum
        self.original_date = utils.date_to_text(date)
        self.original_img_path = img
        self.original_img_base64 = utils.encode_base64(img)
        self.frame_base64 = self.original_img_base64
        self.has_changes = False

        self.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                tooltip="Назад",
                on_click=self.on_exit
            ),
            title=ft.Text("Редактирование информации"),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
        )

        self.category_dropdown = ft.Dropdown(
            label="Категория",
            options=[ft.dropdown.Option(c["category"]) for c in self.page.categories],
            value=category,
            on_change=self.toggle_submit_button
        )

        self.sum_field = ft.TextField(
            label="Сумма",
            hint_text="Введите сумму",
            keyboard_type=ft.KeyboardType.NUMBER,
            value=sum,
            width=200,
            on_change=self.toggle_submit_button 
        )

        self.date_field = ft.TextField(
            label="Дата",
            width=200,
            value=utils.date_to_text(date),
            on_change=self.toggle_submit_button
        )

        self.file_name_text = ft.Text(f"выбран файл: {img}", italic=True, size=12)

        self.attach_button = ft.ElevatedButton(
            "Изменить изображение",
            on_click=lambda e : utils.pick_file(self, e)
        )

        self.submit_button = ft.ElevatedButton(
            "Применить изменения",
            on_click=self.submit,
            disabled=True
        )

        self.form = ft.Column(
            controls=[
                self.category_dropdown,
                self.sum_field,
                self.date_field,
                self.attach_button,
                self.file_name_text,
                self.submit_button,
            ],
            spacing=15,
            width=300,
            alignment=ft.MainAxisAlignment.START,
        )

        self.page.dialog = ft.AlertDialog(
            title=ft.Container(ft.Text(""), alignment=ft.alignment.center),
            content=ft.Text(""),
            actions=[
                ft.TextButton("OK", on_click=lambda e: utils.close_dialog(self))
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )

        self.controls.append(self.appbar)
        self.controls.append(self.form)

    def toggle_submit_button(self, e=None):
        has_changes = self.check_changes()
        if has_changes != self.has_changes:
            self.has_changes = has_changes
            self.submit_button.disabled = not has_changes
            self.page.update()

    def check_changes(self, e=None):
        return self.category_dropdown.value != self.original_category or \
            self.sum_field.value != self.original_sum or \
            self.date_field.value != self.original_date or \
            self.frame_base64 != self.original_img_base64
        

    def submit(self, e):
        try:
            sum_float = float(self.sum_field.value)
            date_sql = utils.date_to_sql(self.date_field.value)

            if date_sql is None:
                utils.show_dialog(self, "Не сохранено", "Дата введена некорректно. Придерживаетесь формата: 01.01.2001")
                return
        except Exception as e:
            utils.show_dialog(self, "Не сохранено", "Сумма введена некорректно. Введите числовое значение")
            return

        modified_item = json.dumps({
            "id": self.id,
            "category": self.category_dropdown.value,
            "sum": sum_float,
            "creation_date": date_sql,
            "image": self.frame_base64
        })
        
        response = requests.post(f'{self.page.ROOT_URL}/update-item', data=modified_item, headers=self.page.content_provided_request_headers)
        print(response)
        utils.show_dialog(self, "Сохранено", "Чтобы увидеть изменения, перезагрузите страницу")
        self.page.update()
