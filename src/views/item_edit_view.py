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

		self.appbar = ft.AppBar(
			leading=ft.IconButton(
				icon=ft.Icons.ARROW_BACK,
				tooltip="Назад",
				on_click=self.on_exit
			),
			title=ft.Text("Редактирование информации"),
			bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
		)

		# Поля формы
		self.category_dropdown = ft.Dropdown(
				label="Категория",
				options=[ft.dropdown.Option(c["category"]) for c in self.page.categories],
		)
		self.sum_field = ft.TextField(
			label="Сумма",
			hint_text="Введите сумму",
			keyboard_type=ft.KeyboardType.NUMBER,
			value=sum,
			width=200
		)
		self.date_field = ft.TextField(
			label="Дата",
			width=200,
			value=datetime.date.today().strftime('%d.%m.%Y'),
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

		# Левая колонка — форма
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


	def check_fieds_data(self):
		try:
			category = self.category_dropdown.value
			sum_ = self.sum_field.value
			date_ = self.date_field.value
			img_base64 = self.frame_base64
			if all([category, sum_, date_, img_base64]):
				self.submit_button.disabled = False
			else:
				self.submit_button.disabled = True
		except Exception as e:
			self.submit_button.disabled = True
		finally:
			try:
				self.submit_button.update()
			except:
				print("Submit button disabled")

	""" Submit form data """
	def submit(self, e):
		category = self.category_dropdown.value
		sum_ = self.sum_field.value
		date_ = self.date_field.value
		img_base64 = self.frame_base64
		try:
			sum_float = float(sum_)
			date_ = utils.date_to_sql(date_)
			if date_ is None:
				print(f"Wrong 'date' field format")
				utils.show_dialog(self, "Ошибка", "Дата введена некорректно. Придерживаетесь формата: 01.01.2001")
				return

		except Exception as e:
			print(f"Error while converting data: {e}")
			utils.show_dialog(self, "Ошибка", "Сумма введена некорректно. В поле суммы необходимо вносить только числовые значения")
			return

		modified_item = json.dumps({
			"category": category,
			"sum": sum_float,
			"creation_date": date_,
			"image": img_base64
		})
		response = requests.post(f'{self.page.ROOT_URL}/edit-item', data=modified_item, headers=self.page.content_provided_request_headers)
		print(response)
		utils.show_dialog(self, "Объект изменен", "Чтобы увидеть изменения, перезагрузите страницу")
		self.page.update()
