import flet as ft
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List
import calendar


# ==================== 数据管理 ====================
class DataManager:
    def __init__(self):
        self.data_file = "roro_data.json"
        self.data = self.load_data()
        self.migrate_data()  # 启动时修复数据

    def get_data_path(self):
        if os.environ.get('FLET_APP_STORAGE_DATA'):
            return os.path.join(os.environ['FLET_APP_STORAGE_DATA'], self.data_file)
        return self.data_file

    def get_default_data(self) -> Dict:
        """定义默认的新版数据结构"""
        return {
            "records": [],
            "categories": {
                "支出": [
                    {"name": "餐饮", "icon": "🍜", "color": "#FF6B6B"},
                    {"name": "交通", "icon": "🚗", "color": "#4ECDC4"},
                    {"name": "购物", "icon": "🛒", "color": "#45B7D1"},
                    {"name": "娱乐", "icon": "🎮", "color": "#96CEB4"},
                    {"name": "居住", "icon": "🏠", "color": "#FFEAA7"},
                    {"name": "通讯", "icon": "📱", "color": "#DDA0DD"},
                    {"name": "医疗", "icon": "💊", "color": "#98D8C8"},
                    {"name": "学习", "icon": "📚", "color": "#F7DC6F"},
                    {"name": "服饰", "icon": "👔", "color": "#BB8FCE"},
                    {"name": "红包", "icon": "🧧", "color": "#E74C3C"},
                    {"name": "其他", "icon": "💡", "color": "#95A5A6"},
                ],
                "收入": [
                    {"name": "工资", "icon": "💰", "color": "#4ECDC4"},
                    {"name": "奖金", "icon": "🎁", "color": "#F39C12"},
                    {"name": "投资", "icon": "📈", "color": "#27AE60"},
                    {"name": "兼职", "icon": "💼", "color": "#3498DB"},
                    {"name": "红包", "icon": "🧧", "color": "#E74C3C"},
                    {"name": "退款", "icon": "💳", "color": "#9B59B6"},
                    {"name": "其他", "icon": "💡", "color": "#95A5A6"},
                ]
            },
            "budgets": {},
            "settings": {
                "monthly_budget": 0,
                "currency": "¥",
            }
        }

    def load_data(self) -> Dict:
        try:
            path = self.get_data_path()
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载数据错误: {e}")

        return self.get_default_data()

    def migrate_data(self):
        """强制修复旧数据结构"""
        changed = False
        default_data = self.get_default_data()

        # 1. 修复缺失字段
        if "budgets" not in self.data:
            self.data["budgets"] = {}
            changed = True

        if "settings" not in self.data:
            self.data["settings"] = default_data["settings"]
            changed = True

        # 2. 核心修复：检查分类是否为旧版字符串列表
        try:
            expense_cats = self.data["categories"].get("支出", [])
            if expense_cats and isinstance(expense_cats[0], str):
                print("检测到旧版分类数据，正在迁移...")
                self.data["categories"] = default_data["categories"]
                changed = True
        except Exception as e:
            print(f"数据迁移检查出错: {e}")
            self.data["categories"] = default_data["categories"]
            changed = True

        if changed:
            self.save_data()
            print("数据结构已修复并保存")

    def save_data(self):
        try:
            path = self.get_data_path()
            dir_path = os.path.dirname(path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据错误: {e}")

    def add_record(self, record_type: str, amount: float, category: str,
                   icon: str, note: str, date: str):
        record = {
            "id": datetime.now().timestamp(),
            "type": record_type,
            "amount": amount,
            "category": category,
            "icon": icon,
            "note": note,
            "date": date,
            "created_at": datetime.now().isoformat()
        }
        self.data["records"].append(record)
        self.save_data()
        return record

    def delete_record(self, record_id: float):
        self.data["records"] = [r for r in self.data["records"] if r["id"] != record_id]
        self.save_data()

    def get_records_by_date(self, date: str) -> List[Dict]:
        return sorted(
            [r for r in self.data["records"] if r["date"] == date],
            key=lambda x: x["created_at"],
            reverse=True
        )

    def get_records_by_month(self, year: int, month: int) -> List[Dict]:
        prefix = f"{year}-{month:02d}"
        return sorted(
            [r for r in self.data["records"] if r["date"].startswith(prefix)],
            key=lambda x: x["date"],
            reverse=True
        )

    def get_monthly_summary(self, year: int, month: int) -> Dict:
        records = self.get_records_by_month(year, month)
        income = sum(r["amount"] for r in records if r["type"] == "收入")
        expense = sum(r["amount"] for r in records if r["type"] == "支出")
        return {
            "income": income,
            "expense": expense,
            "balance": income - expense,
            "count": len(records)
        }

    def get_category_stats(self, year: int, month: int, record_type: str) -> List[Dict]:
        records = self.get_records_by_month(year, month)
        stats = {}
        for r in records:
            if r["type"] == record_type:
                # 兼容旧数据
                cat = r["category"]
                if " " in cat and not r.get("icon"):
                    parts = cat.split(" ", 1)
                    if len(parts) == 2:
                        cat = parts[1]

                if cat not in stats:
                    stats[cat] = {"amount": 0, "count": 0, "icon": r.get("icon", "💰")}
                stats[cat]["amount"] += r["amount"]
                stats[cat]["count"] += 1

        result = [{"category": k, **v} for k, v in stats.items()]
        return sorted(result, key=lambda x: x["amount"], reverse=True)

    def get_weekly_comparison(self) -> Dict:
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())

        this_week_expense = 0
        this_week_income = 0
        last_week_start = week_start - timedelta(days=7)
        last_week_end = week_start - timedelta(days=1)
        last_week_expense = 0
        last_week_income = 0

        for r in self.data["records"]:
            try:
                r_date = datetime.strptime(r["date"], "%Y-%m-%d")
                if week_start.date() <= r_date.date() <= today.date():
                    if r["type"] == "支出":
                        this_week_expense += r["amount"]
                    else:
                        this_week_income += r["amount"]
                elif last_week_start.date() <= r_date.date() <= last_week_end.date():
                    if r["type"] == "支出":
                        last_week_expense += r["amount"]
                    else:
                        last_week_income += r["amount"]
            except:
                pass

        return {
            "this_week": {"expense": this_week_expense, "income": this_week_income},
            "last_week": {"expense": last_week_expense, "income": last_week_income}
        }

    def set_monthly_budget(self, year: int, month: int, amount: float):
        key = f"{year}-{month:02d}"
        self.data["budgets"][key] = amount
        self.save_data()

    def get_monthly_budget(self, year: int, month: int) -> float:
        key = f"{year}-{month:02d}"
        return self.data["budgets"].get(key, self.data["settings"].get("monthly_budget", 0))

    def search_records(self, keyword: str) -> List[Dict]:
        keyword = keyword.lower()
        return [
            r for r in self.data["records"]
            if keyword in r.get("category", "").lower()
               or keyword in r.get("note", "").lower()
        ]


