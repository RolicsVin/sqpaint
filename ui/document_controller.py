"""Контроллер операций с документом и проектом.

Здесь сосредоточены пользовательские сценарии открытия/создания/сохранения,
импорта/экспорта и редактирования слоёв. DomainWindow отвечает за сборку UI
и передаёт контроллеру доступ к уже созданным виджетам.
"""
import os
import sqlite3

from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QDialog, QMessageBox

from core.exporter import Exporter
from ui.selfie_dialog import SelfieDialog
from ui.dialogs import *


class DocumentController:
    """Реализует сценарии работы с документом, не создавая Qt-интерфейс."""

    def __init__(self, window):
        self.window = window

    @property
    def w(self):
        return self.window

    def _history_begin(self):
        return self.w.history_controller.begin()

    def _history_commit(self, before, label: str) -> None:
        self.w.history_controller.commit(before, label)

    def create_project(self) -> None:
        values = ask_new_project(self.w)
        if values is None:
            return
        name, width, height, supports_transparency, max_undo_steps = values
        path = ask_save_project_path(self.w, name)
        if not path:
            return
        if os.path.exists(path):
            show_file_exists(self.w)
            return
        try:
            project = self.w.database.create(path, name, width, height, supports_transparency, max_undo_steps)
            project.create_layer(fill=0 if supports_transparency else 0xFFFFFFFF)
            self.w.database.save(project)
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as error:
            show_create_error(self.w, error)
            return
        self.w.set_project(project)

    def open_project(self) -> None:
        self.open_project_path(ask_open_project_path(self.w))

    def open_project_path(self, path: str) -> None:
        if not path:
            return
        try:
            with OperationDialog(self.w, "Файл открывается...", "Opening file..."):
                project = self.w.database.load(path)
                self.w.set_project(project)
        except (OSError, sqlite3.Error, ValueError, TypeError, RuntimeError) as error:
            show_open_error(self.w, error)
            return

    def save(self) -> None:
        if self.w.project is None:
            return
        self.w._commit_pending_transform()
        self.w.history_controller.flush_pending()
        try:
            with OperationDialog(self.w, "Файл сохраняется...", "Saving file..."):
                self.w.database.save(
                    self.w.project, self.w.history_controller.export_for_save()
                )
            self.w.history_controller.mark_saved()
        except (OSError, sqlite3.Error, RuntimeError, ValueError, MemoryError) as error:
            show_save_error(self.w, error)

    def save_as(self) -> None:
        if self.w.project is None:
            return
        self.w._commit_pending_transform()
        self.w.history_controller.flush_pending()
        path = ask_save_as_path(self.w, self.w.project.get_name())
        if not path:
            return
        if os.path.exists(path):
            show_file_exists(self.w)
            return
        try:
            with OperationDialog(self.w, "Файл сохраняется...", "Saving file..."):
                project = self.w.database.save_as(
                    path, self.w.project, self.w.history_controller.export_for_save()
                )
                self.w.set_project(project)
        except (OSError, sqlite3.Error, ValueError, RuntimeError, MemoryError) as error:
            show_save_error(self.w, error)

    def change_canvas_size(self) -> None:
        project, canvas = self.w.project, self.w.canvas
        if project is None or canvas is None:
            return
        new_size = ask_canvas_size(self.w, project.get_width(), project.get_height())
        if new_size is None:
            return
        width, height = new_size
        if (width, height) == (project.get_width(), project.get_height()):
            return
        before = self._history_begin()
        try:
            project.resize(width, height)
            canvas.set_document_size(width, height)
            self._history_commit(before, "ResizeCanvas")
        except (MemoryError, ValueError, RuntimeError) as error:
            QMessageBox.critical(
                self.w, self.w._tr("Размер холста", "Canvas size"),
                self.w._tr(
                    f"Не удалось изменить размер холста.\\n\\n{error}",
                    f"Could not resize the canvas.\\n\\n{error}",
                ),
            )
            return
        self.w.canvas_view.viewport().update()
        self.w.canvas_view.zoom_changed.emit(round(self.w.canvas_view.zoom * 100))

    def crop_document(self, rect) -> None:
        project, canvas = self.w.project, self.w.canvas
        if project is None or canvas is None:
            return
        self.w._commit_pending_transform()
        before = self._history_begin()
        try:
            project.crop(rect.x(), rect.y(), rect.width(), rect.height())
            self._history_commit(before, "CropCanvas")
            canvas.set_document_size(rect.width(), rect.height())
            canvas.update()
            self.w.canvas_view.viewport().update()
        except (ValueError, MemoryError, RuntimeError) as error:
            QMessageBox.warning(
                self.w, self.w._tr("Кадрирование", "Crop"),
                self.w._tr(
                    f"Не удалось кадрировать холст:\\n{error}",
                    f"Could not crop the canvas:\\n{error}",
                ),
            )

    def add_layer(self) -> None:
        project, canvas, panel = self.w.project, self.w.canvas, self.w.layer_panel
        if project is None or canvas is None:
            return
        before = self._history_begin()
        layer = project.create_layer()
        self._history_commit(before, "AddLayer")
        index = project.get_layers().index(layer)
        canvas.set_layers(project.get_layers(), active=index)
        panel.set_layers(project.get_layers())
        panel.select_layer(index)

    def remove_layer(self, layer) -> None:
        project, canvas = self.w.project, self.w.canvas
        if project is None or canvas is None or layer not in project.get_layers():
            return
        if len(project.get_layers()) <= 1:
            show_last_layer_info(self.w)
            return
        if not confirm_delete_layer(self.w, layer.get_name()):
            return
        old_index = project.get_layers().index(layer)
        before = self._history_begin()
        if not project.remove_layer(layer):
            return
        self._history_commit(before, "DeleteLayer")
        self._sync_layers(min(old_index, len(project.get_layers()) - 1))

    def move_layer(self, source, target, insert_before: bool) -> None:
        project = self.w.project
        if project is None or self.w.canvas is None:
            return
        before = self._history_begin()
        if not project.move_layer(source, target, insert_before):
            return
        self._history_commit(before, "MoveLayer")
        selected = self.w.layer_panel.selected_layer
        index = project.get_layers().index(selected) if selected in project.get_layers() else 0
        self._sync_layers(index)

    def set_layer_visibility(self, layer, visible: bool) -> None:
        project = self.w.project
        if project is not None and self.w.canvas is not None:
            before = self._history_begin()
            if project.set_layer_visibility(layer, visible):
                self._history_commit(before, "SetLayerVisibility")
                self.w.canvas.update()

    def rename_layer(self, layer, name: str) -> None:
        project = self.w.project
        if project is None:
            return
        before = self._history_begin()
        if project.rename_layer(layer, name):
            self._history_commit(before, "RenameLayer")
            self.w.layer_panel.refresh_layer_name(layer)

    def select_layer(self, index: int) -> None:
        self.w._commit_pending_transform()
        if self.w.canvas is not None:
            self.w.canvas.set_active_layer(index)

    def _sync_layers(self, active_index: int) -> None:
        layers = self.w.project.get_layers()
        self.w.canvas.set_layers(layers, active=active_index)
        self.w.layer_panel.set_layers(layers)
        self.w.layer_panel.select_layer(active_index)

    def import_image(self) -> None:
        project, canvas = self.w.project, self.w.canvas
        if project is None or canvas is None:
            return
        path = ask_import_image_path(self.w)
        if not path:
            return
        image = QImage(path)
        if image.isNull():
            QMessageBox.warning(
                self.w, self.w._tr("Вставить как слой", "Paste as layer"),
                self.w._tr(
                    "Не удалось открыть выбранное изображение.",
                    "Could not open the selected image.",
                ),
            )
            return
        before = self._history_begin()
        layer = project.create_layer("Импорт")
        self._history_commit(before, "AddImportedLayer")
        index = project.get_layers().index(layer)
        canvas.set_layers(project.get_layers(), active=index)
        self.w.layer_panel.set_layers(project.get_layers())
        self.w.layer_panel.select_layer(index)
        canvas.begin_image_transform(image)

    def create_project_from_image(self) -> None:
        image_path = ask_import_image_path(self.w)
        if not image_path:
            return
        image = QImage(image_path)
        if image.isNull():
            QMessageBox.warning(
                self.w, self.w._tr("Импорт изображения", "Import image"),
                self.w._tr(
                    "Не удалось открыть выбранное изображение.",
                    "Could not open the selected image.",
                ),
            )
            return
        name = os.path.splitext(os.path.basename(image_path))[0] or "Импорт"
        path = ask_save_project_path(self.w, name)
        if not path:
            return
        if os.path.exists(path):
            show_file_exists(self.w)
            return
        try:
            project = self.w.database.create(path, name, image.width(), image.height())
            project.create_layer("Импорт", image)
            self.w.database.save(project)
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as error:
            show_create_error(self.w, error)
            return
        self.w.set_project(project)

    def take_selfie(self) -> None:
        project, canvas = self.w.project, self.w.canvas
        if project is None or canvas is None:
            return
        try:
            dialog = SelfieDialog(self.w)
        except Exception as error:
            QMessageBox.warning(
                self.w, self.w._tr("Веб-камера", "Webcam"),
                self.w._tr(
                    "Не удалось запустить камеру. Проверьте подключение и разрешения.\\n\\n"
                    f"{error}",
                    "Could not start the camera. Check the connection and permissions.\\n\\n"
                    f"{error}",
                ),
            )
            return
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        image = dialog.get_image()
        if image is None or image.isNull():
            return
        before = self._history_begin()
        layer = project.create_layer("Селфи", image)
        self._history_commit(before, "AddSelfieLayer")
        index = project.get_layers().index(layer)
        canvas.set_layers(project.get_layers(), active=index)
        self.w.layer_panel.set_layers(project.get_layers())
        self.w.layer_panel.select_layer(index)

    def export_image(self, image_format: str) -> None:
        if self.w.canvas is None:
            return
        self.w._commit_pending_transform()
        path = ask_export_image_path(self.w, image_format)
        if not path:
            return
        image = self.w.canvas.get_image()
        if not Exporter.export(image, path, image_format):
            QMessageBox.critical(
                self.w, self.w._tr("Экспорт изображения", "Export image"),
                self.w._tr(
                    f"Не удалось сохранить изображение:\\n{path}",
                    f"Could not save the image:\\n{path}",
                ),
            )

    def open_file_info(self) -> None:
        project = self.w.project
        if project is None:
            return
        show_file_info(self.w, project.get_path())
