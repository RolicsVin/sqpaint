from PyQt6.QtGui import QColor, QImage


class Fill:
    """Инструмент заливки связанной области изображения."""

    def press(
        self,
        image: QImage,
        pos,
        last_pos,
        color: QColor,
        size: int = 1,
    ) -> None:
        x, y = pos.x(), pos.y()

        if image.isNull() or not (0 <= x < image.width() and 0 <= y < image.height()):
            return

        fill_color = QColor(color)
        target_rgba = image.pixelColor(x, y).rgba()

        # Нет смысла заливать область тем же цветом.
        if target_rgba == fill_color.rgba():
            return

        width = image.width()
        height = image.height()
        # Scanline flood fill: обрабатываем горизонтальные отрезки,
        # а не помещаем в стек каждый пиксель отдельно.
        stack = [(x, y)]

        while stack:
            seed_x, seed_y = stack.pop()

            if image.pixelColor(seed_x, seed_y).rgba() != target_rgba:
                continue

            left = seed_x
            while left > 0 and image.pixelColor(left - 1, seed_y).rgba() == target_rgba:
                left -= 1

            right = seed_x
            while right + 1 < width and image.pixelColor(right + 1, seed_y).rgba() == target_rgba:
                right += 1

            for current_x in range(left, right + 1):
                image.setPixelColor(current_x, seed_y, fill_color)

            # Добавляем начала непрерывных целевых отрезков
            # на строках сверху и снизу.
            for adjacent_y in (seed_y - 1, seed_y + 1):
                if not 0 <= adjacent_y < height:
                    continue

                current_x = left
                while current_x <= right:
                    while (
                        current_x <= right
                        and image.pixelColor(current_x, adjacent_y).rgba() != target_rgba
                    ):
                        current_x += 1

                    if current_x <= right:
                        stack.append((current_x, adjacent_y))
                        while (
                            current_x <= right
                            and image.pixelColor(current_x, adjacent_y).rgba() == target_rgba
                        ):
                            current_x += 1
