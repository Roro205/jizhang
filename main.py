import flet as ft
from datetime import datetime
import json
import os
import traceback


def main(page: ft.Page):
    page.title = "Roro记账"
    page.bgcolor = "#F5F5F5"
    page.padding = 0
    page.spacing = 0
    
    # 适配手机全屏
    page.window.width = 400
    page.window.height = 800
    
    PRIMARY = "#6C5CE7"
    INCOME = "#00B894"
    EXPENSE = "#E17055"
    
    # 获取安全区域（适配刘海屏）
    safe_area_top = 40  # 顶部安全距离
    safe_area_bottom = 20  # 底部安全距离
    
    def show_error(e):
        page.controls.clear()
        page.add(
            ft.Container(
                ft.Column([
                    ft.Text("出错了", size=24, color="white"),
                    ft.Container(height=20),
                    ft.Text(str(e), size=12, color="white"),
                ], scroll=ft.ScrollMode.AUTO),
                bgcolor="#E74C3C",
                padding=20,
                expand=True,
            )
        )
        page.update()
    
    try:
        class DataManager:
            def __init__(self):
                self.data_file = "roro_data.json"
                self.data = self.load_data()
            
            def get_data_path(self):
                try:
                    storage = os.environ.get('FLET_APP_STORAGE_DATA')
                    if storage:
                        os.makedirs(storage, exist_ok=True)
                        return os.path.join(storage, self.data_file)
                except:
                    pass
                return self.data_file
            
            def load_data(self):
                try:
                    path = self.get_data_path()
                    if os.path.exists(path):
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if "records" not in data:
                                data["records"] = []
                            if "categories" not in data:
                                data["categories"] = self.default_categories()
                            return data
                except:
                    pass
                return {"records": [], "categories": self.default_categories()}
            
            def default_categories(self):
                return {
                    "支出": [
                        {"name": "餐饮", "icon": "🍜", "color": "#FF6B6B"},
                        {"name": "交通", "icon": "🚗", "color": "#4ECDC4"},
                        {"name": "购物", "icon": "🛒", "color": "#45B7D1"},
                        {"name": "娱乐", "icon": "🎮", "color": "#96CEB4"},
                        {"name": "居住", "icon": "🏠", "color": "#FFEAA7"},
                        {"name": "其他", "icon": "💡", "color": "#95A5A6"},
                    ],
                    "收入": [
                        {"name": "工资", "icon": "💰", "color": "#4ECDC4"},
                        {"name": "奖金", "icon": "🎁", "color": "#F39C12"},
                        {"name": "兼职", "icon": "💼", "color": "#3498DB"},
                        {"name": "其他", "icon": "💡", "color": "#95A5A6"},
                    ]
                }
            
            def save_data(self):
                try:
                    path = self.get_data_path()
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(self.data, f, ensure_ascii=False)
                except:
                    pass
            
            def add_record(self, rtype, amount, category, icon, note, date):
                self.data["records"].append({
                    "id": datetime.now().timestamp(),
                    "type": rtype,
                    "amount": amount,
                    "category": category,
                    "icon": icon,
                    "note": note,
                    "date": date,
                })
                self.save_data()
            
            def delete_record(self, rid):
                self.data["records"] = [r for r in self.data["records"] if r.get("id") != rid]
                self.save_data()
            
            def get_today_records(self):
                today = datetime.now().strftime("%Y-%m-%d")
                return [r for r in self.data["records"] if r.get("date") == today]
            
            def get_month_summary(self):
                now = datetime.now()
                prefix = f"{now.year}-{now.month:02d}"
                records = [r for r in self.data["records"] if r.get("date", "").startswith(prefix)]
                income = sum(r.get("amount", 0) for r in records if r.get("type") == "收入")
                expense = sum(r.get("amount", 0) for r in records if r.get("type") == "支出")
                return {"income": income, "expense": expense, "balance": income - expense}
        
        dm = DataManager()
        
        current_type = "支出"
        current_cat = None
        current_icon = None
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # ========== 首页 ==========
        def build_home():
            summary = dm.get_month_summary()
            records = dm.get_today_records()
            
            def delete_r(rid):
                dm.delete_record(rid)
                refresh_all()
            
            record_items = []
            for r in reversed(records):
                is_exp = r.get("type") == "支出"
                record_items.append(
                    ft.Container(
                        ft.Row([
                            ft.Container(
                                ft.Text(r.get("icon", "💰"), size=20),
                                width=40,
                                height=40,
                                bgcolor="#F5F5F5",
                                border_radius=10,
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Container(width=10),
                            ft.Column([
                                ft.Text(r.get("category", ""), size=14, weight=ft.FontWeight.W_500),
                                ft.Text(r.get("note", "") or "无备注", size=11, color="#888"),
                            ], spacing=2, expand=True),
                            ft.Text(
                                f"{'−' if is_exp else '+'} ¥{r.get('amount', 0):.2f}",
                                color=EXPENSE if is_exp else INCOME,
                                weight=ft.FontWeight.BOLD,
                                size=15,
                            ),
                            ft.IconButton(
                                icon="close",
                                icon_size=16,
                                icon_color="#CCC",
                                on_click=lambda e, rid=r.get("id"): delete_r(rid),
                            ),
                        ]),
                        bgcolor="white",
                        padding=ft.Padding(12, 10, 8, 10),
                        border_radius=12,
                        margin=ft.Margin(0, 0, 0, 8),
                    )
                )
            
            if not record_items:
                record_items = [
                    ft.Container(
                        ft.Column([
                            ft.Text("📝", size=40),
                            ft.Container(height=10),
                            ft.Text("今日暂无记录", color="#999", size=14),
                            ft.Text("点击下方按钮开始记账", color="#CCC", size=12),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                        padding=50,
                        alignment=ft.Alignment(0, 0),
                    )
                ]
            
            return ft.Container(
                ft.Column([
                    # 顶部卡片区域
                    ft.Container(
                        ft.Column([
                            # 安全区域占位
                            ft.Container(height=safe_area_top),
                            # 标题
                            ft.Row([
                                ft.Column([
                                    ft.Text("Roro记账", size=24, weight=ft.FontWeight.BOLD, color="white"),
                                    ft.Text(datetime.now().strftime("%Y年%m月"), size=13, color="#FFFFFFBB"),
                                ], spacing=2),
                            ]),
                            ft.Container(height=20),
                            # 汇总卡片
                            ft.Container(
                                ft.Row([
                                    ft.Column([
                                        ft.Text("支出", size=12, color="#888"),
                                        ft.Container(height=5),
                                        ft.Text(f"¥{summary['expense']:.2f}", size=20, weight=ft.FontWeight.BOLD),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                                    ft.Container(width=1, height=40, bgcolor="#EEE"),
                                    ft.Column([
                                        ft.Text("收入", size=12, color="#888"),
                                        ft.Container(height=5),
                                        ft.Text(f"¥{summary['income']:.2f}", size=20, weight=ft.FontWeight.BOLD, color=INCOME),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                                    ft.Container(width=1, height=40, bgcolor="#EEE"),
                                    ft.Column([
                                        ft.Text("结余", size=12, color="#888"),
                                        ft.Container(height=5),
                                        ft.Text(f"¥{summary['balance']:.2f}", size=20, weight=ft.FontWeight.BOLD,
                                               color=INCOME if summary['balance'] >= 0 else EXPENSE),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                                ]),
                                bgcolor="white",
                                padding=ft.Padding(15, 20, 15, 20),
                                border_radius=16,
                            ),
                        ]),
                        gradient=ft.LinearGradient(
                            colors=[PRIMARY, "#A29BFE"],
                            begin=ft.Alignment(-1, -1),
                            end=ft.Alignment(1, 1),
                        ),
                        padding=ft.Padding(20, 0, 20, 25),
                        border_radius=ft.BorderRadius(0, 0, 30, 30),
                    ),
                    # 今日记录标题
                    ft.Container(
                        ft.Row([
                            ft.Text("今日记录", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text(datetime.now().strftime("%m/%d"), size=13, color="#999"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=ft.Padding(20, 20, 20, 10),
                    ),
                    # 记录列表
                    ft.Container(
                        ft.Column(record_items, spacing=0),
                        padding=ft.Padding(15, 0, 15, 0),
                        expand=True,
                    ),
                    # 底部占位（导航栏高度 + 安全区域）
                    ft.Container(height=70 + safe_area_bottom),
                ], spacing=0),
                expand=True,
                bgcolor="#F5F5F5",
            )
        
        # ========== 记账页 ==========
        def build_add():
            nonlocal current_type, current_cat, current_icon, current_date
            
            amount_field = ft.TextField(
                hint_text="0.00",
                text_align=ft.TextAlign.CENTER,
                text_size=36,
                keyboard_type=ft.KeyboardType.NUMBER,
                border=ft.InputBorder.NONE,
                color="white",
                hint_style=ft.TextStyle(color="#FFFFFF66", size=36),
            )
            note_field = ft.TextField(
                hint_text="添加备注...",
                border_radius=12,
                bgcolor="white",
                border_color="#EEE",
            )
            date_text = ft.Text(current_date, color="white", size=14)
            
            exp_text = ft.Text("支出", size=16, weight=ft.FontWeight.BOLD, color="white")
            inc_text = ft.Text("收入", size=16, color="#FFFFFF88")
            
            cat_grid = ft.GridView(
                runs_count=4,
                spacing=15,
                run_spacing=15,
                child_aspect_ratio=0.85,
                expand=True,
                padding=10,
            )
            
            def switch_type(t):
                nonlocal current_type, current_cat, current_icon
                current_type = t
                current_cat = None
                current_icon = None
                if t == "支出":
                    exp_text.color = "white"
                    exp_text.weight = ft.FontWeight.BOLD
                    inc_text.color = "#FFFFFF88"
                    inc_text.weight = None
                else:
                    inc_text.color = "white"
                    inc_text.weight = ft.FontWeight.BOLD
                    exp_text.color = "#FFFFFF88"
                    exp_text.weight = None
                load_categories()
                page.update()
            
            def load_categories():
                cats = dm.data["categories"].get(current_type, [])
                cat_grid.controls.clear()
                for c in cats:
                    if not isinstance(c, dict):
                        continue
                    selected = current_cat == c.get("name")
                    cat_grid.controls.append(
                        ft.Container(
                            ft.Column([
                                ft.Container(
                                    ft.Text(c.get("icon", "💰"), size=28),
                                    width=55,
                                    height=55,
                                    bgcolor=c.get("color", "#999") if selected else c.get("color", "#999") + "25",
                                    border_radius=15,
                                    alignment=ft.Alignment(0, 0),
                                ),
                                ft.Container(height=5),
                                ft.Text(
                                    c.get("name", ""),
                                    size=12,
                                    color="#333" if selected else "#888",
                                    weight=ft.FontWeight.W_500 if selected else None,
                                ),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                            on_click=lambda e, cat=c: select_cat(cat),
                        )
                    )
            
            def select_cat(c):
                nonlocal current_cat, current_icon
                current_cat = c.get("name")
                current_icon = c.get("icon")
                load_categories()
                page.update()
            
            def save_record(e):
                nonlocal current_cat, current_icon
                if not amount_field.value:
                    page.snack_bar = ft.SnackBar(ft.Text("请输入金额", color="white"), bgcolor=EXPENSE)
                    page.snack_bar.open = True
                    page.update()
                    return
                if not current_cat:
                    page.snack_bar = ft.SnackBar(ft.Text("请选择分类", color="white"), bgcolor=EXPENSE)
                    page.snack_bar.open = True
                    page.update()
                    return
                try:
                    amt = float(amount_field.value)
                except:
                    page.snack_bar = ft.SnackBar(ft.Text("金额无效", color="white"), bgcolor=EXPENSE)
                    page.snack_bar.open = True
                    page.update()
                    return
                
                dm.add_record(current_type, amt, current_cat, current_icon or "💰", note_field.value or "", current_date)
                
                amount_field.value = ""
                note_field.value = ""
                current_cat = None
                current_icon = None
                load_categories()
                
                page.snack_bar = ft.SnackBar(ft.Text("✓ 保存成功", color="white"), bgcolor=INCOME)
                page.snack_bar.open = True
                refresh_all()
            
            # 快捷金额按钮
            quick_amounts = [10, 20, 50, 100, 200]
            
            def add_quick(amt):
                try:
                    current = float(amount_field.value or 0)
                    amount_field.value = str(current + amt)
                except:
                    amount_field.value = str(amt)
                page.update()
            
            quick_btns = ft.Row(
                [
                    ft.Container(
                        ft.Text(f"+{a}", size=13, color="white"),
                        bgcolor="#FFFFFF30",
                        padding=ft.Padding(12, 6, 12, 6),
                        border_radius=15,
                        on_click=lambda e, amt=a: add_quick(amt),
                    ) for a in quick_amounts
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            )
            
            load_categories()
            
            return ft.Container(
                ft.Column([
                    # 顶部输入区域
                    ft.Container(
                        ft.Column([
                            ft.Container(height=safe_area_top),
                            # 类型切换
                            ft.Row([
                                ft.Container(exp_text, on_click=lambda e: switch_type("支出"), padding=10),
                                ft.Container(inc_text, on_click=lambda e: switch_type("收入"), padding=10),
                            ], alignment=ft.MainAxisAlignment.CENTER, spacing=30),
                            ft.Container(height=20),
                            # 金额输入
                            ft.Row([
                                ft.Text("¥", size=30, color="#FFFFFF88"),
                                ft.Container(amount_field, expand=True),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Container(height=15),
                            # 快捷金额
                            quick_btns,
                            ft.Container(height=15),
                            # 日期显示
                            ft.Container(
                                ft.Row([
                                    ft.Icon("event", size=18, color="#FFFFFF88"),
                                    ft.Container(width=8),
                                    date_text,
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                bgcolor="#FFFFFF20",
                                padding=ft.Padding(20, 10, 20, 10),
                                border_radius=12,
                            ),
                        ]),
                        gradient=ft.LinearGradient(
                            colors=[PRIMARY, "#A29BFE"],
                            begin=ft.Alignment(0, -1),
                            end=ft.Alignment(0, 1),
                        ),
                        padding=ft.Padding(20, 0, 20, 25),
                        border_radius=ft.BorderRadius(0, 0, 30, 30),
                    ),
                    # 分类选择
                    ft.Container(
                        ft.Column([
                            ft.Text("选择分类", size=15, weight=ft.FontWeight.BOLD),
                            ft.Container(height=10),
                            cat_grid,
                        ]),
                        padding=ft.Padding(15, 20, 15, 0),
                        expand=True,
                    ),
                    # 备注和保存
                    ft.Container(
                        ft.Column([
                            note_field,
                            ft.Container(height=15),
                            ft.ElevatedButton(
                                "保存",
                                width=float("inf"),
                                height=50,
                                bgcolor=PRIMARY,
                                color="white",
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                ),
                                on_click=save_record,
                            ),
                        ]),
                        padding=ft.Padding(20, 10, 20, 80 + safe_area_bottom),
                    ),
                ], spacing=0),
                expand=True,
                bgcolor="#F5F5F5",
            )
        
        # ========== 设置页 ==========
        def build_settings():
            total = len(dm.data.get("records", []))
            exp = sum(r.get("amount", 0) for r in dm.data.get("records", []) if r.get("type") == "支出")
            inc = sum(r.get("amount", 0) for r in dm.data.get("records", []) if r.get("type") == "收入")
            
            def clear_data(e):
                dm.data["records"] = []
                dm.save_data()
                page.snack_bar = ft.SnackBar(ft.Text("数据已清空", color="white"), bgcolor="#F39C12")
                page.snack_bar.open = True
                refresh_all()
            
            return ft.Container(
                ft.Column([
                    # 顶部
                    ft.Container(
                        ft.Column([
                            ft.Container(height=safe_area_top),
                            ft.Text("设置", size=22, weight=ft.FontWeight.BOLD, color="white"),
                        ]),
                        gradient=ft.LinearGradient(
                            colors=[PRIMARY, "#A29BFE"],
                            begin=ft.Alignment(-1, -1),
                            end=ft.Alignment(1, 1),
                        ),
                        padding=ft.Padding(20, 0, 20, 25),
                        border_radius=ft.BorderRadius(0, 0, 30, 30),
                        alignment=ft.Alignment(0, 0),
                    ),
                    # 统计卡片
                    ft.Container(
                        ft.Row([
                            ft.Column([
                                ft.Text(f"{total}", size=26, weight=ft.FontWeight.BOLD, color=PRIMARY),
                                ft.Text("总记录", size=12, color="#888"),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                            ft.Container(width=1, height=50, bgcolor="#EEE"),
                            ft.Column([
                                ft.Text(f"¥{exp:.0f}", size=26, weight=ft.FontWeight.BOLD, color=EXPENSE),
                                ft.Text("总支出", size=12, color="#888"),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                            ft.Container(width=1, height=50, bgcolor="#EEE"),
                            ft.Column([
                                ft.Text(f"¥{inc:.0f}", size=26, weight=ft.FontWeight.BOLD, color=INCOME),
                                ft.Text("总收入", size=12, color="#888"),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                        ]),
                        bgcolor="white",
                        margin=ft.Margin(15, 20, 15, 0),
                        padding=ft.Padding(15, 25, 15, 25),
                        border_radius=16,
                    ),
                    # 设置项
                    ft.Container(
                        ft.Column([
                            ft.Container(
                                ft.Row([
                                    ft.Container(
                                        ft.Icon("delete_outline", color=EXPENSE, size=22),
                                        width=45,
                                        height=45,
                                        bgcolor=EXPENSE + "15",
                                        border_radius=12,
                                        alignment=ft.Alignment(0, 0),
                                    ),
                                    ft.Container(width=15),
                                    ft.Column([
                                        ft.Text("清空数据", size=15, weight=ft.FontWeight.W_500),
                                        ft.Text("删除所有记账记录", size=12, color="#999"),
                                    ], spacing=2, expand=True),
                                    ft.Icon("chevron_right", color="#CCC"),
                                ]),
                                bgcolor="white",
                                padding=ft.Padding(15, 12, 10, 12),
                                border_radius=14,
                                on_click=clear_data,
                            ),
                        ]),
                        padding=ft.Padding(15, 20, 15, 0),
                    ),
                    # 关于
                    ft.Container(
                        ft.Column([
                            ft.Text("🐰", size=50),
                            ft.Container(height=10),
                            ft.Text("Roro记账", size=18, weight=ft.FontWeight.BOLD),
                            ft.Text("v2.0.0", size=12, color="#999"),
                            ft.Container(height=20),
                            ft.Text("Made with ❤️", size=13, color="#999"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.Padding(0, 40, 0, 0),
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Container(height=80 + safe_area_bottom),
                ], spacing=0),
                expand=True,
                bgcolor="#F5F5F5",
            )
        
        # ========== 导航 ==========
        home_page = ft.Container(expand=True)
        add_page = ft.Container(expand=True)
        settings_page = ft.Container(expand=True)
        
        pages_list = [home_page, add_page, settings_page]
        content = ft.Container(pages_list[0], expand=True)
        
        def refresh_all():
            home_page.content = build_home()
            add_page.content = build_add()
            settings_page.content = build_settings()
            page.update()
        
        def nav_change(e):
            content.content = pages_list[e.control.selected_index]
            page.update()
        
        nav = ft.NavigationBar(
            selected_index=0,
            bgcolor="white",
            on_change=nav_change,
            height=65,
            elevation=10,
            shadow_color="#00000020",
            indicator_color=PRIMARY + "20",
            destinations=[
                ft.NavigationBarDestination(icon="home_outlined", selected_icon="home", label="首页"),
                ft.NavigationBarDestination(icon="add_circle_outline", selected_icon="add_circle", label="记账"),
                ft.NavigationBarDestination(icon="settings_outlined", selected_icon="settings", label="设置"),
            ],
        )
        
        refresh_all()
        
        page.add(
            ft.Stack([
                content,
                ft.Container(
                    nav,
                    bottom=0,
                    left=0,
                    right=0,
                ),
            ], expand=True)
        )
    
    except Exception as e:
        show_error(f"{str(e)}\n\n{traceback.format_exc()}")


ft.app(target=main)