# ==================== 主应用 ====================
def main(page: ft.Page):
    page.title = "Roro记账"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#F8F9FA"

    # 主题色
    PRIMARY_COLOR = "#6C5CE7"
    PRIMARY_LIGHT = "#A29BFE"
    INCOME_COLOR = "#00B894"
    EXPENSE_COLOR = "#E17055"
    CARD_COLOR = "#FFFFFF"
    TEXT_PRIMARY = "#2D3436"
    TEXT_SECONDARY = "#636E72"

    dm = DataManager()

    # 状态变量
    state = {
        "selected_type": "支出",
        "selected_category": None,
        "selected_icon": None,
        "selected_date": datetime.now().strftime("%Y-%m-%d"),
        "stats_year": datetime.now().year,
        "stats_month": datetime.now().month,
        "quick_amounts": [10, 20, 50, 100, 200, 500],
    }

    # ==================== 通用组件 ====================
    def show_snackbar(message: str, color: str = None):
        snack_bar = ft.SnackBar(
            content=ft.Text(message, color="white", size=14),
            bgcolor=color or TEXT_PRIMARY,
            duration=2000,
            behavior=ft.SnackBarBehavior.FLOATING,
        )
        page.open(snack_bar)

    def create_card(content, padding_val=16, margin_val=None):
        if margin_val is None:
            margin_val = ft.margin.only(left=16, right=16, bottom=12)
        return ft.Container(
            content=content,
            bgcolor=CARD_COLOR,
            border_radius=16,
            padding=padding_val,
            margin=margin_val,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color="#0000000D",
                offset=ft.Offset(0, 2),
            ),
        )

    # ==================== 首页 ====================
    def build_home_page():
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")

        monthly_summary = dm.get_monthly_summary(today.year, today.month)
        today_records = dm.get_records_by_date(today_str)
        budget = dm.get_monthly_budget(today.year, today.month)
        weekly = dm.get_weekly_comparison()

        budget_percent = (monthly_summary["expense"] / budget * 100) if budget > 0 else 0
        budget_color = INCOME_COLOR if budget_percent < 80 else ("#F39C12" if budget_percent < 100 else EXPENSE_COLOR)

        def delete_record(record_id):
            def do_delete(e):
                dm.delete_record(record_id)
                page.close(dlg)
                refresh_all()

            def cancel(e):
                page.close(dlg)

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("删除记录", size=18, weight=ft.FontWeight.BOLD),
                content=ft.Text("确定要删除这条记录吗？", size=14, color=TEXT_SECONDARY),
                actions=[
                    ft.TextButton("取消", on_click=cancel),
                    ft.TextButton("删除", on_click=do_delete,
                                  style=ft.ButtonStyle(color=EXPENSE_COLOR)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.open(dlg)

        def create_record_item(record):
            is_expense = record["type"] == "支出"

            # 兼容旧数据处理
            cat_name = record["category"]
            icon = record.get("icon", "💰")
            if "icon" not in record and " " in cat_name:
                parts = cat_name.split(" ", 1)
                if len(parts) == 2:
                    icon = parts[0]
                    cat_name = parts[1]

            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(icon, size=24),
                        width=48, height=48,
                        bgcolor="#F8F9FA",
                        border_radius=12,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(width=12),
                    ft.Column([
                        ft.Text(cat_name, size=15, weight=ft.FontWeight.W_500,
                                color=TEXT_PRIMARY),
                        ft.Text(record["note"] if record["note"] else "无备注",
                                size=12, color=TEXT_SECONDARY),
                    ], spacing=4, expand=True),
                    ft.Text(
                        f"{'-' if is_expense else '+'} ¥{record['amount']:.2f}",
                        size=16, weight=ft.FontWeight.BOLD,
                        color=EXPENSE_COLOR if is_expense else INCOME_COLOR
                    ),
                    ft.IconButton(
                        icon=ft.icons.CLOSE,
                        icon_color=TEXT_SECONDARY,
                        icon_size=16,
                        on_click=lambda e, rid=record["id"]: delete_record(rid),
                    ),
                ]),
                padding=ft.padding.symmetric(vertical=8),
            )

        expense_diff = weekly["this_week"]["expense"] - weekly["last_week"]["expense"]
        expense_diff_percent = (expense_diff / weekly["last_week"]["expense"] * 100) if weekly["last_week"][
                                                                                            "expense"] > 0 else 0

        budget_section = []
        if budget > 0:
            budget_section = [
                ft.Container(height=16),
                ft.Row([
                    ft.Text("月预算", size=12, color=TEXT_SECONDARY),
                    ft.Text(f"¥{monthly_summary['expense']:.0f} / ¥{budget:.0f}",
                            size=12, color=TEXT_SECONDARY),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=8),
                ft.Stack([
                    ft.Container(
                        bgcolor="#E8E8E8",
                        border_radius=4,
                        height=8,
                    ),
                    ft.Container(
                        bgcolor=budget_color,
                        border_radius=4,
                        height=8,
                        width=min(budget_percent, 100) * 2.8,
                    ),
                ]),
            ]

        week_badge = []
        if weekly["last_week"]["expense"] > 0:
            week_badge = [
                ft.Container(
                    content=ft.Text(
                        f"{'↑' if expense_diff > 0 else '↓'} {abs(expense_diff_percent):.1f}%",
                        size=11, color="white"
                    ),
                    bgcolor=EXPENSE_COLOR if expense_diff > 0 else INCOME_COLOR,
                    border_radius=10,
                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                )
            ]

        if today_records:
            records_content = [create_record_item(r) for r in today_records[:5]]
        else:
            records_content = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.RECEIPT_LONG_OUTLINED, size=48, color="#DDD"),
                        ft.Container(height=8),
                        ft.Text("今日暂无记录", size=14, color=TEXT_SECONDARY),
                        ft.Container(height=4),
                        ft.TextButton(
                            "立即记一笔",
                            on_click=lambda e: switch_page(1),
                            style=ft.ButtonStyle(color=PRIMARY_COLOR),
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=40,
                )
            ]

        return ft.Column([
            # 顶部渐变区域
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text("Roro记账", size=24, weight=ft.FontWeight.BOLD, color="white"),
                            ft.Text(today.strftime("%Y年%m月%d日"), size=13, color="white70"),
                        ], spacing=4),
                        ft.Row([
                            ft.IconButton(
                                icon=ft.icons.SEARCH,
                                icon_color="white",
                                on_click=lambda e: show_search_dialog(),
                            ),
                        ], spacing=0),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                    ft.Container(height=20),

                    # 月度概览卡片
                    ft.Container(
                        content=ft.Column([
                                              ft.Row(
                                                  [ft.Text(f"{today.month}月概览", size=14,
                                                           color=TEXT_SECONDARY)] + week_badge,
                                                  alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                              ),
                                              ft.Container(height=16),
                                              ft.Row([
                                                  ft.Column([
                                                      ft.Text("支出", size=12, color=TEXT_SECONDARY),
                                                      ft.Text(f"¥{monthly_summary['expense']:.2f}",
                                                              size=22, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                                  ], expand=True),
                                                  ft.Container(width=1, height=40, bgcolor="#E0E0E0"),
                                                  ft.Column([
                                                      ft.Text("收入", size=12, color=TEXT_SECONDARY),
                                                      ft.Text(f"¥{monthly_summary['income']:.2f}",
                                                              size=22, weight=ft.FontWeight.BOLD, color=INCOME_COLOR),
                                                  ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                                  ft.Container(width=1, height=40, bgcolor="#E0E0E0"),
                                                  ft.Column([
                                                      ft.Text("结余", size=12, color=TEXT_SECONDARY),
                                                      ft.Text(f"¥{monthly_summary['balance']:.2f}",
                                                              size=22, weight=ft.FontWeight.BOLD,
                                                              color=INCOME_COLOR if monthly_summary[
                                                                                        'balance'] >= 0 else EXPENSE_COLOR),
                                                  ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.END),
                                              ]),
                                          ] + budget_section),
                        bgcolor=CARD_COLOR,
                        border_radius=20,
                        padding=20,
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=20,
                            color="#00000015",
                            offset=ft.Offset(0, 4),
                        ),
                    ),
                ]),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[PRIMARY_COLOR, PRIMARY_LIGHT],
                ),
                padding=ft.padding.only(left=20, right=20, top=50, bottom=30),
                border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30),
            ),

            # 今日记录标题
            ft.Container(
                content=ft.Row([
                    ft.Text("今日记录", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.TextButton(
                        "查看全部",
                        on_click=lambda e: switch_page(2),
                        style=ft.ButtonStyle(color=PRIMARY_COLOR),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.only(left=20, right=20, top=16, bottom=8),
            ),

            # 记录列表
            ft.Container(
                content=ft.Column(records_content, spacing=0),
                bgcolor=CARD_COLOR,
                border_radius=16,
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                margin=ft.margin.only(left=16, right=16),
                expand=True,
            ),

            ft.Container(height=80),
        ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

    def show_search_dialog():
        search_results = ft.Column([], scroll=ft.ScrollMode.AUTO, height=300)

        def do_search(e):
            keyword = e.control.value
            if not keyword:
                search_results.controls.clear()
                page.update()
                return

            results = dm.search_records(keyword)
            search_results.controls.clear()

            if not results:
                search_results.controls.append(
                    ft.Container(
                        content=ft.Text("未找到相关记录", color=TEXT_SECONDARY),
                        alignment=ft.alignment.center,
                        padding=40,
                    )
                )
            else:
                for r in results[:20]:
                    is_expense = r["type"] == "支出"

                    # 兼容处理
                    cat_name = r["category"]
                    icon = r.get("icon", "💰")
                    if "icon" not in r and " " in cat_name:
                        parts = cat_name.split(" ", 1)
                        if len(parts) == 2:
                            icon = parts[0]
                            cat_name = parts[1]

                    search_results.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(icon, size=20),
                                ft.Container(width=8),
                                ft.Column([
                                    ft.Text(cat_name, size=14),
                                    ft.Text(r["date"], size=11, color=TEXT_SECONDARY),
                                ], spacing=2, expand=True),
                                ft.Text(
                                    f"{'−' if is_expense else '+'} ¥{r['amount']:.2f}",
                                    color=EXPENSE_COLOR if is_expense else INCOME_COLOR,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ]),
                            padding=12,
                            border=ft.border.only(bottom=ft.BorderSide(1, "#F0F0F0")),
                        )
                    )
            page.update()

        def close_dialog(e):
            page.close(dlg)

        search_field = ft.TextField(
            hint_text="搜索分类或备注...",
            border_radius=12,
            prefix_icon=ft.icons.SEARCH,
            on_change=do_search,
        )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("搜索记录", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    search_field,
                    ft.Container(height=16),
                    search_results,
                ]),
                width=350,
            ),
            actions=[ft.TextButton("关闭", on_click=close_dialog)],
        )
        page.open(dlg)

    # ==================== 记账页 ====================
    def build_add_page():
        amount_field = ft.TextField(
            value="",
            text_align=ft.TextAlign.CENTER,
            text_size=36,
            hint_text="0.00",
            hint_style=ft.TextStyle(size=36, color="#DDD"),
            border=ft.InputBorder.NONE,
            keyboard_type=ft.KeyboardType.NUMBER,
            color=TEXT_PRIMARY,
        )

        note_field = ft.TextField(
            hint_text="添加备注...",
            border_radius=12,
            bgcolor="#F8F9FA",
            border_color="transparent",
            focused_border_color=PRIMARY_COLOR,
        )

        date_text = ft.Text(
            state["selected_date"],
            size=14,
            color=PRIMARY_COLOR,
            weight=ft.FontWeight.W_500,
        )

        category_grid = ft.GridView(
            runs_count=5,
            spacing=12,
            run_spacing=12,
            child_aspect_ratio=0.85,
        )

        expense_text = ft.Text("支出", size=15, weight=ft.FontWeight.BOLD, color="white")
        income_text = ft.Text("收入", size=15, color="white70")

        def on_date_change(e):
            if e.control.value:
                state["selected_date"] = e.control.value.strftime("%Y-%m-%d")
                date_text.value = state["selected_date"]
                page.update()

        date_picker = ft.DatePicker(
            first_date=datetime(2020, 1, 1),
            last_date=datetime(2030, 12, 31),
            on_change=on_date_change,
        )
        page.overlay.append(date_picker)

        def select_type(t):
            state["selected_type"] = t
            state["selected_category"] = None
            state["selected_icon"] = None

            if t == "支出":
                expense_text.color = "white"
                expense_text.weight = ft.FontWeight.BOLD
                income_text.color = "white70"
                income_text.weight = None
            else:
                income_text.color = "white"
                income_text.weight = ft.FontWeight.BOLD
                expense_text.color = "white70"
                expense_text.weight = None

            update_categories()
            page.update()

        def update_categories():
            categories = dm.data["categories"].get(state["selected_type"], [])

            category_grid.controls.clear()

            for cat in categories:
                if isinstance(cat, str): continue

                is_selected = state["selected_category"] == cat["name"]

                btn = ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Text(cat["icon"], size=28),
                            width=52, height=52,
                            bgcolor=cat["color"] if is_selected else cat["color"] + "20",
                            border_radius=14,
                            alignment=ft.alignment.center,
                        ),
                        ft.Text(
                            cat["name"],
                            size=12,
                            color=TEXT_PRIMARY if is_selected else TEXT_SECONDARY,
                            weight=ft.FontWeight.W_500 if is_selected else None,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                    data=cat,
                    on_click=lambda e: select_category(e.control.data),
                )
                category_grid.controls.append(btn)

        def select_category(cat):
            state["selected_category"] = cat["name"]
            state["selected_icon"] = cat["icon"]
            update_categories()
            page.update()

        def on_quick_amount(amount):
            current = amount_field.value or "0"
            try:
                new_amount = float(current) + amount
                amount_field.value = str(new_amount)
            except:
                amount_field.value = str(amount)
            page.update()

        def clear_amount(e):
            amount_field.value = ""
            page.update()

        def save_record(e):
            if not amount_field.value:
                show_snackbar("请输入金额", EXPENSE_COLOR)
                return
            if not state["selected_category"]:
                show_snackbar("请选择分类", EXPENSE_COLOR)
                return
            try:
                amount = float(amount_field.value)
                if amount <= 0:
                    show_snackbar("金额必须大于0", EXPENSE_COLOR)
                    return
            except:
                show_snackbar("请输入有效金额", EXPENSE_COLOR)
                return

            dm.add_record(
                record_type=state["selected_type"],
                amount=amount,
                category=state["selected_category"],
                icon=state["selected_icon"] or "💰",
                note=note_field.value or "",
                date=state["selected_date"],
            )

            amount_field.value = ""
            note_field.value = ""
            state["selected_category"] = None
            state["selected_icon"] = None
            update_categories()

            show_snackbar("✓ 记账成功", INCOME_COLOR)
            refresh_all()

        update_categories()

        return ft.Column([
            # 顶部
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=expense_text,
                                on_click=lambda e: select_type("支出"),
                                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                            ),
                            ft.Container(
                                content=income_text,
                                on_click=lambda e: select_type("收入"),
                                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                            ),
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                        margin=ft.margin.only(top=40, bottom=20),
                    ),

                    ft.Row([
                        ft.Text("¥", size=28, color="white70"),
                        ft.Container(content=amount_field, expand=True),
                        ft.IconButton(
                            icon=ft.icons.BACKSPACE_OUTLINED,
                            icon_color="white70",
                            icon_size=22,
                            on_click=clear_amount,
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER),

                    ft.Row([
                        ft.Container(
                            content=ft.Text(f"+{amt}", size=13, color="white"),
                            bgcolor="white20",
                            border_radius=20,
                            padding=ft.padding.symmetric(horizontal=14, vertical=6),
                            on_click=lambda e, a=amt: on_quick_amount(a),
                        ) for amt in state["quick_amounts"]
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=8,
                        scroll=ft.ScrollMode.AUTO),

                    ft.Container(height=16),

                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.CALENDAR_TODAY_OUTLINED, color="white70", size=18),
                            ft.Container(width=8),
                            date_text,
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.icons.EDIT_CALENDAR,
                                icon_color="white70",
                                icon_size=18,
                                on_click=lambda e: date_picker.pick_date(),
                            ),
                        ]),
                        bgcolor="white15",
                        border_radius=12,
                        padding=ft.padding.symmetric(horizontal=16, vertical=4),
                        margin=ft.margin.symmetric(horizontal=20),
                    ),
                ]),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_center,
                    end=ft.alignment.bottom_center,
                    colors=[PRIMARY_COLOR, PRIMARY_LIGHT],
                ),
                padding=ft.padding.only(bottom=24),
                border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30),
            ),

            ft.Container(
                content=ft.Column([
                    ft.Text("选择分类", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Container(height=12),
                    category_grid,
                ]),
                padding=ft.padding.only(left=20, right=20, top=20),
                expand=True,
            ),

            ft.Container(
                content=ft.Column([
                    note_field,
                    ft.Container(height=16),
                    ft.ElevatedButton(
                        "保存",
                        width=float("inf"),
                        height=50,
                        bgcolor=PRIMARY_COLOR,
                        color="white",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=14),
                        ),
                        on_click=save_record,
                    ),
                ]),
                padding=ft.padding.only(left=20, right=20, bottom=100),
            ),
        ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)

    # ==================== 统计页 ====================
    def build_stats_page():
        month_text = ft.Text(
            f"{state['stats_year']}年{state['stats_month']}月",
            size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY
        )

        stats_type = ["支出"]

        summary_container = ft.Column([])
        chart_container = ft.Column([])
        category_list = ft.Column([])

        def change_month(delta):
            state["stats_month"] += delta
            if state["stats_month"] > 12:
                state["stats_month"] = 1
                state["stats_year"] += 1
            elif state["stats_month"] < 1:
                state["stats_month"] = 12
                state["stats_year"] -= 1
            refresh_stats()

        def toggle_stats_type(t):
            stats_type[0] = t
            refresh_stats()

        def refresh_stats():
            month_text.value = f"{state['stats_year']}年{state['stats_month']}月"
            summary = dm.get_monthly_summary(state["stats_year"], state["stats_month"])
            category_stats = dm.get_category_stats(state["stats_year"], state["stats_month"], stats_type[0])
            total = sum(c["amount"] for c in category_stats)

            summary_container.controls = [
                ft.Row([
                    ft.Column([
                        ft.Text("总支出", size=12, color=TEXT_SECONDARY),
                        ft.Text(f"¥{summary['expense']:.2f}", size=20,
                                weight=ft.FontWeight.BOLD, color=EXPENSE_COLOR),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                    ft.Container(width=1, height=40, bgcolor="#E8E8E8"),
                    ft.Column([
                        ft.Text("总收入", size=12, color=TEXT_SECONDARY),
                        ft.Text(f"¥{summary['income']:.2f}", size=20,
                                weight=ft.FontWeight.BOLD, color=INCOME_COLOR),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                    ft.Container(width=1, height=40, bgcolor="#E8E8E8"),
                    ft.Column([
                        ft.Text("笔数", size=12, color=TEXT_SECONDARY),
                        ft.Text(f"{summary['count']}", size=20,
                                weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ]),
            ]

            chart_container.controls = [
                ft.Row([
                    ft.Container(
                        content=ft.Text("支出", size=13,
                                        color="white" if stats_type[0] == "支出" else TEXT_SECONDARY,
                                        weight=ft.FontWeight.W_500),
                        bgcolor=EXPENSE_COLOR if stats_type[0] == "支出" else "#F0F0F0",
                        border_radius=20,
                        padding=ft.padding.symmetric(horizontal=20, vertical=8),
                        on_click=lambda e: toggle_stats_type("支出"),
                    ),
                    ft.Container(
                        content=ft.Text("收入", size=13,
                                        color="white" if stats_type[0] == "收入" else TEXT_SECONDARY,
                                        weight=ft.FontWeight.W_500),
                        bgcolor=INCOME_COLOR if stats_type[0] == "收入" else "#F0F0F0",
                        border_radius=20,
                        padding=ft.padding.symmetric(horizontal=20, vertical=8),
                        on_click=lambda e: toggle_stats_type("收入"),
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=12),
            ]

            category_list.controls.clear()
            if category_stats:
                for cat in category_stats[:8]:
                    pct = (cat["amount"] / total * 100) if total > 0 else 0
                    bar_color = EXPENSE_COLOR if stats_type[0] == "支出" else INCOME_COLOR

                    category_list.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Container(
                                        content=ft.Text(cat["icon"], size=20),
                                        width=40, height=40,
                                        bgcolor=bar_color + "15",
                                        border_radius=10,
                                        alignment=ft.alignment.center,
                                    ),
                                    ft.Container(width=12),
                                    ft.Column([
                                        ft.Text(cat["category"], size=14, weight=ft.FontWeight.W_500),
                                        ft.Text(f"{cat['count']}笔", size=11, color=TEXT_SECONDARY),
                                    ], spacing=2, expand=True),
                                    ft.Column([
                                        ft.Text(f"¥{cat['amount']:.2f}", size=14,
                                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                        ft.Text(f"{pct:.1f}%", size=11, color=TEXT_SECONDARY),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
                                ]),
                                ft.Container(height=8),
                                ft.Stack([
                                    ft.Container(
                                        bgcolor="#F0F0F0",
                                        border_radius=3,
                                        height=6,
                                    ),
                                    ft.Container(
                                        bgcolor=bar_color,
                                        border_radius=3,
                                        height=6,
                                        width=pct * 2.8,
                                    ),
                                ]),
                            ]),
                            padding=ft.padding.symmetric(vertical=8),
                        )
                    )
            else:
                category_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.ANALYTICS_OUTLINED, size=48, color="#DDD"),
                            ft.Text("暂无数据", color=TEXT_SECONDARY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        padding=40,
                    )
                )

            page.update()

        refresh_stats()

        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Container(height=40),
                    ft.Text("统计分析", size=20, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(height=16),
                    ft.Row([
                        ft.IconButton(
                            icon=ft.icons.CHEVRON_LEFT,
                            icon_color="white",
                            on_click=lambda e: change_month(-1),
                        ),
                        ft.Container(
                            content=month_text,
                            bgcolor="white20",
                            border_radius=20,
                            padding=ft.padding.symmetric(horizontal=20, vertical=8),
                        ),
                        ft.IconButton(
                            icon=ft.icons.CHEVRON_RIGHT,
                            icon_color="white",
                            on_click=lambda e: change_month(1),
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[PRIMARY_COLOR, PRIMARY_LIGHT],
                ),
                padding=ft.padding.only(bottom=24),
                border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30),
            ),

            ft.Container(
                content=ft.Column([
                    create_card(summary_container),
                    ft.Container(content=chart_container, padding=ft.padding.symmetric(vertical=8)),
                    create_card(
                        ft.Column([
                            ft.Text("分类明细", size=15, weight=ft.FontWeight.BOLD),
                            ft.Container(height=8),
                            category_list,
                        ]),
                    ),
                    ft.Container(height=80),
                ], spacing=0),
                expand=True,
                padding=ft.padding.only(top=16),
            ),
        ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

    # ==================== 设置页 ====================
    def build_settings_page():
        budget_field = ft.TextField(
            value=str(dm.data["settings"].get("monthly_budget", 0)),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            prefix_text="¥ ",
        )

        def save_budget(e):
            try:
                budget = float(budget_field.value or 0)
                dm.data["settings"]["monthly_budget"] = budget
                now = datetime.now()
                dm.set_monthly_budget(now.year, now.month, budget)
                show_snackbar("预算设置成功", INCOME_COLOR)
                refresh_all()
            except:
                show_snackbar("请输入有效金额", EXPENSE_COLOR)

        def export_data(e):
            try:
                data_str = json.dumps(dm.data, ensure_ascii=False, indent=2)
                page.set_clipboard(data_str)
                show_snackbar("数据已复制到剪贴板", INCOME_COLOR)
            except Exception as ex:
                show_snackbar(f"导出失败", EXPENSE_COLOR)

        def clear_data(e):
            def confirm(e):
                dm.data["records"] = []
                dm.save_data()
                page.close(dlg)
                refresh_all()
                show_snackbar("数据已清空", "#F39C12")

            def cancel(e):
                page.close(dlg)

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=EXPENSE_COLOR),
                    ft.Container(width=8),
                    ft.Text("确认清空", size=18, weight=ft.FontWeight.BOLD),
                ]),
                content=ft.Text("此操作将删除所有记账数据，且无法恢复。",
                                size=14, color=TEXT_SECONDARY),
                actions=[
                    ft.TextButton("取消", on_click=cancel),
                    ft.ElevatedButton(
                        "确认清空",
                        bgcolor=EXPENSE_COLOR,
                        color="white",
                        on_click=confirm,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.open(dlg)

        def show_about(e):
            def close_dlg(e):
                page.close(dlg)

            dlg = ft.AlertDialog(
                title=ft.Row([
                    ft.Text("🐰", size=28),
                    ft.Container(width=8),
                    ft.Text("Roro记账", size=20, weight=ft.FontWeight.BOLD),
                ]),
                content=ft.Column([
                    ft.Text("版本 2.0.0", size=14, color=TEXT_SECONDARY),
                    ft.Container(height=12),
                    ft.Text("一款简洁优雅的个人记账应用", size=14),
                    ft.Text("使用 Python + Flet 开发", size=14, color=TEXT_SECONDARY),
                ], tight=True, spacing=4),
                actions=[ft.TextButton("关闭", on_click=close_dlg)],
            )
            page.open(dlg)

        def create_setting_item(icon, title, subtitle, action=None):
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=PRIMARY_COLOR, size=22),
                        width=44, height=44,
                        bgcolor=PRIMARY_COLOR + "15",
                        border_radius=12,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(width=16),
                    ft.Column([
                        ft.Text(title, size=15, weight=ft.FontWeight.W_500),
                        ft.Text(subtitle, size=12, color=TEXT_SECONDARY),
                    ], spacing=2, expand=True),
                    ft.Icon(ft.icons.CHEVRON_RIGHT, color=TEXT_SECONDARY, size=20),
                ]),
                padding=ft.padding.symmetric(vertical=12, horizontal=4),
                on_click=action,
            )

        total_records = len(dm.data["records"])
        total_expense = sum(r["amount"] for r in dm.data["records"] if r["type"] == "支出")
        total_income = sum(r["amount"] for r in dm.data["records"] if r["type"] == "收入")

        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Container(height=40),
                    ft.Text("设置", size=20, weight=ft.FontWeight.BOLD, color="white"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[PRIMARY_COLOR, PRIMARY_LIGHT],
                ),
                padding=ft.padding.only(bottom=24),
                border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30),
            ),

            ft.Container(
                content=ft.Column([
                    create_card(
                        ft.Row([
                            ft.Column([
                                ft.Text(f"{total_records}", size=24, weight=ft.FontWeight.BOLD,
                                        color=PRIMARY_COLOR),
                                ft.Text("总记录", size=12, color=TEXT_SECONDARY),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                            ft.Column([
                                ft.Text(f"¥{total_expense:.0f}", size=24, weight=ft.FontWeight.BOLD,
                                        color=EXPENSE_COLOR),
                                ft.Text("总支出", size=12, color=TEXT_SECONDARY),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                            ft.Column([
                                ft.Text(f"¥{total_income:.0f}", size=24, weight=ft.FontWeight.BOLD,
                                        color=INCOME_COLOR),
                                ft.Text("总收入", size=12, color=TEXT_SECONDARY),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                        ]),
                    ),

                    create_card(
                        ft.Column([
                            ft.Text("月度预算", size=15, weight=ft.FontWeight.BOLD),
                            ft.Container(height=12),
                            ft.Row([
                                ft.Container(content=budget_field, expand=True),
                                ft.Container(width=12),
                                ft.ElevatedButton(
                                    "保存",
                                    bgcolor=PRIMARY_COLOR,
                                    color="white",
                                    on_click=save_budget,
                                ),
                            ]),
                        ]),
                    ),

                    create_card(
                        ft.Column([
                            create_setting_item(
                                ft.icons.UPLOAD_OUTLINED,
                                "导出数据",
                                "复制数据到剪贴板",
                                action=export_data,
                            ),
                            ft.Divider(height=1, color="#F0F0F0"),
                            create_setting_item(
                                ft.icons.DELETE_OUTLINE,
                                "清空数据",
                                "删除所有记账记录",
                                action=clear_data,
                            ),
                            ft.Divider(height=1, color="#F0F0F0"),
                            create_setting_item(
                                ft.icons.INFO_OUTLINE,
                                "关于",
                                "版本信息",
                                action=show_about,
                            ),
                        ], spacing=0),
                        padding_val=ft.padding.symmetric(horizontal=16, vertical=8),
                    ),

                    ft.Container(
                        content=ft.Column([
                            ft.Text("Made with ❤️ by Roro", size=12, color=TEXT_SECONDARY),
                            ft.Text("v2.0.0", size=11, color="#CCC"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                        alignment=ft.alignment.center,
                        padding=30,
                    ),

                    ft.Container(height=80),
                ], spacing=0),
                expand=True,
                padding=ft.padding.only(top=16),
            ),
        ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

    # ==================== 导航 ====================
    pages_content = [ft.Container(expand=True) for _ in range(4)]
    content_area = ft.Container(content=pages_content[0], expand=True)

    def refresh_all():
        pages_content[0].content = build_home_page()
        pages_content[1].content = build_add_page()
        pages_content[2].content = build_stats_page()
        pages_content[3].content = build_settings_page()
        page.update()

    def switch_page(index):
        nav_bar.selected_index = index
        content_area.content = pages_content[index]
        page.update()

    def on_nav_change(e):
        content_area.content = pages_content[e.control.selected_index]
        page.update()

    nav_bar = ft.NavigationBar(
        selected_index=0,
        bgcolor="white",
        elevation=0,
        on_change=on_nav_change,
        destinations=[
            ft.NavigationBarDestination(icon=ft.icons.HOME_OUTLINED, selected_icon=ft.icons.HOME, label="首页"),
            ft.NavigationBarDestination(icon=ft.icons.ADD_CIRCLE_OUTLINE, selected_icon=ft.icons.ADD_CIRCLE,
                                        label="记账"),
            ft.NavigationBarDestination(icon=ft.icons.PIE_CHART_OUTLINE, selected_icon=ft.icons.PIE_CHART,
                                        label="统计"),
            ft.NavigationBarDestination(icon=ft.icons.SETTINGS_OUTLINED, selected_icon=ft.icons.SETTINGS, label="设置"),
        ],
        height=65,
    )

    refresh_all()

    page.add(
        ft.Stack([
            ft.Column([content_area], spacing=0, expand=True),
            ft.Container(
                content=nav_bar,
                bottom=0,
                left=0,
                right=0,
            ),
        ], expand=True)
    )


if __name__ == "__main__":
    ft.app(target=main)