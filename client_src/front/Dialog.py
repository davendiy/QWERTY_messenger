#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# author: Valentyn Kofanov

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.recycleview import RecycleView


Builder.load_file("style.kv")

CHATS = ["Alex", "Masha", "Petya", "Vasya", "Vilatiy", "Misha", "John", "Michael", "Alexander", "Fedor", "111", "333"]


class RV(RecycleView):
    def __init__(self, chats=CHATS, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.data = [{'text': str(chat)} for chat in chats]


class DialogScreen(Screen):

    def refresh(self):
        print(self.chat_list.selected.text)







