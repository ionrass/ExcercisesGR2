"""
ToDoApp.py

Simple Todo application using PyQt6.

This file contains two main pieces:
 - TodoModel: a QAbstractListModel that holds the list of todos and
     provides persistence (save/load) as JSON.
 - MainWindow: the QMainWindow that loads the UI (mainwindow.ui) and
     connects UI events to the TodoModel operations.

Comments throughout the file explain what each section and method does.
"""

import json
import os
from datetime import date

# PyQt6 imports
from PyQt6 import uic  # For loading the .ui file created with Qt Designer
from PyQt6.QtCore import QAbstractListModel, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QStyledItemDelegate
from PyQt6.QtGui import QColor, QFontMetrics
from PyQt6.QtWidgets import QStyle

# Path to the file we use to persist todos. Using a simple file in the
# working directory keeps the example minimal.
DB_PATH = "data.db"

# Load the UI definition produced by Qt Designer. This creates a class
# `MainWindowUI` we can instantiate to get all widgets defined in the .ui file.
MainWindowUI, _ = uic.loadUiType("mainwindow.ui")


class TodoModel(QAbstractListModel):
    """A simple list model storing (completed: bool, text: str) tuples.

    The model exposes the todo text via DisplayRole and a tick icon via
    DecorationRole when an item is completed.
    """

    def __init__(self):
        """Initialize the model and load persisted todos.

        We store todos as a list of tuples: (completed_flag, text).
        completed_flag is a boolean (True for done, False for not done).
        """
        super().__init__()

        # Load existing todos or start with an empty list
        # Each todo will be stored as: [completed(bool), text(str), due_date_iso(str|None)]
        # Using list (not tuple) keeps JSON round-trippable without change.
        self.todos = self._load()

        # Load the tick image (as QPixmap) used for DecorationRole.
        # We keep a QPixmap, because the view expects a pixmap/icon for decoration.
        tick_path = "tick.png"
        if os.path.exists(tick_path):
            self.tick = QPixmap(tick_path)
        else:
            # If the file doesn't exist, use None and the view won't display an icon.
            self.tick = None

    def _load(self):
        """Load todos from DB_PATH (JSON file).

        Returns an empty list if the file does not exist or on error.
        """
        try:
            with open(DB_PATH, mode="r", encoding="utf-8") as f:
                raw = json.load(f)

                # Backwards-compatibility: older format might be [completed, text]
                normalized = []
                for item in raw:
                    # If already in new shape (3 items) use as-is
                    if isinstance(item, list) and len(item) == 3:
                        normalized.append(item)
                    elif isinstance(item, list) and len(item) == 2:
                        # convert [status, text] -> [status, text, None]
                        normalized.append([item[0], item[1], None])
                    elif isinstance(item, (list, tuple)) and len(item) == 2:
                        normalized.append([item[0], item[1], None])
                    else:
                        # Unknown shape: skip
                        continue

                return normalized
        except FileNotFoundError:
            # No saved todos yet
            return []
        except Exception:
            # If the file is corrupted or another error occurs, return empty list
            return []

    def _save(self):
        """Persist the current todos list to DB_PATH as JSON.

        After saving we notify any attached views by emitting layoutChanged.
        """
        try:
            with open(DB_PATH, mode="w", encoding="utf-8") as todo_db:
                # Save the list of todos (each is [status, text, due_iso_or_none])
                json.dump(self.todos, todo_db, ensure_ascii=False, indent=2)
        except Exception:
            # For this simple example we silently ignore save errors; a real
            # app should show an error to the user.
            pass

        # Notify views that the model content changed so they refresh.
        self.layoutChanged.emit()

    # QAbstractListModel interface -------------------------------------------------
    def rowCount(self, parent=None):
        """Return the number of todos the view should display."""
        return len(self.todos)

    def data(self, index, role):
        """Return data for each role requested by the view.

        - DisplayRole: return the todo text
        - DecorationRole: return the tick image when completed
        """
        if not index.isValid():
            return None

        row = index.row()
        try:
            status, text, due = self.todos[row]
        except Exception:
            return None

        # Primary text shown in the list
        if role == Qt.ItemDataRole.DisplayRole:
            return text

        # Expose the due date separately via UserRole so a delegate can draw it
        if role == Qt.ItemDataRole.UserRole:
            return due

        if role == Qt.ItemDataRole.DecorationRole and status:
            # If the item is completed and we have a tick image, return it.
            return self.tick

        return None

    # Application operations ------------------------------------------------------
    def add(self, todo_text: str, due_iso: str | None = None):
        """Add a new todo with completed=False and optional due date.

        due_iso should be an ISO date string (YYYY-MM-DD) or None.
        """
        if not todo_text:
            return

        # Append as a list: [status, text, due_iso]
        self.todos.append([False, todo_text, due_iso])
        self._save()

    def delete(self, row: int):
        """Delete the todo at the given row index and save.

        The method accepts an integer row index (not a QModelIndex).
        """
        try:
            del self.todos[row]
        except Exception:
            return

        self._save()

    def complete(self, row: int):
        """Toggle the completion state for the todo at `row` and save.

        Preserves the due date field.
        """
        try:
            status, text, due = self.todos[row]
            self.todos[row] = [not status, text, due]
        except Exception:
            return

        self._save()


