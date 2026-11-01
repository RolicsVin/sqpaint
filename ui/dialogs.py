from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
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