from .base_view import BaseView
import flet as ft
from lib import utils, controls
import requests
import json


class UserView(BaseView):
	def __init__(self, page: ft.Page):
		super().__init__(page=page, view_route='/user', on_exit_view_path='/items')
		self.page = page
		self.username_field = ft.TextField(label="Имя пользователя", width=300)
		self.password_field = ft.TextField(label="Пароль", width=300)
		self.admin_rights_dropdown = ft.Dropdown(
				label="Администратор",
				options=[ft.dropdown.Option(1, "Да"), ft.dropdown.Option(0, "Нет")],
				width=200
		)
		self.add_button = ft.ElevatedButton(text="Добавить", on_click=self.add_user)
		self.reload_button = ft.IconButton(
			icon=ft.Icons.REFRESH,
			tooltip="Reload",
			on_click=self.load_users
		)

		# AppBar
		self.appbar = ft.AppBar(
			leading=ft.IconButton(
				icon=ft.Icons.ARROW_BACK,
				tooltip="Назад",
				on_click=self.on_exit
			),
			title=ft.Text("Список пользователей"),
			bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
		)

		# Blank table for items
		self.table = ft.DataTable(
			columns=[
				ft.DataColumn(ft.Text("Имя пользователя")),
				ft.DataColumn(ft.Text("Права администратора")),
				ft.DataColumn(ft.Text(""))
			],
			rows=[],
			expand=True
		)

		self.main_content = ft.Column(
			controls=[
				ft.Row(
					controls=[
						self.username_field,
						self.password_field,
						self.admin_rights_dropdown,
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

		self.load_users()

	""" Add new user to db """
	def add_user(self, e=None):
		username = self.username_field.value
		password = self.password_field.value
		admin = self.admin_rights_dropdown.value
		if not str(username).isalnum() or not str(password).isalnum() or int(admin) not in [0, 1]:
			print(f"Wrong input data format")
			utils.show_dialog(self, "Заполните данные!", "Проверьте, что в каждом поле указано значение")
		else:
			new_user = json.dumps({
				"username": username,
				"password": password,
				"admin": int(admin)
			})
			response = requests.post(f'{self.page.ROOT_URL}/add-user', data=new_user, headers=self.page.content_provided_request_headers)
			print(response)
			if response.status_code in (200, 204):
				utils.show_dialog(self, "Пользователь сохранен", "Данные таблицы обновлены")
				self.load_users()
				self.page.update()
			else:
				utils.show_dialog(self, "Ошибка!", "Пользователь с таким именем уже существует")
		
	
	""" Add item row to table """
	def add_row(self, user):
		username = user["username"]
		if user["admin"] == 0:
			admin = 'Нет'
		else:
			admin = 'Да'
		self.table.rows.append(
			ft.DataRow(
				cells=[
					ft.DataCell(ft.Text(username, selectable=True)),
					ft.DataCell(ft.Text(admin, selectable=False)),
					ft.DataCell(
						ft.Container(
							content=ft.ElevatedButton(
								text="Удалить",
								icon=ft.Icons.DELETE,
								on_click=lambda e: self.delete_user(username=username)
							),
							alignment=ft.alignment.center_right,
							expand=True, 
						)
					)
				]
			)
		)
		self.page.update()

	""" Load list of active users from server """
	def load_users(self, e=None):
		resp = requests.get(f'{self.page.ROOT_URL}/users', headers=self.page.request_headers)
		if resp.status_code in [200, 204]:
			self.table.rows.clear()
			for user in resp.json():
				self.add_row(user)
			print("Loaded users")

	def delete_user(self, e=None, username=None):
		if username == self.page.current_session_username:
			utils.show_dialog(self, "Ошибка!", "Нельзя удалить данные пользователя, который используется вами в данный момент")
			return
		response = requests.delete(f"{self.page.ROOT_URL}/delete-user/{username}",  headers=self.page.content_provided_request_headers)
		print(response)
		if response.status_code in (200, 204):
			print(f"=> Deleted user = {username}")
			utils.show_dialog(self, "Пользователь удален", "Данные таблицы обновлены")
			self.load_users()
	