class MainWindow(QMainWindow):
    """Main application window that wires UI elements to the model.

    The UI file must define the following widget names (we rely on them):
    - todoView: a QListView to show todos
    - todoEdit: a QLineEdit for entering new todos
    - addButton: a QPushButton to add the typed todo
    - completeButton: a QPushButton to toggle completion of the selected todo
    - deleteButton: a QPushButton to remove the selected todo
    """

    def __init__(self):
        """Initialize the window, set up the UI and connect signals."""
        super().__init__()

        # Create an instance of the UI class generated by uic
        self.ui = MainWindowUI()
        self.ui.setupUi(self)

        # Create the model and attach it to the QListView in the UI
        self.model = TodoModel()
        self.ui.todoView.setModel(self.model)

        # Set a custom delegate so we can draw the due date in red
        class TodoDelegate(QStyledItemDelegate):
            def paint(self, painter, option, index):
                # Retrieve main text and due date from the model
                text = index.data(Qt.ItemDataRole.DisplayRole)
                due = index.data(Qt.ItemDataRole.UserRole)

                # Determine whether this row is overdue (due < today)
                overdue = False
                if due:
                    try:
                        due_date = date.fromisoformat(due)
                        overdue = due_date < date.today()
                    except Exception:
                        overdue = False

                # If the row is selected, draw the selection background.
                # Otherwise, if overdue, draw a light-red background for the whole row.
                if option.state & QStyle.StateFlag.State_Selected:
                    painter.fillRect(option.rect, option.palette.highlight())
                elif overdue:
                    painter.fillRect(option.rect, QColor(255, 200, 200))

                # Prepare font metrics for eliding long text
                fm = QFontMetrics(option.font)
                rect = option.rect.adjusted(4, 0, -4, 0)

                # Reserve space on the right for the due date (approx)
                due_width = 0
                due_text = ""
                if due:
                    due_text = f"Due: {due}"
                    due_width = fm.horizontalAdvance(due_text) + 10

                # Main text area
                main_rect = rect.adjusted(0, 0, -due_width, 0)
                elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, main_rect.width())

                # Determine text colors. If selected use highlightedText color,
                # if overdue (but not selected) use white for contrast on red bg,
                # otherwise use the normal text color. Due date text uses same
                # highlighted color when selected, otherwise a red/orange logic is
                # handled in the model's ForegroundRole; we'll default to red here.
                if option.state & QStyle.StateFlag.State_Selected:
                    text_color = option.palette.highlightedText().color()
                    due_color = option.palette.highlightedText().color()
                elif overdue:
                    text_color = QColor("white")
                    due_color = QColor("white")
                else:
                    text_color = option.palette.text().color()
                    due_color = QColor("red")

                painter.setPen(text_color)
                painter.drawText(main_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided)

                # Draw due date on the right
                if due:
                    due_rect = rect.adjusted(rect.width() - due_width + 2, 0, 0, 0)
                    # If model provided a ForegroundRole for due column, prefer that
                    # color when not selected/overdue; otherwise use due_color.
                    model_due_color = index.data(Qt.ItemDataRole.ForegroundRole)
                    if model_due_color is not None and not (option.state & QStyle.StateFlag.State_Selected or overdue):
                        painter.setPen(model_due_color)
                    else:
                        painter.setPen(due_color)

                    painter.drawText(due_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, due_text)

            def sizeHint(self, option, index):
                fm = QFontMetrics(option.font)
                return fm.size(0, index.data(Qt.ItemDataRole.DisplayRole))

        # Assign the delegate instance to the list view
        self.ui.todoView.setItemDelegate(TodoDelegate(self.ui.todoView))

        # Connect the buttons to local handler methods
        # These methods call the model to perform actions and update the UI
        self.ui.addButton.pressed.connect(self.add)
        self.ui.deleteButton.pressed.connect(self.delete)
        self.ui.completeButton.pressed.connect(self.complete)

    # Handlers connected to the UI ------------------------------------------------
    def add(self):
        """Read text from the input field, add it to the model, and clear input."""
        text = self.ui.todoEdit.text().strip()
        if not text:
            return

        # Read the date from the QDateEdit as ISO string (YYYY-MM-DD)
        # PyQt6 uses Qt.DateFormat for standard formats
        try:
            due_qdate = self.ui.dueDateEdit.date()
            due_iso = due_qdate.toString(Qt.DateFormat.ISODate)
        except Exception:
            due_iso = None

        # Add the todo with the optional due date
        self.model.add(text, due_iso)

        # Clear the text input; keep the due date (user may add many items with same date)
        self.ui.todoEdit.clear()

    def delete(self):
        """Delete the currently selected item in the view."""
        indexes = self.ui.todoView.selectedIndexes()
        if not indexes:
            return

        row = indexes[0].row()
        self.model.delete(row)
        # Clear the selection so the UI is consistent after deletion
        self.ui.todoView.clearSelection()

    def complete(self):
        """Toggle completion state for the selected item."""
        indexes = self.ui.todoView.selectedIndexes()
        if not indexes:
            return

        row = indexes[0].row()
        self.model.complete(row)
        self.ui.todoView.clearSelection()


if __name__ == "__main__":
    # Create and start the Qt application
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()