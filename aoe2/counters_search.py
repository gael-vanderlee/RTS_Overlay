from PyQt6.QtGui import QFont, QIcon, QShortcut, QKeySequence, QPixmap
from PyQt6.QtWidgets import QMainWindow, QLineEdit, QPushButton, QLabel
from PyQt6.QtCore import Qt, QPoint, QSize
from pathlib import Path
import json
from thefuzz import process

from aoe2.aoe2_settings import AoE2OverlaySettings
from common.useful_tools import set_background_opacity, widget_y_end
from common.label_display import QLabelSettings, MultiQLabelDisplay


class CountersSearchWindow(QMainWindow):
    def __init__(self, settings: AoE2OverlaySettings, icon_path: str):
        """Constructor

        Parameters
        ----------
        parent                 parent window
        game_icon              icon of the game
        build_order_folder     folder where the build orders are saved
        font_police            font police type
        font_size              font size
        color_font             color of the font
        color_background       color of the background
        opacity                opacity of the window
        border_size            size of the borders
        edit_width             width for the build order text input
        edit_height            height for the build order text input
        edit_init_text         initial text for the build order text input
        button_margin          margin from text to button border
        vertical_spacing       vertical spacing between the elements
        horizontal_spacing     horizontal spacing between the elements
        build_order_website    list of 2 website elements [button name, website link], empty otherwise
        """
        counter_path = Path(__file__).resolve().parent / "unit_counters.json"
        if not counter_path.exists():
            print("Counters file not found, can't search for counters")
            return
        super().__init__()

        with open(counter_path, 'r') as f:
            self.unit_counters = json.load(f)

        # style to apply on the different parts
        style_description = f'color: rgb({settings.panel_build_order.color_font[0]}, {settings.panel_build_order.color_font[1]}, {settings.panel_build_order.color_font[2]})'

        # text input for the build order
        color_default_str = f'color: rgb({settings.layout.color_default[0]}, {settings.layout.color_default[1]}, {settings.layout.color_default[2]})'
        qwidget_color_default_str = f'QWidget{{ {color_default_str}; border: 1px solid white }};'

        # Search objects
        self.text_input = QLineEdit(self)
        self.text_input.resize(settings.layout.configuration.counter_search_size[0],
                               settings.layout.configuration.counter_search_size[1])
        self.text_input.setStyleSheet(qwidget_color_default_str)
        self.text_input.setFont(QFont(settings.layout.font_police, settings.layout.font_size))
        self.text_input.setToolTip('Unit that you want to counter')
        self.text_input.move(settings.panel_build_order.border_size, settings.panel_build_order.border_size)
        self.text_input.textChanged.connect(self.update_search)

        self.pictures_folder = Path(__file__).resolve().parent.parent / "pictures"
        self.unit_icons_folder = self.pictures_folder / "aoe2" / "unit_icons"
        self.unit_selection_display = MultiQLabelDisplay(
            font_police=settings.layout.font_police,
            font_size=settings.layout.font_size,
            border_size=settings.layout.border_size,
            vertical_spacing=settings.layout.configuration.build_order_selection_vertical_spacing,
            color_default=settings.layout.color_default,
            image_height=settings.layout.build_order.image_height,
            game_pictures_folder=self.unit_icons_folder.as_posix()
        )

        # Counter display objects
        self.unit_counters_display = MultiQLabelDisplay(
            font_police=settings.layout.font_police,
            font_size=settings.layout.font_size,
            border_size=settings.layout.border_size,
            vertical_spacing=settings.layout.configuration.build_order_selection_vertical_spacing,
            color_default=settings.layout.color_default,
            image_height=settings.layout.build_order.image_height,
            game_pictures_folder=self.unit_icons_folder.as_posix()
        )
        self.back_button = QPushButton(self)
        self.back_button.setFont(QFont(settings.layout.font_police, settings.layout.font_size))
        self.back_button.setToolTip('Back to search')
        self.back_button.setIcon(QIcon((self.pictures_folder / "common" / "action_button" / "previous.png").as_posix()))
        w, h = settings.layout.action_button_size, settings.layout.action_button_size
        self.back_button.setIconSize(QSize(w, h))
        self.back_button.setGeometry(settings.panel_build_order.border_size, settings.panel_build_order.border_size, w,
                                     h)
        # self.back_button.move()
        self.back_button.clicked.connect(self.go_back)
        self.unit_picture = QLabel(self)
        self.unit_text = QLabel("", self)

        self.search_results = list()
        self.max_shown = 10
        self.selection_id = 0
        self.selected_unit = None
        self.settings = settings
        self.previous_hover_id = -1
        self.hover_id = -1

        # Esc hotkey
        QShortcut(QKeySequence("ESC"), self).activated.connect(self.close)
        QShortcut(QKeySequence("Return"), self).activated.connect(self.select)

        # window properties and show
        # TODO position next to the parent window ?
        max_width = settings.panel_build_order.border_size + self.text_input.width()
        self.setWindowTitle('Counters Search')
        self.setWindowIcon(QIcon(icon_path))
        self.resize(
            max_width + settings.panel_build_order.border_size,
            widget_y_end(self.text_input) + settings.panel_build_order.border_size
        )
        set_background_opacity(self, settings.panel_build_order.color_background, settings.panel_build_order.opacity)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.show_search()
        self.show()

    def update_search(self):
        """Update the build order search matching display"""
        self.show_search_results()
        self.update_size()

    def update_size(self):
        if self.text_input.isVisible():
            self.unit_selection_display.update_size_position(init_y=widget_y_end(self.text_input))
            max_y = max(self.unit_selection_display.y() + self.unit_selection_display.row_total_height,
                        self.text_input.y() + self.text_input.height())
            max_y += self.settings.panel_build_order.border_size
            max_x = max(self.text_input.x() + self.text_input.width(),
                        self.unit_selection_display.x() + self.unit_selection_display.row_max_width)
            max_x += self.settings.layout.border_size
            self.resize(max_x, max_y)
            self.unit_selection_display.show()
        elif self.back_button.isVisible():
            counters_start_y = max(widget_y_end(self.back_button), widget_y_end(self.unit_picture))
            counters_start_y += self.settings.layout.horizontal_spacing
            self.unit_counters_display.update_size_position(init_y=counters_start_y)
            max_y = max(self.unit_counters_display.y() + self.unit_counters_display.row_total_height,
                        self.back_button.y() + self.back_button.height())
            max_y += self.settings.panel_build_order.border_size
            max_x = max(self.unit_text.x() + self.unit_text.width(),
                        self.unit_counters_display.x() + self.unit_counters_display.row_max_width)
            max_x += self.settings.layout.border_size
            self.resize(max_x, max_y)
            self.unit_counters_display.show()

    def show_search_results(self):
        self.get_search_results()
        self.unit_selection_display.clear()

        valid_count = len(self.search_results)
        if valid_count > 0:
            if not 0 <= self.selection_id < valid_count:
                self.reset_selection()

            for i in range(valid_count):
                unit_name = self.search_results[i]
                if "image_name" in self.unit_counters[unit_name].keys():
                    line = f"@{self.unit_counters[unit_name]['image_name']}@{unit_name}"
                else:
                    line = unit_name
                if i == self.selection_id:
                    self.unit_selection_display.add_row_from_picture_line(
                        parent=self, line=line, labels_settings=[None, QLabelSettings(
                            text_bold=True, text_color=self.settings.layout.configuration.selected_build_order_color)])
                else:
                    self.unit_selection_display.add_row_from_picture_line(parent=self, line=line)
        else:
            if self.selected_unit is None:
                self.unit_selection_display.add_row_from_picture_line(parent=self, line='No Unit selected')

    def get_search_results(self):
        self.search_results = []  # reset the list
        search_text = self.text_input.text()

        if search_text == '':  # no text added
            return

        if search_text == ' ':  # special case: select any build order, up to the limit count
            for count, unit in enumerate(self.unit_counters.keys()):
                if count >= self.max_shown:
                    break
                self.search_results.append(unit)

        else:  # do a fuzzy search for matching build orders
            self.search_results = [match[0] for match in process.extractBests(
                query=search_text,
                choices=self.unit_counters.keys(),
                score_cutoff=50,
                limit=self.max_shown
            )]

        # check all elements are unique
        assert len(set(self.search_results)) == len(self.search_results)

    def mouse_hovering(self, mouse_x: int, mouse_y: int):

        if len(self.search_results) < 1 or not self.text_input.isVisible():
            return

        relative_pos = self.mapFromGlobal(QPoint(mouse_x, mouse_y))
        hover_pos = self.unit_selection_display.get_mouse_label_id(relative_pos.x(), relative_pos.y())
        if hover_pos[0] > -1:
            color = self.settings.layout.configuration.hovering_build_order_color
            col = len(self.unit_selection_display.labels[hover_pos[0]]) - 1
            self.unit_selection_display.set_color_label(hover_pos[0], col, color)
            self.selection_id = hover_pos[0]

            if self.previous_hover_id > -1 \
                    and self.previous_hover_id != hover_pos[0]:
                col = len(self.unit_selection_display.labels[self.previous_hover_id]) - 1
                self.unit_selection_display.set_color_label(self.previous_hover_id, col, None)
            self.previous_hover_id = hover_pos[0]

            self.hover_id = hover_pos[0]

    def mousePressEvent(self, event):
        if self.hover_id == -1 or not self.text_input.isVisible():
            return
        self.selection_id = self.hover_id
        self.select()

    def select(self):
        if self.selection_id > len(self.search_results) - 1:
            return
        self.update_counters_display()
        self.show_counters()
        self.update_size()

    def go_back(self):
        self.show_search()

    def reset_selection(self):
        for row_id in range(len(self.search_results)):
            col = len(self.unit_selection_display.labels[row_id]) - 1
            self.unit_selection_display.set_color_label(row_id, col, color=None)
        self.selection_id = 0
        self.previous_hover_id = -1

    def show_search(self):
        self.back_button.hide()
        self.unit_counters_display.hide()
        self.unit_text.hide()
        self.unit_picture.hide()
        self.unit_counters_display.labels = list()
        self.reset_selection()

        self.text_input.show()
        self.unit_selection_display.show()
        self.update_size()

    def show_counters(self):
        self.back_button.show()
        self.unit_counters_display.show()
        self.unit_text.show()
        self.unit_picture.show()
        self.text_input.hide()
        self.unit_selection_display.hide()
        self.update_size()

    def update_counters_display(self):

        selected_unit = self.search_results[self.selection_id]
        unit_info = self.unit_counters[selected_unit]
        next_x = self.back_button.x() + self.back_button.width() + self.settings.layout.action_button_spacing

        if "image_name" in unit_info.keys():

            pixmap: QPixmap = QPixmap((self.unit_icons_folder / unit_info["image_name"]).as_posix())
            self.unit_picture.setPixmap(pixmap.scaledToHeight(self.unit_counters_display.image_height,
                                                              mode=Qt.TransformationMode.SmoothTransformation))
            self.unit_picture.move(QPoint(next_x, self.back_button.y()))
            self.unit_picture.adjustSize()
            next_x = self.unit_picture.x() + self.unit_picture.width() + self.settings.layout.action_button_spacing
            self.unit_picture.show()
        else:
            self.unit_picture = QLabel("", self)
            self.unit_picture.setHidden(True)
            self.unit_picture.hide()
            self.unit_picture.adjustSize()

        self.unit_text.setText(selected_unit)
        self.unit_text.move(QPoint(next_x, self.back_button.y()))
        self.unit_text.setFont(QFont(self.settings.layout.font_police, self.settings.layout.font_size))
        color_default = self.settings.layout.configuration.selected_build_order_color
        color_default_str = f'color: rgb({color_default[0]}, {color_default[1]}, {color_default[2]})'
        self.unit_text.setStyleSheet(color_default_str)
        self.unit_text.adjustSize()
        self.unit_text.show()

        if "weak_vs" in unit_info.keys() and unit_info["weak_vs"] is not None:
            self.unit_counters_display.add_row_from_picture_line(
                parent=self,
                line="\tWeak against",
                labels_settings=[QLabelSettings(text_bold=True)]
            )
            for unit in unit_info["weak_vs"]:
                if unit in self.unit_counters.keys():
                    line = f"@{self.unit_counters[unit]['image_name']}@{unit}"
                else:
                    line = unit
                self.unit_counters_display.add_row_from_picture_line(
                    parent=self,
                    line=line
                )

        if "strong_vs" in unit_info.keys() and unit_info["strong_vs"] is not None:
            self.unit_counters_display.add_row_from_picture_line(
                parent=self,
                line="\tStrong against",
                labels_settings=[QLabelSettings(text_bold=True)]
            )
            for unit in unit_info["strong_vs"]:
                if unit in self.unit_counters.keys():
                    line = f"@{self.unit_counters[unit]['image_name']}@{unit}"
                else:
                    line = unit
                self.unit_counters_display.add_row_from_picture_line(
                    parent=self,
                    line=line
            )


