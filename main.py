# -*- coding: utf-8 -*-
"""Arena AI - обёртка на Kivy + нативный Android WebView."""
import webbrowser

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.utils import get_color_from_hex, platform

URL_HOME = "https://arena.ai/"
URL_RANK = "https://arena.ai/leaderboard"

BG = "#0B0B0F"
BAR = "#15151D"
ACCENT = "#7C5CFF"
UA = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36")
BAR_H = dp(56)

if platform == "android":
    from android.runnable import run_on_ui_thread
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    WebView = autoclass("android.webkit.WebView")
    WebViewClient = autoclass("android.webkit.WebViewClient")
    CookieManager = autoclass("android.webkit.CookieManager")
    Color = autoclass("android.graphics.Color")
    LayoutParams = autoclass("android.view.ViewGroup$LayoutParams")
    activity = PythonActivity.mActivity
else:
    def run_on_ui_thread(func):
        return func


class Web:
    """Управление WebView (все вызовы в UI-потоке Android)."""
    view = None

    @staticmethod
    @run_on_ui_thread
    def create(height_px):
        if Web.view is not None:
            return
        wv = WebView(activity)
        s = wv.getSettings()
        s.setJavaScriptEnabled(True)
        s.setDomStorageEnabled(True)
        s.setDatabaseEnabled(True)
        s.setLoadWithOverviewMode(True)
        s.setUseWideViewPort(True)
        s.setBuiltInZoomControls(False)
        s.setMediaPlaybackRequiresUserGesture(False)
        s.setUserAgentString(UA)
        wv.setBackgroundColor(Color.parseColor(BG))
        cm = CookieManager.getInstance()
        cm.setAcceptCookie(True)
        cm.setAcceptThirdPartyCookies(wv, True)
        wv.setWebViewClient(WebViewClient())  # ссылки открываются внутри
        lp = LayoutParams(LayoutParams.MATCH_PARENT, int(height_px))
        activity.addContentView(wv, lp)
        wv.loadUrl(URL_HOME)
        Web.view = wv

    @staticmethod
    @run_on_ui_thread
    def load(url):
        if Web.view:
            Web.view.loadUrl(url)

    @staticmethod
    @run_on_ui_thread
    def reload():
        if Web.view:
            Web.view.reload()

    @staticmethod
    @run_on_ui_thread
    def back():
        if Web.view and Web.view.canGoBack():
            Web.view.goBack()
        else:
            activity.moveTaskToBack(True)


class ArenaApp(App):
    title = "Arena AI"

    def build(self):
        Window.clearcolor = get_color_from_hex(BG)
        root = BoxLayout(orientation="vertical")

        # Заставка (видна, пока грузится сайт; WebView накладывается сверху)
        self.splash = Label(
            text="[b]Arena AI[/b]\n[size=14sp]Загрузка...[/size]",
            markup=True, font_size="32sp",
            color=get_color_from_hex(ACCENT), halign="center",
        )
        root.add_widget(self.splash)

        bar = BoxLayout(size_hint_y=None, height=BAR_H, spacing=dp(2))
        with bar.canvas.before:
            from kivy.graphics import Color as KColor, Rectangle
            KColor(*get_color_from_hex(BAR))
            self._rect = Rectangle(pos=bar.pos, size=bar.size)
        bar.bind(pos=self._upd, size=self._upd)

        for text, cb in (
            ("Назад", lambda *_: self.go_back()),
            ("Чат", lambda *_: self.open(URL_HOME)),
            ("Рейтинг", lambda *_: self.open(URL_RANK)),
            ("Обновить", lambda *_: self.refresh()),
        ):
            bar.add_widget(Button(
                text=text, background_normal="", background_down="",
                background_color=get_color_from_hex(BAR),
                color=get_color_from_hex("#E8E8F0"), font_size="15sp",
                on_release=cb,
            ))
        root.add_widget(bar)

        Window.bind(on_keyboard=self.on_key)
        return root

    def _upd(self, inst, *_):
        self._rect.pos, self._rect.size = inst.pos, inst.size

    def on_start(self):
        Clock.schedule_once(self.start_web, 0.5)

    def start_web(self, *_):
        if platform == "android":
            Web.create(Window.height - BAR_H)
        else:
            self.splash.text = "Запусти на Android.\nОткрываю сайт в браузере..."
            webbrowser.open(URL_HOME)

    def open(self, url):
        if platform == "android":
            Web.load(url)
        else:
            webbrowser.open(url)

    def refresh(self):
        if platform == "android":
            Web.reload()

    def go_back(self):
        if platform == "android":
            Web.back()

    def on_key(self, window, key, *args):
        if key == 27:  # кнопка «Назад»
            self.go_back()
            return True
        return False

    def on_pause(self):
        return True


if __name__ == "__main__":
    ArenaApp().run()
