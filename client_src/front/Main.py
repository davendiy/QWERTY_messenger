#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# author: Valentyn Kofanov


from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from client_src.front.Login import SignInScreen, SignUpScreen
from client_src.front.Dialog import DialogScreen


class Container(ScreenManager):
    pass


class MessengerApp(App):

    def build(self):
        container = Container()
        container.add_widget(SignInScreen(name="sign_in_screen"))
        container.add_widget(SignUpScreen(name="sign_up_screen"))
        container.add_widget(DialogScreen(name="dialog_screen"))
        container.current = "sign_in_screen"
        return container


if __name__ == '__main__':
    MessengerApp().run()
