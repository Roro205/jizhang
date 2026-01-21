import flet as ft

def main(page: ft.Page):
    page.title = "Roro记账"
    page.bgcolor = "#6C5CE7"
    
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("🐰", size=80),
                ft.Text("Roro记账", size=32, color="white", weight=ft.FontWeight.BOLD),
                ft.Text("APP启动成功！", size=16, color="white"),
                ft.Container(height=30),
                ft.ElevatedButton(
                    "点击测试",
                    on_click=lambda e: page.add(ft.Text("按钮可用！", color="white"))
                ),
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.alignment.center,
        )
    )

ft.app(target=main)
