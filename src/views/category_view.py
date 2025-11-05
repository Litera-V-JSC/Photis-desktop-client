from .base_view import BaseView
import flet as ft
import requests
import json
from lib import utils


class CategoryView(BaseView):
	def __init__(self, page: ft.Page):
		super().__init__(page=page, view_route='/category', on_exit_view_path='/items')
		
		self.new_category_field = ft.TextField(label="Новая категория", width=300)
		self.add_button = ft.ElevatedButton(text="Добавить", on_click=self.add_category)
		self.reload_button = ft.IconButton(
			icon=ft.Icons.REFRESH,
			tooltip="Reload",
			on_click=self.load_categories
		)

		# AppBar
		self.appbar = ft.AppBar(
			leading=ft.IconButton(
				icon=ft.Icons.ARROW_BACK,
				tooltip="Назад",
				on_click=self.on_exit
			),
			title=ft.Text("Категории документов"),
			bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
		)

		# Blank table for items
		self.table = ft.DataTable(
			columns=[
				ft.DataColumn(ft.Text("")),
				ft.DataColumn(ft.Text("")),
			],
			rows=[],
			expand=True
		)

		self.main_content = ft.Column(
			controls=[
				ft.Row(
					controls=[
						self.new_category_field,
						self.add_button,
						self.reload_button
					],
					alignment=ft.MainAxisAlignment.CENTER,
					spacing=50,
				),
				ft.ListView(controls=[self.table], expand=True)
			],
			alignment=ft.MainAxisAlignment.CENTER,
			horizontal_alignment=ft.CrossAxisAlignment.CENTER,
			spacing=10,
			expand=True,
			scroll=ft.ScrollMode.AUTO
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
		self.controls.append(self.main_content)

		self.load_categories()

	""" Add new category to db """
	def add_category(self, e=None):
		category = self.new_category_field.value
		if not "".join(category.split(" ")).isalnum():
			print(f"Wrong 'category' field format")
			utils.show_dialog(self, "Заполните данные!", "Поле с названием новой категории не может быть пустым")
		else:
			new_category = json.dumps({
				"category": category,
			})
			response = requests.post(f'{self.page.ROOT_URL}/add-category', data=new_category, headers=self.page.content_provided_request_headers)
			print(response)
			if response.status_code in (200, 204):
				utils.show_dialog(self, "Категория сохранена", "Данные таблицы обновлены")
				self.load_categories()
				self.page.update()
			else:
				utils.show_dialog(self, "Ошибка!", "Такая категория уже существует. Выберите другое название")
		
	
	""" Add item row to table """
	def add_row(self, category):
		self.table.rows.append(
			ft.DataRow(
				cells=[
					ft.DataCell(ft.Text(category["category"], selectable=True)),
					ft.DataCell(
						ft.Container(
							content=ft.ElevatedButton(
								text="Удалить",
								icon=ft.Icons.DELETE,
								on_click=lambda e: self.delete_category(category=category)
							),
							alignment=ft.alignment.center_right,
							expand=True, 
						)
					)
				]
			)
		)
		self.page.update()

	""" Load list of available categories from server """
	def load_categories(self, e=None):
		resp = requests.get(f'{self.page.ROOT_URL}/categories', headers=self.page.request_headers)
		if resp.status_code in [200, 204]:
			self.table.rows.clear()
			self.page.categories = resp.json()
			for category in self.page.categories:
				self.add_row(category)
			print("Loaded categories")

	def delete_category(self, e=None, category=None):
		if any([category["category"]==item["category"] for item in self.page.loaded_items]):
			utils.show_dialog(self, "Категория используется!", "Нельзя удалить категорию, которая используется одним или более объектом")
			return
		id = category["id"]
		response = requests.delete(f"{self.page.ROOT_URL}/delete-category/{id}",  headers=self.page.content_provided_request_headers)
		print(response)
		if response.status_code in (200, 204):
			print(f"=> Deleted category id={id}")
			utils.show_dialog(self, "Категория удалена", "Данные таблицы обновлены")
			self.load_categories()
