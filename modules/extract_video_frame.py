import cv2
import sys
import os

def extract_frame(video_path, output_path='frame.jpg', frame_time=2):
    """
    Извлекает кадр из видео в указанное время (в секундах)
    """
    try:
        # Проверяем существование файла
        if not os.path.exists(video_path):
            return f"Файл не найден: {video_path}"

        # Открываем видео
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return "Не удалось открыть видеофайл"

        # Получаем FPS и общее количество кадров
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if fps == 0:
            fps = 30  # значение по умолчанию

        # Вычисляем номер кадра для извлечения
        target_frame = int(frame_time * fps)

        # Устанавливаем позицию
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

        # Читаем кадр
        ret, frame = cap.read()

        if not ret:
            # Если не удалось, пробуем первый кадр
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()

        if ret:
            # Сохраняем кадр
            cv2.imwrite(output_path, frame)
            result = f"Кадр сохранен как {output_path}"
        else:
            result = "Не удалось извлечь кадр из видео"

        # Освобождаем ресурсы
        cap.release()
        return result

    except Exception as e:
        return f"Ошибка: {str(e)}"

if __name__ == "__main__":
    # Тестирование функции
    video_path = "downloads/#TikTokFilmTVCompetition #filmbreaker #moviereview #usmovies .mp4"
    result = extract_frame(video_path)
    print(result)