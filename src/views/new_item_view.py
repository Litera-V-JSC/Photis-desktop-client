from .base_view import BaseView
import flet as ft
import requests
import json
import os
import datetime
import base64
from lib import utils
from lib.stream import Stream
from lib.timer import Timer


class NewItemView(ft.View):
	def __init__(self, page: ft.Page):
		super().__init__(route='/newitem')
		self.page = page
		self.stream = Stream()

		self.file_picker = ft.FilePicker(on_result=lambda e: utils.file_picked(self, e))
		self.page.overlay.append(self.file_picker)
		self.file_path = None

		self.appbar = ft.AppBar(
			leading=ft.IconButton(
				icon=ft.Icons.ARROW_BACK,
				tooltip="Назад",
				on_click=self.on_exit
			),
			title=ft.Text("Добавление"),
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
			width=200
		)
		self.date_field = ft.TextField(
			label="Дата",
			width=200,
			value=datetime.date.today().strftime('%d.%m.%Y'),
		)

		self.file_name_text = ft.Text("Файл не выбран", italic=True, size=12)

		self.attach_button = ft.ElevatedButton(
			"Прикрепить изображение",
			on_click=lambda e : utils.pick_file(self, e)
		)

		self.submit_button = ft.ElevatedButton(
			"Отправить",
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

		# Правая колонка — видеопоток
		self.photo_label = ft.Text("Новая фотография", size=16)

		# Контейнер для видео/плейсхолдера
		self.photo_placeholder = ft.Container(
			width=300,
			height=300,
			bgcolor=ft.Colors.GREY_800,
			border_radius=8,
			alignment=ft.alignment.center,
		)

		# Кнопка "Сделать фото"
		self.photo_button = ft.ElevatedButton(
			"Сделать фото",
			icon=ft.Icons.PHOTO_CAMERA,
			on_click=self.take_photo,
			disabled = True
		)

		# Кнопка для старта стрима с камеры
		self.toggle_camera_button = ft.ElevatedButton(
			"Включить камеру",
			on_click=self.toggle_camera
		)

		self.photo_column = ft.Column(
			controls=[
				self.photo_label,
				self.photo_placeholder,
				ft.Row(
					controls=[
						self.photo_button,
						self.toggle_camera_button
					],
					alignment=ft.MainAxisAlignment.CENTER,
					spacing=50,
				)
			],
			spacing=15,
			alignment=ft.MainAxisAlignment.START,
			horizontal_alignment=ft.CrossAxisAlignment.CENTER,
			# width=220,
		)

		# Основной контейнер — горизонтальный ряд из двух колонок
		self.main_row = ft.Column(
			controls=[ft.Row(
			controls=[
				self.form,
				self.photo_column,
			],
			alignment=ft.MainAxisAlignment.CENTER,
			spacing=50,
		)],
			alignment=ft.MainAxisAlignment.CENTER,
			horizontal_alignment=ft.CrossAxisAlignment.CENTER,
			spacing=10,
			expand=True,
			scroll=ft.ScrollMode.AUTO
		)

		self.controls.append(self.appbar)
		self.controls.append(self.main_row)

		self.page.dialog = ft.AlertDialog(
			title=ft.Container(ft.Text(""), alignment=ft.alignment.center),
			content=ft.Text(""),
			actions=[
				ft.TextButton("OK", on_click=lambda e: utils.close_dialog(self))
			],
			actions_alignment=ft.MainAxisAlignment.CENTER,
		)

		# timer to update frames from video stream
		self.camera_on = False
		self.cap_timer = Timer(self.page.TIMER_RATE, self.update_frame)
		self.cap_timer.start()
		# timer to check submit form data
		self.check_timer = Timer(0.002, self.check_fieds_data)
		self.check_timer.start()

	""" Check fields data to enable submit button """
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
				pass

	""" Release camera """
	def close_camera_connection(self):
		self.camera_on = False
		self.stream.release()
		self.photo_placeholder.content = None
		self.photo_placeholder.width = 400
		self.photo_placeholder.height = 400
		self.photo_placeholder.update()

	""" Open or close camera stream """
	def toggle_camera(self, e=None):
		if not self.camera_on:
			print("Camera stream started")
			if not self.stream.available:
				self.stream.create_stream() 
			self.camera_on = True
			self.photo_button.disabled = False
			self.toggle_camera_button.text = "Выключить камеру"
		else:
			print("Camera stream stopped")
			self.close_camera_connection()
			self.photo_button.disabled = True
			self.toggle_camera_button.text = "Включить камеру"
		self.photo_button.update()
		self.toggle_camera_button.update()

	""" Activates on page exit. Releases camera, stops update-frame timer and removes temp files """
	def on_exit(self, e=None):
		self.close_camera_connection()
		self.cap_timer.stop()
		self.check_timer.stop()
		if not self.file_path is None:
			os.remove(self.file_path)
		print(f"Cap released. Temp files removed")
		self.page.go("/items")
		
	""" Update frame in photo_placeholder """
	def update_frame(self, e=None):
		if not self.camera_on: 
			return

		frame_base64 = self.stream.get_frame()
		if frame_base64:
			# Creating base64 image and put it into placeholder
			frame_shape = utils.clamp_shape(self.stream.frame_shape)
			self.photo_placeholder.width = frame_shape[1]
			self.photo_placeholder.height = frame_shape[0]
			self.photo_placeholder.content = ft.Image(
				src_base64=frame_base64,
				width=self.photo_placeholder.width,
				height=self.photo_placeholder.height,
				fit=ft.ImageFit.CONTAIN,
			)

		self.photo_placeholder.update()

	""" Make photo and save it to local storage """
	def take_photo(self, e):
		frame_base64 = self.stream.get_frame()
		if frame_base64:
			print("Made photo")
			utils.show_dialog(self, "Фото сделано!", "Фотография была прикреплена к форме отправки")
			
			filename = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.png'
			utils.upload_file_base64(frame_base64, os.path.join(self.page.STORAGE_PATH, 'temp', filename))
			utils.update_attachment_data(self, os.path.join(self.page.STORAGE_PATH, 'temp', filename), filename, frame_base64, "screenshot")
		else:
			print("Base64 converting error, photo was not made")
			utils.show_dialog(self, "Ошибка", "Некорректный источник")
		self.page.update()

	""" Submit data from item creation form """
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

		new_item = json.dumps({
			"category": category,
			"sum": sum_float,
			"creation_date": date_,
			"image": img_base64
		})
		response = requests.post(f'{self.page.ROOT_URL}/add-item', data=new_item, headers=self.page.content_provided_request_headers)
		print(response)
		utils.show_dialog(self, "Объект сохранен", "Чтобы увидеть изменения, перезагрузите страницу")
		self.page.update()