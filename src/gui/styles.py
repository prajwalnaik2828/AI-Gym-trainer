"""
Default UI Styling and Design System for AI Gym Trainer Desktop App.
Easily customizable once new design specifications are provided.
"""

APP_STYLESHEET = """
QMainWindow {
    background-color: #0F172A;
}

QWidget {
    color: #F8FAFC;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 14px;
}

/* Sidebar Navigation */
QListWidget#nav_bar {
    background-color: #1E293B;
    border: none;
    border-radius: 12px;
    padding: 8px;
    outline: none;
}

QListWidget#nav_bar::item {
    height: 48px;
    border-radius: 8px;
    padding-left: 14px;
    margin-bottom: 4px;
    font-weight: 600;
    font-size: 15px;
    color: #94A3B8;
}

QListWidget#nav_bar::item:hover {
    background-color: #334155;
    color: #F8FAFC;
}

QListWidget#nav_bar::item:selected {
    background-color: #3B82F6;
    color: #FFFFFF;
}

/* Card Containers */
QFrame.card {
    background-color: #1E293B;
    border-radius: 12px;
    border: 1px solid #334155;
}

/* Section Header Labels */
QLabel.heading {
    font-size: 20px;
    font-weight: bold;
    color: #F8FAFC;
}

QLabel.subheading {
    font-size: 13px;
    color: #94A3B8;
}

/* Stat Display Card */
QFrame.stat-card {
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 10px;
}

QLabel.stat-title {
    font-size: 12px;
    text-transform: uppercase;
    font-weight: 700;
    color: #94A3B8;
    letter-spacing: 0.5px;
}

QLabel.stat-value {
    font-size: 38px;
    font-weight: 800;
    color: #38BDF8;
}

QLabel.stat-cue {
    font-size: 15px;
    font-weight: 600;
    color: #FDE047;
}

/* Video Feed Container */
QLabel#video_display {
    background-color: #020617;
    border: 2px solid #334155;
    border-radius: 12px;
}

/* Buttons */
QPushButton {
    background-color: #3B82F6;
    color: #FFFFFF;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #2563EB;
}

QPushButton:pressed {
    background-color: #1D4ED8;
}

QPushButton:disabled {
    background-color: #334155;
    color: #64748B;
}

QPushButton#btn_start {
    background-color: #10B981;
}
QPushButton#btn_start:hover {
    background-color: #059669;
}

QPushButton#btn_stop {
    background-color: #EF4444;
}
QPushButton#btn_stop:hover {
    background-color: #DC2626;
}

QPushButton#btn_secondary {
    background-color: #334155;
    color: #E2E8F0;
}
QPushButton#btn_secondary:hover {
    background-color: #475569;
}

/* Inputs & Combos */
QComboBox, QLineEdit, QSpinBox {
    background-color: #0F172A;
    border: 1px solid #475569;
    border-radius: 8px;
    padding: 8px 12px;
    color: #F8FAFC;
    min-height: 22px;
}

QComboBox:focus, QLineEdit:focus {
    border: 1px solid #38BDF8;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #1E293B;
    border: 1px solid #475569;
    selection-background-color: #3B82F6;
    color: #F8FAFC;
    outline: none;
}

/* Checkbox */
QCheckBox {
    spacing: 8px;
    color: #CBD5E1;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #475569;
    background-color: #0F172A;
}

QCheckBox::indicator:checked {
    background-color: #3B82F6;
    border-color: #3B82F6;
}

/* Tables */
QTableWidget {
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 8px;
    gridline-color: #1E293B;
    color: #F8FAFC;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background-color: #3B82F6;
    color: white;
}

QHeaderView::section {
    background-color: #1E293B;
    color: #94A3B8;
    padding: 8px;
    border: none;
    font-weight: 600;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #0F172A;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}
"""
