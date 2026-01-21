import flet as ft
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List


# ==================== 数据管理 ====================
class DataManager:
    def __init__(self):
        self.data_file = "roro_data.json"
        self.data = self.load_data()
        self.migrate_data()
    
    def get_data_path(self):
        try:
            storage = os.environ.get('FLET_APP_STORAGE_DATA')
            if storage:
                os.makedirs(storage, exist_ok=True)
                return os.path.join(storage, self.data_file)
        except:
            pass
        return self.data_file
    
    def get_default_data(self) -> Dict:
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
                    {"name": "其他", "icon": "💡", "color": "#95A5A6"},
                ],
                "收入": [
                    {"name": "工资", "icon": "💰", "color": "#4ECDC4"},
                    {"name": "奖金", "icon": "🎁", "color": "#F39C12"},
                    {"name": "投资", "icon": "📈", "color": "#27AE60"},
                    {"name": "兼职", "icon": "💼", "color": "#3498DB"},
                    {"name": "红包", "icon": "🧧", "color": "#E74C3C"},
                    {"name": "其他", "icon": "💡", "color": "#95A5A6"},
                ]
            },
            "budgets": {},
            "settings": {"monthly_budget": 0}
        }

    def load_data(self) -> Dict:
        try:
            path = self.get_data_path()
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return self.get_default_data()

    def migrate_data(self):
        changed = False
        default = self.get_default_data()
        
        if "budgets" not in self.data:
            self.data["budgets"] = {}
            changed = True
        if "settings" not in self.data:
            self.data["settings"] = default["settings"]
            changed = True
        try:
            cats = self.data.get("categories", {}).get("支出", [])
            if cats and isinstance(cats[0], str):
                self.data["categories"] = default["categories"]
                changed = True
        except:
            self.data["categories"] = default["categories"]
            changed = True
        
        if changed:
            self.save_data()
    
    def save_data(self):
        try:
            path = self.get_data_path()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def add_record(self, record_type, amount, category, icon, note, date):
        record = {
            "id": datetime.now().timestamp(),
            "type": record_type,
            "amount": amount,
            "category": category,
            "icon": icon,
            "note": note,
            "date": date,
        }
        self.data["records"].append(record)
        self.save_data()
    
    def delete_record(self, record_id):
        self.data["records"] = [r for r in self.data["records"] if r["id"] != record_id]
        self.save_data()
    
    def get_records_by_date(self, date):
        return [r for r in self.data["records"] if r["date"] == date]
    
    def get_records_by_month(self, year, month):
        prefix = f"{year}-{month:02d}"
        return [r for r in self.data["records"] if r["date"].startswith(prefix)]
    
    def get_monthly_summary(self, year, month):
        records = self.get_records_by_month(year, month)
        income = sum(r["amount"] for r in records if r["type"] == "收入")
        expense = sum(r["amount"] for r in records if r["type"] == "支出")
        return {"income": income, "expense": expense, "balance": income - expense, "count": len(records)}
    
    def get_category_stats(self, year, month, record_type):
        records = self.get_records_by_month(year, month)
        stats = {}
        for r in records:
            if r["type"] == record_type:
                cat = r["category"]
                if cat not in stats:
                    stats[cat] = {"amount": 0, "count": 0, "icon": r.get("icon", "💰")}
                stats[cat]["amount"] += r["amount"]
                stats[cat]["count"] += 1
        return sorted([{"category": k, **v} for k, v in stats.items()], key=lambda x: x["amount"], reverse=True)
    
    def get_budget(self, year, month):
        key = f"{year}-{month:02d}"
        return self.data.get("budgets", {}).get(key, self.data.get("settings", {}).get("monthly_budget", 0))
    
    def set_budget(self, year, month, amount):
        if "budgets" not in self.data:
            self.data["budgets"] = {}
        self.data["budgets"][f"{year}-{month:02d}"] = amount
        self.data["settings"]["monthly_budget"] = amount
        self.save_data()


