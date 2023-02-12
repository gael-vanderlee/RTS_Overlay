from PyQt6.QtGui import QFont, QIcon, QShortcut, QKeySequence
from PyQt6.QtWidgets import QMainWindow, QLineEdit
from PyQt6.QtCore import Qt
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

        self.text_input = QLineEdit(self)
        self.text_input.resize(settings.layout.configuration.counter_search_size[0],
                                       settings.layout.configuration.counter_search_size[1])
        self.text_input.setStyleSheet(qwidget_color_default_str)
        self.text_input.setFont(QFont(settings.layout.font_police, settings.layout.font_size))
        self.text_input.setToolTip('Unit that you want to counter')
        self.text_input.move(settings.panel_build_order.border_size, settings.panel_build_order.border_size)
        self.text_input.textChanged.connect(self.update_search)
        self.text_input.show()

        image_folder = Path(__file__).resolve().parent.parent / "pictures" / "aoe2" / "unit_icons"
        self.unit_selection_display = MultiQLabelDisplay(
            font_police=settings.layout.font_police,
            font_size=settings.layout.font_size,
            border_size=settings.layout.border_size,
            vertical_spacing=settings.layout.configuration.build_order_selection_vertical_spacing,
            color_default=settings.layout.color_default,
            image_height=settings.layout.build_order.image_height,
            game_pictures_folder=image_folder.as_posix()
        )

        # window properties and show
        # TODO position next to the parent window
        max_width = settings.panel_build_order.border_size + self.text_input.width()
        self.setWindowTitle('Counters Search')
        self.setWindowIcon(QIcon(icon_path))
        self.resize(
            max_width + settings.panel_build_order.border_size,
            widget_y_end(self.text_input) + settings.panel_build_order.border_size
        )
        set_background_opacity(self, settings.panel_build_order.color_background, settings.panel_build_order.opacity)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.show()

        self.search_results = None
        self.max_shown = 10
        self.selection_id = 0
        self.selected_unit = None
        self.settings = settings

        # Esc hotkey
        QShortcut(QKeySequence("ESC"), self).activated.connect(self.close)

    def update_search(self):
        """Update the build order search matching display"""
        self.obtain_build_order_search()
        self.update_size()

    def update_size(self):
        self.unit_selection_display.show()
        self.unit_selection_display.update_size_position(init_y=widget_y_end(self.text_input))
        max_y = self.unit_selection_display.y() + self.unit_selection_display.row_total_height
        self.resize(self.width(), max_y + self.settings.panel_build_order.border_size)

    def obtain_build_order_search(self):
        self.get_search_results()
        self.unit_selection_display.clear()

        valid_count = len(self.search_results)
        if valid_count > 0:
            assert 0 <= self.selection_id < valid_count

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


