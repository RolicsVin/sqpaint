from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QLabel,
)


class NewProjectDialog(QDialog):
    """Диалог параметров нового проекта."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новый проект")
        self.setModal(True)

        self.name_edit = QLineEdit("Новый проект", self)

        self.width_spin = QSpinBox(self)
        self.width_spin.setRange(1, 8192)
        self.width_spin.setValue(1920)
        self.width_spin.setSuffix(" px")

        self.height_spin = QSpinBox(self)
        self.height_spin.setRange(1, 8192)
        self.height_spin.setValue(1080)
        self.height_spin.setSuffix(" px")

        form = QFormLayout(self)
        form.addRow("Название:", self.name_edit)
        form.addRow("Ширина:", self.width_spin)
        form.addRow("Высота:", self.height_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def get_values(self) -> tuple[str, int, int]:
        return (
            self.name_edit.text().strip(),
            self.width_spin.value(),
            self.height_spin.value(),
        )


class DeleteLayerDialog(QDialog):
    """Диалог подтверждения удаления слоя."""

    def __init__(self, layer_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Удаление слоя")
        self.setModal(True)

        layout = QFormLayout(self)
        layout.addRow(QLabel(
            f'Вы действительно хотите удалить слой «{layer_name}»?'
        ))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes
            | QDialogButtonBox.StandardButton.No,
            parent=self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Yes).setText("Удалить")
        buttons.button(QDialogButtonBox.StandardButton.No).setText("Отмена")
        buttons.button(QDialogButtonBox.StandardButton.No).setDefault(True)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)