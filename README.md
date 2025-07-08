## **Фрації депутатів**

**Голосування депутатів КМР**

    https://kmr.gov.ua/uk/result_golosuvanya?title=&field_start_date_n_h_value%5Bmin%5D=&field_start_date_n_h_value%5Bmax%5D=&page=10

Вибори -  **25 жовтня 2020 року**

1 сесія 9 скликання - 03.12.2020

Станом на 25 лютого 2025 року цей файл тут:

[](https://kmr.gov.ua/uk/result_golosuvanya?title=&field_start_date_n_h_value%5Bmin%5D=&field_start_date_n_h_value%5Bmax%5D=&page=19)[https://kmr.gov.ua/uk/result_golosuvanya?title=&amp;field_start_date_n_h_value[min]=&amp;field_start_date_n_h_value[max]=&amp;page=19](https://kmr.gov.ua/uk/result_golosuvanya?title=&field_start_date_n_h_value%5Bmin%5D=&field_start_date_n_h_value%5Bmax%5D=&page=19)

## **PDF голосування** (26/10/2006 - Now)

## **Перші структуровані дані КМР у форматі XLSX**

**(3/12/2020 - 22/07/2021):**

Серед усіх результатів голосування уперше дані у форматі XLSX з'являються **03.12.2020 (це 1а сесія 9 скликання) і до 22.07.2021** включно.

**03.12.2020** Результати поіменного голосування (структуровані дані) 03.12.2020:

— Станом на 13 жовтня 2024 року це *сторінка  **17** :*

— Cтаном на 27 лютого 2025 року це ст 19

— Станом на 24 травня 2025 року - це ( **03.12.2020** ) сторінка 21

[](https://kmr.gov.ua/uk/result_golosuvanya?title=&field_start_date_n_h_value%5Bmin%5D=&field_start_date_n_h_value%5Bmax%5D=&page=17)[https://kmr.gov.ua/uk/result_golosuvanya?title=&amp;field_start_date_n_h_value[min]=&amp;field_start_date_n_h_value[max]=&amp;page=17](https://kmr.gov.ua/uk/result_golosuvanya?title=&field_start_date_n_h_value%5Bmin%5D=&field_start_date_n_h_value%5Bmax%5D=&page=17)

Останні файли Excel - це **22.07.2021** включно. Станом на 27 лют 2025 це сторінка 16, станом на 24 травня 2025 року - це ст 17.

Станом на 24 травня 2025 року, по факту нам треба range між 16 і 21 сторінкою

## **Перші структуровані дані КМР у форматі JSON (31/08/2021 - Now):**

Прийшла на заміну XLSX, запаковані у ZIP.

Серед усіх результатів голосування уперше дані у форматі JSON з'являються **31.08.2021.**

Станом на 24 травня 2025 року - це сторінка 17

**31.08.2021** [Результати поіменного голосування (структуровані дані) 31.08.2021](https://kmr.gov.ua/sites/default/files/31.08.2021.zip)

**File for parsing JSON files:**

ua_kmr_voting_json_v4.py

Total unique deputies (after normalization): 133

```bash
**Examples of normalized deputy names:**
Deputy ID 1: 'Андронов В.Є.' - Variations: ['Андронов В. Є.', 'Андронов В.Є.']
Deputy ID 2: 'Андрусишин В.Й.' - Variations: ['Андрусишин В. Й.', 'Андрусишин В.Й.']
Deputy ID 3: 'Артеменко С.В.' - Variations: ['Артеменко  С. В.', 'Артеменко  С.В.']
Deputy ID 4: 'Ахметов Р.С.' - Variations: ['Ахметов Р. С.', 'Ахметов Р.С.']
Deputy ID 5: 'Баленко І.М.' - Variations: ['Баленко  І. М.', 'Баленко  І.М.']
Deputy ID 6: 'Банас Д.М.' - Variations: ['Банас  Д. М.', 'Банас  Д.М.']
Deputy ID 7: 'Баняс Ю.В.' - Variations: ['Баняс Ю. В.', 'Баняс Ю.В.']
Deputy ID 8: 'Берікашвілі Н.В.' - Variations: ['Берікашвілі Н. В.', 'Берікашвілі Н.В.']
Deputy ID 9: 'Білоцерковець Д.О.' - Variations: ['Білоцерковець Д. О.', 'Білоцерковець Д.О.']
Deputy ID 10: 'Богатов К.В.' - Variations: ['Богатов  К. В.', 'Богатов  К.В.']
```

У таблиці з питаннями маємо 1)". ...." and 2) ". .. ..” на місці депутатів, але через складну ідентифікацію (фактично ID можна знайти лише в аналогічному PDF форматі голосування, у json ID відсутній), пропоную скіпнути цих депутатів. Відфільтрую усе де є точки такі.
