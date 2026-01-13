from .base_view import BaseView
import flet as ft
import requests
from lib import utils, controls
import urllib.parse
import datetime
import os


class ItemsView(BaseView):
	def __init__(self, page: ft.Page):
		super().__init__(page=page, view_route="/items")

		# Info panel with items count
		self.item_count = ft.Text(value=f"Всего позиций: 0")

		# Blank table for items
		self.table = ft.DataTable(
			columns=[
				ft.DataColumn(ft.Text("Дата")),
				ft.DataColumn(ft.Text("Категория")),
				ft.DataColumn(ft.Text("Сумма")),
				ft.DataColumn(ft.Text("Фото")),
				ft.DataColumn(ft.Text("")),
				ft.DataColumn(ft.Text("")),
			],
			rows=[],
			expand=True
		)
		
		self.controls.append(ft.AppBar(title=ft.Text("База данных"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST))
		self.start_filter_field = ft.TextField(label="Начальная дата")
		self.end_filter_field = ft.TextField(label="Конечная дата")
		self.minimum_sum_field = ft.TextField(label="Минимальная сумма")
		self.maximum_sum_field = ft.TextField(label="Максимальная сумма")
		self.category_dropdown = ft.Dropdown(
				label="Категория",
				options=[ft.dropdown.Option("", "Все")] + [ft.dropdown.Option(c["category"]) for c in self.load_categories(return_categories=True)],
				value="Все"
		)
		self.reload_button = ft.IconButton(
			icon=ft.Icons.REFRESH,
			tooltip="Reload",
			on_click=self.reset_filter
		)
		self.category_button = ft.ElevatedButton(
			"Категории", 
			icon=ft.Icons.CATEGORY, 
			on_click=lambda e: self.page.go('/category')
		)
		self.user_button = ft.ElevatedButton(
			"Пользователи", 
			icon=ft.Icons.PERSON, 
			on_click=lambda e: self.page.go('/user')
		)
		
		is_admin = self.page.current_session_admin
		self.controls.append(
			ft.Column([
				ft.Row([
					self.category_button if is_admin else ft.Row([]),
					self.user_button if is_admin else ft.Row([]),
					ft.ElevatedButton(
						"Сформировать отчет", 
						on_click=self.get_report
					),
					ft.ElevatedButton(
						"Добавить объект", 
						on_click=lambda e: self.page.go('/newitem')
					),
					self.reload_button
				]),
				ft.Row([
					ft.Column([
						ft.Row([
							self.category_dropdown,
							self.start_filter_field,
							self.end_filter_field
						]),
						ft.Row([
							self.minimum_sum_field,
							self.maximum_sum_field,
							ft.ElevatedButton(
								"Отфильтровать", 
								on_click=self.apply_filter
							)
						])
					])
					
				]),
			])
		)
		

		self.controls.append(self.item_count)
		
		self.controls.append(ft.ListView(controls=[self.table], expand=True, height=400))
		self.page.dialog = ft.AlertDialog(
			title=ft.Container(ft.Text(""), alignment=ft.alignment.center),
			content=ft.Text(""),
			actions=[
				ft.TextButton("OK", on_click=lambda e: utils.close_dialog(self))
			],
			actions_alignment=ft.MainAxisAlignment.CENTER,
		)

		self.load_items()

	""" Add item row to table """
	def add_row(self, item):
		date_ = utils.date_to_text(item['creation_date'])

		def on_photo_click(e):
			img_path = urllib.parse.quote(os.path.join(self.page.STORAGE_PATH, 'temp', item['file_name']))
			utils.open_image(img_path)

		self.table.rows.append(
			ft.DataRow(
				cells=[
					ft.DataCell(ft.Text(date_, selectable=True)),
					ft.DataCell(ft.Text(item['category'], selectable=True)),
					ft.DataCell(ft.Text(item['sum'], selectable=True)),
					controls.ClickableDatacell( 
						text='Посмотреть фото', 
						on_tap=on_photo_click
					),
					ft.DataCell(ft.ElevatedButton(
						text="Удалить",
						icon=ft.Icons.DELETE, 
						on_click=lambda e: self.delete_item(id=item['id'])
					)),
						ft.DataCell(ft.ElevatedButton(
						text="Редактировать",
						icon=ft.Icons.EDIT, 
						on_click=lambda e: self.edit_item(item=item)
					))
				],
			)
		)
		self.page.update()


	def delete_item(self, e=None, id=None):
		response = requests.delete(f"{self.page.ROOT_URL}/delete-item/{int(id)}",  headers=self.page.content_provided_request_headers)
		print('-', response)
		if response.status_code in (200, 204):
			print(f"Deleted item id={id}")
			self.page.filtered_items = None
			self.page.loaded_items = None
			self.page.go("/items")


	def edit_item(self, e=None, item=None):
		img_path = urllib.parse.quote(os.path.join(self.page.STORAGE_PATH, 'temp', item['file_name']))
		category = urllib.parse.quote(item['category'])
		id_ = urllib.parse.quote(str(item['id']))
		date = urllib.parse.quote(str(item['creation_date']))
		sum_ = urllib.parse.quote(str(item['sum']))
		route = f"/edititem?id={id_}&img={img_path}&category={category}&date={date}&sum={sum_}"
		self.page.go(route)


	""" 
	Load list of available categories from server
	return_categories (boolean) - return list of categories as result
	"""
	def load_categories(self, return_categories=False):
		resp = requests.get(f'{self.page.ROOT_URL}/categories', headers=self.page.request_headers)
		if resp.status_code in [200, 204]:
			self.page.categories = resp.json()
			if return_categories: 
				return resp.json()

	""" Load file image from server and save it to local storage """
	def load_photo(self, item):
		resp = requests.get(f"{self.page.ROOT_URL}/files/{item['id']}", headers=self.page.request_headers)
		with open(os.path.join(self.page.STORAGE_PATH, 'temp', item['file_name']), 'wb') as f:
			f.write(resp.content)

	""" Load items from buffer and add them to table """
	def load_items(self):
		self.table.rows.clear()
		if self.page.loaded_items is None:
			self.load_all_items()
			current_items = self.page.loaded_items
		else:
			if self.page.filtered_items is None: 
				current_items = self.page.loaded_items
			else:
				current_items = self.page.filtered_items
			
			for item in current_items:
				self.add_row(item)

		self.page.update()
		self.update_count(current_items)

	""" Get list of all items from server """
	def load_all_items(self):
		resp = requests.get(f'{self.page.ROOT_URL}/item/all', headers=self.page.request_headers)
		if resp.status_code in [200, 204]:
			loaded_items = []
			for item in resp.json():
				loaded_items.append(item)
				self.load_photo(item)
			self.page.loaded_items = loaded_items
			for item in self.page.loaded_items:
				self.add_row(item)
		print("> Loaded all available items")

	""" Reset filter fields and updates items table """
	def reset_filter(self, e=None):
		self.start_filter_field.value = None
		self.end_filter_field.value = None
		self.minimum_sum_field.value = None
		self.maximum_sum_field.value = None
		self.category_dropdown.value = "Все"
		self.page.filtered_items = None
		self.page.loaded_items = None
		self.load_items()
		print("> Filter reset")

	""" Get item filtered by date """	
	def apply_filter(self, e):
		start = utils.date_to_sql(self.start_filter_field.value)
		end = utils.date_to_sql(self.end_filter_field.value)

		minimum_sum = self.minimum_sum_field.value
		maximum_sum = self.maximum_sum_field.value
		minimum_sum = int(minimum_sum) if minimum_sum != '' else 0
		maximum_sum = int(maximum_sum) if maximum_sum != '' else float('inf')

		category = self.category_dropdown.value
		if category == "Все": 
			category = None

		if category in [None, "Все"] and start == end == None and minimum_sum == 0 and maximum_sum == float('inf'):
			print("> Filter not applied : parameters not set")
			return

		filtered = utils.get_filtered_items(self.page.loaded_items, start, end, minimum_sum, maximum_sum, category)
		self.page.filtered_items = filtered
		self.load_items()


	""" 
	Get report from server.
	Uses filtered items, 
	otherwise returns report about all items 
	"""
	def get_report(self, e):
		if self.page.filtered_items is None:
			items = self.page.loaded_items
		else:
			items = self.page.filtered_items
		id_list = json.dumps({
			"id_list": [int(item['id']) for item in items]
		})
		resp = requests.get(f'{self.page.ROOT_URL}/report', data=id_list, headers=self.page.content_provided_request_headers)
		print(resp)
		if resp.status_code in [200, 204]:
			filename = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.pdf'
			path = os.path.join(self.page.STORAGE_PATH, filename)
			with open(path, 'wb') as f:
				f.write(resp.content)
				utils.show_dialog(self, text="Отчет сформирован", desc=f"Путь к файлу: {path}")
				print("> Report loaded")

	def update_count(self, items):
		try:
			self.item_count.value = f"Всего позиций: {len(items)}"
			self.item_count.update()
		except Exception as e:
			pass
