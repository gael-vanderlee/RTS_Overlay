from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QMainWindow, QLineEdit

from aoe2.aoe2_settings import AoE2OverlaySettings
from common.useful_tools import set_background_opacity, widget_y_end


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
        super().__init__()

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
        # self.text_input.textChanged.connect(None)
        self.text_input.show()

        # window properties and show
        max_width = settings.panel_build_order.border_size + self.text_input.width()
        self.setWindowTitle('Counters Search')
        self.setWindowIcon(QIcon(icon_path))
        self.resize(max_width + settings.panel_build_order.border_size, widget_y_end(self.text_input) + settings.panel_build_order.border_size)
        set_background_opacity(self, settings.panel_build_order.color_background, settings.panel_build_order.opacity)
        self.show()

    def update_display(self):
        """Update the build order search matching display"""
        self.obtain_build_order_search()
        self.config_panel_layout()

    def obtain_build_order_search(self, key_condition: dict = None):
        """Obtain the valid build order from search bar

        Parameters
        ----------
        key_condition   dictionary with the keys to look for and their value (to consider as valid), None to skip it
        """
        self.get_valid_build_orders(key_condition)
        valid_count = len(self.valid_build_orders)
        self.build_order_selection.clear()

        if valid_count > 0:
            assert 0 <= self.build_order_selection_id < valid_count

            for i in range(valid_count):
                if i == self.build_order_selection_id:
                    self.build_order_selection.add_row_from_picture_line(
                        parent=self, line=self.valid_build_orders[i], labels_settings=[QLabelSettings(
                            text_bold=True, text_color=self.settings.layout.configuration.selected_build_order_color)])
                else:
                    self.build_order_selection.add_row_from_picture_line(parent=self, line=self.valid_build_orders[i])
        else:
            if self.selected_build_order is None:
                self.build_order_selection.add_row_from_picture_line(parent=self, line='no build order')