# ==================== 主应用 ====================
def main(page: ft.Page):
    page.title = "Roro记账"
    page.bgcolor = "#F5F5F5"
    page.padding = 0
    
    # 颜色
    PRIMARY = "#6C5CE7"
    INCOME = "#00B894"
    EXPENSE = "#E17055"
    
    dm = DataManager()
    
    state = {
        "type": "支出",
        "category": None,
        "icon": None,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "stats_year": datetime.now().year,
        "stats_month": datetime.now().month,
    }
    
    def show_msg(msg, color=None):
        page.snack_bar = ft.SnackBar(ft.Text(msg, color="white"), bgcolor=color or "#333")
        page.snack_bar.open = True
        page.update()
    
    # ========== 首页 ==========
    def build_home():
        today = datetime.now()
        summary = dm.get_monthly_summary(today.year, today.month)
        records = dm.get_records_by_date(today.strftime("%Y-%m-%d"))
        
        def del_record(rid):
            dm.delete_record(rid)
            refresh()
        
        def record_item(r):
            is_exp = r["type"] == "支出"
            return ft.Container(
                content=ft.Row([
                    ft.Text(r.get("icon", "💰"), size=24),
                    ft.Container(width=10),
                    ft.Column([
                        ft.Text(r["category"], size=14, weight=ft.FontWeight.W_500),
                        ft.Text(r.get("note") or "无备注", size=11, color="#888"),
                    ], spacing=2, expand=True),
                    ft.Text(f"{'−' if is_exp else '+'} ¥{r['amount']:.2f}", 
                           color=EXPENSE if is_exp else INCOME, weight=ft.FontWeight.BOLD),
                    ft.IconButton(ft.icons.DELETE_OUTLINE, icon_size=18, icon_color="#999",
                                 on_click=lambda e, rid=r["id"]: del_record(rid)),
                ]),
                bgcolor="white", padding=12, border_radius=12,
                margin=ft.margin.only(bottom=8),
            )
        
        records_list = [record_item(r) for r in reversed(records)] if records else [
            ft.Container(
                ft.Column([
                    ft.Icon(ft.icons.RECEIPT_LONG, size=50, color="#DDD"),
                    ft.Text("今日暂无记录", color="#999"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=40, alignment=ft.alignment.center,
            )
        ]
        
        return ft.Column([
            # 顶部
            ft.Container(
                ft.Column([
                    ft.Text("Roro记账", size=22, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text(today.strftime("%Y年%m月"), size=13, color="#FFFFFFAA"),
                    ft.Container(height=15),
                    ft.Container(
                        ft.Row([
                            ft.Column([
                                ft.Text("支出", size=11, color="#666"),
                                ft.Text(f"¥{summary['expense']:.2f}", size=18, weight=ft.FontWeight.BOLD),
                            ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            ft.Container(width=1, height=35, bgcolor="#EEE"),
                            ft.Column([
                                ft.Text("收入", size=11, color="#666"),
                                ft.Text(f"¥{summary['income']:.2f}", size=18, weight=ft.FontWeight.BOLD, color=INCOME),
                            ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            ft.Container(width=1, height=35, bgcolor="#EEE"),
                            ft.Column([
                                ft.Text("结余", size=11, color="#666"),
                                ft.Text(f"¥{summary['balance']:.2f}", size=18, weight=ft.FontWeight.BOLD,
                                       color=INCOME if summary['balance'] >= 0 else EXPENSE),
                            ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ]),
                        bgcolor="white", padding=15, border_radius=15,
                    ),
                ]),
                gradient=ft.LinearGradient(colors=[PRIMARY, "#A29BFE"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
                padding=ft.padding.only(left=20, right=20, top=45, bottom=25),
                border_radius=ft.border_radius.only(bottom_left=25, bottom_right=25),
            ),
            ft.Container(
                ft.Text("今日记录", size=15, weight=ft.FontWeight.BOLD),
                padding=ft.padding.only(left=20, top=15, bottom=10),
            ),
            ft.Container(
                ft.Column(records_list, spacing=0),
                padding=ft.padding.symmetric(horizontal=15),
                expand=True,
            ),
            ft.Container(height=70),
        ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
    
    # ========== 记账页 ==========
    def build_add():
        amount = ft.TextField(hint_text="0.00", text_align=ft.TextAlign.CENTER, text_size=32,
                             keyboard_type=ft.KeyboardType.NUMBER, border=ft.InputBorder.NONE)
        note = ft.TextField(hint_text="备注", border_radius=10)
        date_txt = ft.Text(state["date"], color=PRIMARY)
        cat_grid = ft.GridView(runs_count=5, spacing=10, run_spacing=10, child_aspect_ratio=0.9)
        
        exp_btn = ft.Text("支出", size=15, weight=ft.FontWeight.BOLD, color="white")
        inc_btn = ft.Text("收入", size=15, color="#FFFFFFAA")
        
        def pick_date(e):
            if e.control.value:
                state["date"] = e.control.value.strftime("%Y-%m-%d")
                date_txt.value = state["date"]
                page.update()
        
        dp = ft.DatePicker(on_change=pick_date)
        page.overlay.append(dp)
        
        def set_type(t):
            state["type"] = t
            state["category"] = state["icon"] = None
            exp_btn.color = "white" if t == "支出" else "#FFFFFFAA"
            exp_btn.weight = ft.FontWeight.BOLD if t == "支出" else None
            inc_btn.color = "white" if t == "收入" else "#FFFFFFAA"
            inc_btn.weight = ft.FontWeight.BOLD if t == "收入" else None
            load_cats()
            page.update()
        
        def load_cats():
            cats = dm.data["categories"].get(state["type"], [])
            cat_grid.controls.clear()
            for c in cats:
                if isinstance(c, str): continue
                sel = state["category"] == c["name"]
                cat_grid.controls.append(
                    ft.Container(
                        ft.Column([
                            ft.Container(
                                ft.Text(c["icon"], size=26),
                                width=48, height=48,
                                bgcolor=c["color"] if sel else c["color"] + "30",
                                border_radius=12,
                                alignment=ft.alignment.center,
                            ),
                            ft.Text(c["name"], size=11, color="#333" if sel else "#888"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                        on_click=lambda e, cat=c: sel_cat(cat),
                    )
                )
        
        def sel_cat(c):
            state["category"] = c["name"]
            state["icon"] = c["icon"]
            load_cats()
            page.update()
        
        def save(e):
            if not amount.value:
                show_msg("请输入金额", EXPENSE)
                return
            if not state["category"]:
                show_msg("请选择分类", EXPENSE)
                return
            try:
                amt = float(amount.value)
            except:
                show_msg("金额无效", EXPENSE)
                return
            
            dm.add_record(state["type"], amt, state["category"], state["icon"] or "💰", note.value or "", state["date"])
            amount.value = note.value = ""
            state["category"] = state["icon"] = None
            load_cats()
            show_msg("✓ 保存成功", INCOME)
            refresh()
        
        load_cats()
        
        return ft.Column([
            ft.Container(
                ft.Column([
                    ft.Row([
                        ft.Container(exp_btn, on_click=lambda e: set_type("支出"), padding=10),
                        ft.Container(inc_btn, on_click=lambda e: set_type("收入"), padding=10),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                    ft.Container(height=10),
                    ft.Row([ft.Text("¥", size=28, color="#FFFFFFAA"), amount], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=10),
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.icons.CALENDAR_TODAY, size=16, color="#FFFFFFAA"),
                            date_txt,
                            ft.IconButton(ft.icons.EDIT_CALENDAR, icon_size=16, icon_color="#FFFFFFAA",
                                         on_click=lambda e: dp.pick_date()),
                        ]),
                        bgcolor="#FFFFFF20", border_radius=10, padding=ft.padding.symmetric(horizontal=15, vertical=5),
                    ),
                ]),
                gradient=ft.LinearGradient(colors=[PRIMARY, "#A29BFE"]),
                padding=ft.padding.only(top=40, bottom=20, left=20, right=20),
                border_radius=ft.border_radius.only(bottom_left=25, bottom_right=25),
            ),
            ft.Container(
                ft.Column([
                    ft.Text("选择分类", size=14, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    cat_grid,
                ]),
                padding=20, expand=True,
            ),
            ft.Container(
                ft.Column([
                    note,
                    ft.Container(height=10),
                    ft.ElevatedButton("保存", width=float("inf"), height=45, bgcolor=PRIMARY, color="white",
                                     on_click=save),
                ]),
                padding=ft.padding.only(left=20, right=20, bottom=90),
            ),
        ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
    
    # ========== 统计页 ==========
    def build_stats():
        m_txt = ft.Text(f"{state['stats_year']}年{state['stats_month']}月", size=15, weight=ft.FontWeight.BOLD)
        summary_box = ft.Column([])
        cat_list = ft.Column([])
        stats_type = ["支出"]
        
        def chg_month(d):
            state["stats_month"] += d
            if state["stats_month"] > 12:
                state["stats_month"] = 1
                state["stats_year"] += 1
            elif state["stats_month"] < 1:
                state["stats_month"] = 12
                state["stats_year"] -= 1
            load_stats()
        
        def set_type(t):
            stats_type[0] = t
            load_stats()
        
        def load_stats():
            m_txt.value = f"{state['stats_year']}年{state['stats_month']}月"
            s = dm.get_monthly_summary(state["stats_year"], state["stats_month"])
            cats = dm.get_category_stats(state["stats_year"], state["stats_month"], stats_type[0])
            total = sum(c["amount"] for c in cats)
            
            summary_box.controls = [
                ft.Row([
                    ft.Column([ft.Text("支出", size=11, color="#888"), ft.Text(f"¥{s['expense']:.2f}", size=18, weight=ft.FontWeight.BOLD, color=EXPENSE)], 
                             horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                    ft.Container(width=1, height=35, bgcolor="#EEE"),
                    ft.Column([ft.Text("收入", size=11, color="#888"), ft.Text(f"¥{s['income']:.2f}", size=18, weight=ft.FontWeight.BOLD, color=INCOME)], 
                             horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ])
            ]
            
            cat_list.controls.clear()
            for c in cats[:8]:
                pct = c["amount"] / total * 100 if total else 0
                cat_list.controls.append(
                    ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(c["icon"], size=20),
                                ft.Container(width=10),
                                ft.Column([ft.Text(c["category"], size=13), ft.Text(f"{c['count']}笔", size=10, color="#999")], spacing=0, expand=True),
                                ft.Text(f"¥{c['amount']:.2f}", weight=ft.FontWeight.BOLD),
                            ]),
                            ft.Container(height=5),
                            ft.Stack([
                                ft.Container(bgcolor="#EEE", height=5, border_radius=3),
                                ft.Container(bgcolor=EXPENSE if stats_type[0] == "支出" else INCOME, height=5, width=pct * 2.5, border_radius=3),
                            ]),
                        ]),
                        padding=ft.padding.symmetric(vertical=8),
                    )
                )
            if not cats:
                cat_list.controls.append(ft.Container(ft.Text("暂无数据", color="#999"), padding=30, alignment=ft.alignment.center))
            page.update()
        
        load_stats()
        
        return ft.Column([
            ft.Container(
                ft.Column([
                    ft.Text("统计", size=20, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(height=15),
                    ft.Row([
                        ft.IconButton(ft.icons.CHEVRON_LEFT, icon_color="white", on_click=lambda e: chg_month(-1)),
                        ft.Container(m_txt, bgcolor="#FFFFFF30", padding=ft.padding.symmetric(horizontal=20, vertical=8), border_radius=20),
                        ft.IconButton(ft.icons.CHEVRON_RIGHT, icon_color="white", on_click=lambda e: chg_month(1)),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                gradient=ft.LinearGradient(colors=[PRIMARY, "#A29BFE"]),
                padding=ft.padding.only(top=40, bottom=20),
                border_radius=ft.border_radius.only(bottom_left=25, bottom_right=25),
            ),
            ft.Container(summary_box, bgcolor="white", margin=15, padding=15, border_radius=15),
            ft.Row([
                ft.Container(ft.Text("支出", color="white" if stats_type[0] == "支出" else "#666"),
                            bgcolor=EXPENSE if stats_type[0] == "支出" else "#EEE", padding=ft.padding.symmetric(horizontal=20, vertical=8),
                            border_radius=20, on_click=lambda e: set_type("支出")),
                ft.Container(ft.Text("收入", color="white" if stats_type[0] == "收入" else "#666"),
                            bgcolor=INCOME if stats_type[0] == "收入" else "#EEE", padding=ft.padding.symmetric(horizontal=20, vertical=8),
                            border_radius=20, on_click=lambda e: set_type("收入")),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Container(cat_list, bgcolor="white", margin=15, padding=15, border_radius=15, expand=True),
            ft.Container(height=70),
        ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
    
    # ========== 设置页 ==========
    def build_settings():
        budget = ft.TextField(value=str(dm.data.get("settings", {}).get("monthly_budget", 0) or ""), 
                             hint_text="输入预算", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)
        
        total = len(dm.data.get("records", []))
        exp = sum(r["amount"] for r in dm.data.get("records", []) if r.get("type") == "支出")
        inc = sum(r["amount"] for r in dm.data.get("records", []) if r.get("type") == "收入")
        
        def save_budget(e):
            try:
                dm.set_budget(datetime.now().year, datetime.now().month, float(budget.value or 0))
                show_msg("预算已保存", INCOME)
            except:
                show_msg("请输入有效金额", EXPENSE)
        
        def clear(e):
            dm.data["records"] = []
            dm.save_data()
            show_msg("数据已清空", "#F39C12")
            refresh()
        
        return ft.Column([
            ft.Container(
                ft.Text("设置", size=20, weight=ft.FontWeight.BOLD, color="white"),
                gradient=ft.LinearGradient(colors=[PRIMARY, "#A29BFE"]),
                padding=ft.padding.only(top=45, bottom=20),
                alignment=ft.alignment.center,
                border_radius=ft.border_radius.only(bottom_left=25, bottom_right=25),
            ),
            ft.Container(
                ft.Row([
                    ft.Column([ft.Text(f"{total}", size=22, weight=ft.FontWeight.BOLD, color=PRIMARY), ft.Text("总记录", size=11, color="#888")], 
                             horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                    ft.Column([ft.Text(f"¥{exp:.0f}", size=22, weight=ft.FontWeight.BOLD, color=EXPENSE), ft.Text("总支出", size=11, color="#888")], 
                             horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                    ft.Column([ft.Text(f"¥{inc:.0f}", size=22, weight=ft.FontWeight.BOLD, color=INCOME), ft.Text("总收入", size=11, color="#888")], 
                             horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ]),
                bgcolor="white", margin=15, padding=20, border_radius=15,
            ),
            ft.Container(
                ft.Column([
                    ft.Text("月预算", weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    ft.Row([budget, ft.ElevatedButton("保存", bgcolor=PRIMARY, color="white", on_click=save_budget)]),
                ]),
                bgcolor="white", margin=ft.margin.symmetric(horizontal=15), padding=15, border_radius=15,
            ),
            ft.Container(
                ft.Column([
                    ft.Container(
                        ft.Row([ft.Icon(ft.icons.DELETE_OUTLINE, color=EXPENSE), ft.Text("清空数据", size=14)]),
                        on_click=clear, padding=12,
                    ),
                ]),
                bgcolor="white", margin=15, border_radius=15,
            ),
            ft.Container(
                ft.Text("Made with ❤️ by Roro", size=12, color="#999"),
                alignment=ft.alignment.center, padding=20,
            ),
            ft.Container(height=70),
        ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
    
    # ========== 导航 ==========
    pages = [ft.Container(expand=True) for _ in range(4)]
    content = ft.Container(pages[0], expand=True)
    
    def refresh():
        pages[0].content = build_home()
        pages[1].content = build_add()
        pages[2].content = build_stats()
        pages[3].content = build_settings()
        page.update()
    
    def nav_change(e):
        content.content = pages[e.control.selected_index]
        page.update()
    
    nav = ft.NavigationBar(
        selected_index=0, bgcolor="white", on_change=nav_change, height=60,
        destinations=[
            ft.NavigationBarDestination(icon=ft.icons.HOME_OUTLINED, selected_icon=ft.icons.HOME, label="首页"),
            ft.NavigationBarDestination(icon=ft.icons.ADD_CIRCLE_OUTLINE, selected_icon=ft.icons.ADD_CIRCLE, label="记账"),
            ft.NavigationBarDestination(icon=ft.icons.PIE_CHART_OUTLINE, selected_icon=ft.icons.PIE_CHART, label="统计"),
            ft.NavigationBarDestination(icon=ft.icons.SETTINGS_OUTLINED, selected_icon=ft.icons.SETTINGS, label="设置"),
        ],
    )
    
    refresh()
    page.add(ft.Stack([ft.Column([content], expand=True), ft.Container(nav, bottom=0, left=0, right=0)], expand=True))


ft.app(target=main)
