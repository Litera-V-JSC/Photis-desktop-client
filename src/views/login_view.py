from .base_view import BaseView
import flet as ft
import requests

class LoginView(BaseView):
	def __init__(self, page: ft.Page):
		super().__init__(page=page, view_route="/login", on_exit_view_path='/items')

		self.username = ft.TextField(label="Логин", width=300)
		self.password = ft.TextField(label="Пароль", width=300, password=True, can_reveal_password=True)
		self.result_text = ft.Text()
		self.login_button = ft.ElevatedButton(text="Войти", on_click=self.login_click)

		form = ft.Column(
			[
				ft.Text("Вход в систему", size=24, weight=ft.FontWeight.BOLD),
				self.username,
				self.password,
				self.login_button,
				self.result_text,
			],
			alignment=ft.MainAxisAlignment.CENTER,
			horizontal_alignment=ft.CrossAxisAlignment.CENTER,
			spacing=10,
			expand=False,
		)
		container = ft.Container(
			content=form,
			alignment=ft.alignment.center,
			expand=True,
		)

		self.controls.append(container)
	

	""" Login button handler """
	def login_click(self, e):
		credentials = {
			'username': self.username.value.strip(),
			'password': self.password.value.strip()
		}
		self.result_text.value = "Выполняется вход..."
		self.result_text.update()
		resp = requests.get(f'{self.page.ROOT_URL}/login', json=credentials)

		if resp.status_code in (200, 204):
			token = resp.json()['access_token']
			user_data = resp.json()['user_data']
			self.page.current_session_username = user_data['username']
			self.page.current_session_admin = user_data['admin']
			self.page.request_headers = {'Authorization': f'Bearer {token}'}
			self.page.content_provided_request_headers = {
				'Content-Type': 'application/json',
				'Authorization': f'Bearer {token}'
			}
			self.result_text.value = "Успешный вход!"
			print("> Login : success")
			self.page.go("/items")
		else:
			print("> Login : invalid user data")
			self.result_text.value = "Неверный логин или пароль"
		self.update()