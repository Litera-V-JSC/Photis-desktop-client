import flet as ft
from views.login_view import LoginView
from views.items_view import ItemsView
from views.item_edit_view import ItemEditView
from views.category_view import CategoryView
from views.user_view import UserView
from views.new_item_view import NewItemView
import os
import sys
import json
import urllib.parse


def main(page: ft.Page):
	# load app config
	with open(os.path.join(os.path.dirname(__file__), "client_app_config.json")) as file:
		config = json.load(file)
		page.ROOT_URL = config["ROOT_URL"] # root url for requests to API
		page.TIMER_RATE = config["TIMER_RATE"]
		page.THEME = config["THEME"]
		print(f"<*> Startup params: theme={page.THEME}, timer rate={page.TIMER_RATE}, root url={page.ROOT_URL}")
		
		page.STORAGE_PATH = config["STORAGE_PATH"]
		if page.STORAGE_PATH == "":
			print("> Parameter STORAGE_PATH is not set - creating new storage...")
			page.STORAGE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'storage'))

		page.TEMP_STORAGE_PATH = os.path.join(page.STORAGE_PATH, 'temp')

		os.makedirs(page.TEMP_STORAGE_PATH, exist_ok=True)

		print(f"> Created TEMP storage: {page.TEMP_STORAGE_PATH}")


	# setting app theme
	try:
		with open(os.path.join(os.path.dirname(__file__), "lib", "themes.json")) as file:
			page.theme = ft.Theme(color_scheme_seed=json.load(file)[page.THEME])
	except Exception as e:
		# default theme
		page.theme = ft.Theme(color_scheme_seed='#D4E9F7')
	page.theme_mode=ft.ThemeMode.LIGHT

	page.window.prevent_close = True
	page.window.icon = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")

	page.vertical_alignment = ft.MainAxisAlignment.CENTER
	page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

	page.title = "ItemScanner"
	# needed for correct views work according to account rights 
	page.current_session_username = None 
	page.current_session_admin = None
	# needed for requests to api
	page.token = None
	page.request_headers = None
	# for requests that send json data
	page.content_provided_request_headers = None
	# stroring loaded objects
	page.loaded_items = None
	page.filtered_items = None 
	page.categories = []

	def on_close(e: ft.ControlEvent):
		if e.data == "close":
			# Removing temp files
			print("> Application is closing. Performing cleanup...")
			count = 0
			start_count = len(os.listdir(page.TEMP_STORAGE_PATH))
			for item_name in os.listdir(page.TEMP_STORAGE_PATH):
				item_path = os.path.join(page.TEMP_STORAGE_PATH, item_name)
				if os.path.isfile(item_path):
					os.remove(item_path)
					count += 1
			print(f": Removed {count} of {start_count} files")
			
			page.window.prevent_close = False
			page.window.on_event = None  
			page.update()
			page.window.close() 

	def parse_edit_view_params():
		parsed = urllib.parse.urlparse(page.route)
		params = urllib.parse.parse_qs(parsed.query)

		id = urllib.parse.unquote(params.get("id", [""])[0])
		img = urllib.parse.unquote(params.get("img", [""])[0])
		category = urllib.parse.unquote(params.get("category", [""])[0])
		date = urllib.parse.unquote(params.get("date", [""])[0])
		sum = urllib.parse.unquote(params.get("sum", [""])[0])

		return [id, img, category, date, sum]


	def route_change(route):
		print(f"- {page.route}")
		page.views.clear()
		if page.route == '/login':
			page.views.append(LoginView(page))
		elif page.route == "/items":
			page.views.append(ItemsView(page))
		elif page.route == "/newitem":
			page.views.append(NewItemView(page))
		elif page.route.startswith("/edititem"):
			page.views.append(ItemEditView(page, *parse_edit_view_params()))
		elif page.route == "/category":
			page.views.append(CategoryView(page))
		elif page.route == "/user":
			page.views.append(UserView(page))
		page.update()
			

	def view_pop(view):
		page.views.pop()
		top_view = page.views[-1]
		page.go(top_view.route)
	print("> Views routing created")

	page.window.on_event = on_close

	page.on_route_change = route_change
	page.on_view_pop = view_pop
	page.go("/login")
	print("> Ready to work", '\n', '-'*8)


if __name__ == "__main__":
	ft.app(main)
	