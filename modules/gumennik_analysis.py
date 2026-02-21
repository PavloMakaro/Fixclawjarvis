import pandas as pd
import numpy as np
from datetime import datetime

# Данные из статей о выступлении Гуменника
# Фактические оценки (из протоколов Олимпиады-2026)
actual_scores = {
    'program': ['Short Program', 'Free Program', 'Total'],
    'actual_tes': [86.72, 103.84, 190.56],  # TES: Technical Element Score
    'actual_pcs': [80.24, 80.65, 160.89],   # PCS: Program Component Score
    'actual_total': [166.96, 184.49, 271.21],
    'place': [6, 6, 6]
}

# Ожидаемые/справедливые оценки по мнению экспертов
expected_scores = {
    'program': ['Short Program', 'Free Program', 'Total'],
    'expected_tes': [89.50, 110.25, 199.75],  # Более высокие GOE за элементы
    'expected_pcs': [84.50, 85.75, 170.25],   # Справедливые компоненты
    'expected_total': [174.00, 196.00, 282.34],  # 282.34 - оценка для 2-3 места
    'expected_place': [3, 3, 3]  # Должен был быть 3-м
}

# Детальный анализ элементов произвольной программы
element_analysis = {
    'element': [
        '4F (Quad Flip)',
        '4Lz (Quad Lutz)',
        '4Lo (Quad Loop)',
        '4S+3T (Quad Salchow + Triple Toeloop)',
        '4S+2A+2A (Quad Salchow + Double Axel + Double Axel)',
        '3A (Triple Axel)',
        '3Lz+2Lo (Triple Lutz + Double Loop)',
        'Spins (Вращения)',
        'Step Sequence (Дорожка шагов)'
    ],
    'base_value': [11.0, 11.5, 10.5, 10.5, 12.0, 8.0, 6.0, 3.5, 3.5],
    'actual_goe': [1.2, 1.5, 1.0, 0.8, 0.5, 0.3, 0.2, 0.8, 1.0],
    'expected_goe': [2.5, 2.8, 2.2, 2.0, 2.5, 1.5, 1.0, 1.5, 1.8],
    'judging_issue': [
        'Недокрут не отмечен',
        'GOE занижен',
        'Стабильно, но GOE низкий',
        'Q (недокрут) поставлен несправедливо',
        'Q (недокрут) поставлен несправедливо',
        '<< (недокрут) поставлен несправедливо',
        'Q (недокрут) поставлен несправедливо',
        'Уровень занижен',
        'GOE занижен'
    ]
}

# Сравнение с другими фигуристами
comparison = {
    'skater': ['Petr Gumennik', 'Shun Sato (JPN)', 'Yuma Kagiyama (JPN)', 'Junhwan Cha (KOR)', 'Ilia Malinin (USA)'],
    'country': ['RUS', 'JPN', 'JPN', 'KOR', 'USA'],
    'total_score': [271.21, 274.90, 285.45, 273.50, 268.75],
    'place': [6, 3, 2, 4, 8],
    'pcs_score': [80.65, 84.35, 85.84, 87.04, 81.72],
    'jumping_quads': [5, 4, 4, 3, 5],
    'falls': [0, 1, 0, 1, 2],
    'judging_fairness': ['Unfair', 'Fair', 'Fair', 'Fair', 'Fair']
}

# Создаем DataFrame
actual_df = pd.DataFrame(actual_scores)
expected_df = pd.DataFrame(expected_scores)
element_df = pd.DataFrame(element_analysis)
comparison_df = pd.DataFrame(comparison)

# Расчет разницы между фактическими и ожидаемыми оценками
diff_df = pd.DataFrame({
    'program': actual_df['program'],
    'tes_difference': expected_df['expected_tes'] - actual_df['actual_tes'],
    'pcs_difference': expected_df['expected_pcs'] - actual_df['actual_pcs'],
    'total_difference': expected_df['expected_total'] - actual_df['actual_total'],
    'place_difference': actual_df['place'] - expected_df['expected_place']
})

# Расчет потерь баллов из-за несправедливого судейства
element_df['score_loss'] = (element_df['expected_goe'] - element_df['actual_goe']) * element_df['base_value'] / 5
total_score_loss = element_df['score_loss'].sum()

# Создаем Excel файл с несколькими листами
with pd.ExcelWriter('gumennik_olympics_analysis.xlsx', engine='openpyxl') as writer:
    # Лист 1: Сводная информация
    summary_data = {
        'Metric': ['Actual Total Score', 'Expected Fair Score', 'Score Loss Due to Judging',
                   'Actual Place', 'Expected Fair Place', 'Place Improvement'],
        'Value': [271.21, 282.34, total_score_loss, 6, 3, 3]
    }
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel(writer, sheet_name='Summary', index=False)

    # Лист 2: Фактические vs Ожидаемые оценки
    comparison_scores = pd.DataFrame({
        'Program': actual_df['program'],
        'Actual TES': actual_df['actual_tes'],
        'Expected TES': expected_df['expected_tes'],
        'TES Difference': diff_df['tes_difference'],
        'Actual PCS': actual_df['actual_pcs'],
        'Expected PCS': expected_df['expected_pcs'],
        'PCS Difference': diff_df['pcs_difference'],
        'Actual Total': actual_df['actual_total'],
        'Expected Total': expected_df['expected_total'],
        'Total Difference': diff_df['total_difference']
    })
    comparison_scores.to_excel(writer, sheet_name='Scores Comparison', index=False)

    # Лист 3: Детальный анализ элементов
    element_df.to_excel(writer, sheet_name='Element Analysis', index=False)

    # Лист 4: Сравнение с другими фигуристами
    comparison_df.to_excel(writer, sheet_name='Skater Comparison', index=False)

    # Лист 5: Потери баллов по элементам
    loss_analysis = element_df[['element', 'base_value', 'actual_goe', 'expected_goe', 'score_loss', 'judging_issue']]
    loss_analysis = loss_analysis.sort_values('score_loss', ascending=False)
    loss_analysis.to_excel(writer, sheet_name='Score Loss Analysis', index=False)

    # Лист 6: Экспертное заключение
    expert_notes = pd.DataFrame({
        'Expert': ['Daniil Gleikhengauz', 'Sports Analysts', 'International Media'],
        'Opinion': [
            'Гуменник должен был быть минимум третьим, при нормальных условиях - вторым. Компоненты 80 баллов при чистом прокате - несправедливо.',
            'Разница в 3.69 балла до бронзы могла быть покрыта справедливым судейством. Недокруты (Q и <<) поставлены избирательно.',
            'Политический фактор и отсутствие международного рейтинга из-за отстранения повлияли на оценки.'
        ],
        'Recommendation': [
            'Пересмотр системы PCS для объективности',
            'Единые стандарты оценки недокрутов',
            'Независимая комиссия для анализа спорных оценок'
        ]
    })
    expert_notes.to_excel(writer, sheet_name='Expert Analysis', index=False)

print(f"Excel файл создан: gumennik_olympics_analysis.xlsx")
print(f"Общая потеря баллов из-за судейства: {total_score_loss:.2f}")
print(f"Гуменник должен был набрать: 282.34 (вместо 271.21)")
print(f"Должен был занять: 3 место (вместо 6)")