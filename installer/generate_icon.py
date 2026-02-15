"""Генерация иконки Normocontrol (normocontrol.ico).

Создаёт ICO-файл с несколькими размерами (16, 32, 48, 64, 128, 256).
Дизайн: тёмно-синий щит/документ с белой буквой «N» и зелёной галочкой.
"""

from PIL import Image, ImageDraw, ImageFont
import math
import os


def create_icon(size: int) -> Image.Image:
    """Создать одну иконку заданного размера."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = max(1, size // 16)
    s = size  # shorthand

    # === ФОН: скруглённый прямоугольник (документ) ===
    # Основной цвет — тёмно-синий (#1a3a5c)
    bg_color = (26, 58, 92, 255)
    corner_r = max(2, s // 8)

    # Рисуем скруглённый прямоугольник
    draw.rounded_rectangle(
        [margin, margin, s - margin - 1, s - margin - 1],
        radius=corner_r,
        fill=bg_color,
    )

    # === ЗАГНУТЫЙ УГОЛОК (верхний правый — эффект документа) ===
    fold_size = max(3, s // 5)
    fold_x = s - margin - fold_size
    fold_y = margin

    # Треугольник-уголок (светлее)
    fold_color = (200, 215, 230, 255)
    fold_shadow = (15, 45, 75, 255)

    # Тень загиба
    draw.polygon(
        [(fold_x, fold_y), (s - margin - 1, fold_y + fold_size), (fold_x, fold_y + fold_size)],
        fill=fold_shadow,
    )
    # Сам загнутый уголок
    draw.polygon(
        [(fold_x, fold_y), (s - margin - 1, fold_y), (s - margin - 1, fold_y + fold_size)],
        fill=fold_color,
    )

    # === БУКВА «N» — белая, крупная ===
    n_color = (255, 255, 255, 255)

    # Попытка использовать системный шрифт
    font_size = int(s * 0.48)
    font = None
    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf",    # Arial Bold
        "C:/Windows/Fonts/arial.ttf",       # Arial
        "C:/Windows/Fonts/calibrib.ttf",    # Calibri Bold
        "C:/Windows/Fonts/segoeui.ttf",     # Segoe UI
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except Exception:
                continue

    if font is None:
        font = ImageFont.load_default()

    # Центрируем букву N (чуть левее и ниже центра из-за загиба)
    text = "N"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    tx = (s - tw) // 2 - max(1, s // 20)
    ty = (s - th) // 2 + max(1, s // 12)

    draw.text((tx, ty), text, fill=n_color, font=font)

    # === ЗЕЛЁНАЯ ГАЛОЧКА (нижний правый угол) ===
    check_color = (46, 204, 113, 255)        # Зелёный
    check_outline = (39, 174, 96, 255)       # Тёмно-зелёный

    # Круг-подложка для галочки
    cr = max(4, s // 4)  # радиус круга
    cx = s - margin - cr + max(1, s // 16)
    cy = s - margin - cr + max(1, s // 16)

    # Белый круг + зелёная заливка
    draw.ellipse(
        [cx - cr, cy - cr, cx + cr, cy + cr],
        fill=check_color,
        outline=(255, 255, 255, 255),
        width=max(1, s // 32),
    )

    # Галочка внутри круга (белая)
    check_w = max(1, cr // 5)

    # Точки галочки (относительно центра круга)
    p1 = (cx - cr * 0.4, cy)                  # Начало (слева)
    p2 = (cx - cr * 0.1, cy + cr * 0.35)      # Излом (внизу)
    p3 = (cx + cr * 0.45, cy - cr * 0.35)     # Конец (справа вверху)

    draw.line([p1, p2], fill=(255, 255, 255, 255), width=check_w)
    draw.line([p2, p3], fill=(255, 255, 255, 255), width=check_w)

    # === ЛИНИИ-СТРОЧКИ (имитация текста документа) ===
    if s >= 48:
        line_color = (120, 160, 200, 150)
        line_y_start = ty - max(2, s // 8)
        line_h = max(1, s // 48)
        line_gap = max(3, s // 16)
        line_x1 = margin + max(3, s // 8)
        line_x2 = fold_x - max(3, s // 10)

        for i in range(min(3, max(1, (line_y_start - margin - corner_r) // line_gap))):
            ly = margin + corner_r + max(2, s // 12) + i * line_gap
            if ly < line_y_start - line_gap // 2:
                lx2 = line_x2 if i > 0 else line_x2 - fold_size  # первая строка короче (загиб)
                draw.rounded_rectangle(
                    [line_x1, ly, lx2, ly + line_h],
                    radius=line_h // 2,
                    fill=line_color,
                )

    return img


def main():
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    print("Генерация иконки Normocontrol...")
    for sz in sizes:
        img = create_icon(sz)
        images.append(img)
        print(f"  {sz}x{sz} — OK")

    # Путь к .ico — в корне проекта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    ico_path = os.path.join(project_root, "normocontrol.ico")

    # Сохраняем ICO (первое изображение = 256x256, остальные как доп. размеры)
    images[-1].save(
        ico_path,
        format="ICO",
        sizes=[(sz, sz) for sz in sizes],
        append_images=images[:-1],
    )

    print(f"\nГотово: {ico_path}")
    print(f"Размеры: {', '.join(f'{s}x{s}' for s in sizes)}")

    # Также сохранить PNG 256x256 для превью
    png_path = os.path.join(script_dir, "normocontrol_preview.png")
    images[-1].save(png_path, format="PNG")
    print(f"Превью: {png_path}")


if __name__ == "__main__":
    main()
