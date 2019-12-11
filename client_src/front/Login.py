#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# author: Valentyn Kofanov


from kivy.uix.screenmanager import Screen
from kivy.lang.builder import Builder
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


Builder.load_file("style.kv")


def check(self, *args, **kwargs):
    return True


def register_check(self, *args, **kwargs):
    return True


class SignInScreen(Screen):

    def login(self):
        login = self.input_login_in.text
        password = self.input_password_in.text
        if check(login, password):
            self.input_login_in.text = ""
            self.input_password_in.text = ""
            self.manager.current = "dialog_screen"

        else:
            self.input_login_in.text = ""
            self.input_password_in.text = ""
            content = BoxLayout(orientation="vertical", spacing=10, padding=10)
            content.add_widget(Label(text="incorrect login/password"))
            but = Button(text="close")
            content.add_widget(but)
            popup = Popup(title='Error', content=content, size_hint=(None, None), size=(400, 400))
            but.bind(on_release=popup.dismiss)
            popup.open()


class SignUpScreen(Screen):

    def register(self):
        login = self.input_login_up.text
        password = self.input_password_up.text
        confirm = self.input_confirm_up.text

        if confirm != password:

            content = BoxLayout(orientation="vertical", spacing=10, padding=10)
            content.add_widget(Label(text="passwords doesn't match"))
            but = Button(text="close")
            content.add_widget(but)
            popup = Popup(title='Error', content=content, size_hint=(None, None), size=(400, 400))
            but.bind(on_release=popup.dismiss)
            popup.open()

        else:

            if register_check(login, password):
                content = BoxLayout(orientation="vertical", spacing=10, padding=10)
                content.add_widget(Label(text="registration succesfull"))
                but = Button(text="sign in")
                content.add_widget(but)
                popup = Popup(title='Error', content=content, size_hint=(None, None), size=(400, 400))

                def tmp(content):
                    popup.dismiss()
                    self.manager.current = "sign_in_screen"
                but.bind(on_release=tmp)

                popup.open()

            else:

                content = BoxLayout(orientation="vertical", spacing=10, padding=10)
                content.add_widget(Label(text="account already exist"))
                but = Button(text="close")
                content.add_widget(but)
                popup = Popup(title='Error', content=content, size_hint=(None, None), size=(400, 400))
                but.bind(on_release=popup.dismiss)
                popup.open()

        self.input_login_up.text = ""
        self.input_password_up.text = ""
        self.input_confirm_up.text = ""



