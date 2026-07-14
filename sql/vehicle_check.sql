/*
  NazoratBot Telegram uchun SQL Server so'rov namunasi.

  Parametr:
    ? = normalizatsiya qilingan davlat raqami, masalan 01A123BB.

  Muhim:
    Quyidagi dbo.* jadval/view nomlarini o'zingizdagi real baza nomlariga moslang.
    So'rov bitta parametr qabul qiladi va bot kutadigan ustunlarni qaytaradi.
*/

DECLARE @plate varchar(20) = ?;

WITH vehicle AS (
    SELECT TOP (1)
        v.plate,
        CASE WHEN v.is_foreign = 1 THEN 'Xorijiy' ELSE 'Milliy' END AS origin,
        CASE
            WHEN v.vehicle_type IN ('TRUCK', 'YUK') THEN 'Yuk mashinasi'
            WHEN v.vehicle_type IN ('BUS', 'AVTOBUS') THEN 'Avtobus'
            WHEN v.vehicle_type IN ('TRAILER', 'TIRKAMA') THEN 'Tirkama'
            WHEN v.vehicle_type IN ('CAR', 'YENGIL') THEN 'Yengil avtomobil'
            ELSE 'Noma''lum'
        END AS vehicle_type
    FROM dbo.vehicle_registry v
    WHERE UPPER(REPLACE(REPLACE(v.plate, ' ', ''), '-', '')) = @plate
),
cargo_docs AS (
    SELECT
        td.plate,
        'Tranzit deklaratsiya' AS doc_type,
        td.declaration_no AS doc_number,
        td.from_post AS doc_from_post,
        CONVERT(varchar(10), td.created_at, 104) AS doc_start_date,
        td.to_post AS doc_to_post,
        CASE
            WHEN td.deadline < GETDATE() THEN CONVERT(varchar(10), td.deadline, 104) + ' da tugagan'
            ELSE CONVERT(varchar(10), td.deadline, 104) + ' gacha'
        END AS doc_deadline,
        CASE WHEN td.deadline < GETDATE() THEN 'Muddati o''tgan' ELSE 'Yuk yetkazib berilmagan' END AS doc_state,
        CASE WHEN td.deadline < GETDATE() THEN 'danger' ELSE 'ok' END AS doc_level
    FROM dbo.transit_declaration td
    WHERE UPPER(REPLACE(REPLACE(td.plate, ' ', ''), '-', '')) = @plate
      AND td.closed_at IS NULL

    UNION ALL

    SELECT
        ek.plate,
        'Eksport 3 qadam' AS doc_type,
        ek.export_no AS doc_number,
        ek.from_post AS doc_from_post,
        CONVERT(varchar(10), ek.created_at, 104) AS doc_start_date,
        ek.exit_post AS doc_to_post,
        CASE
            WHEN ek.deadline < GETDATE() THEN CONVERT(varchar(10), ek.deadline, 104) + ' da tugagan'
            ELSE CONVERT(varchar(10), ek.deadline, 104) + ' gacha'
        END AS doc_deadline,
        CASE WHEN ek.deadline < GETDATE() THEN 'Muddati o''tgan' ELSE 'Yuk yetkazib berilmagan' END AS doc_state,
        CASE WHEN ek.deadline < GETDATE() THEN 'danger' ELSE 'ok' END AS doc_level
    FROM dbo.export_three_step ek
    WHERE UPPER(REPLACE(REPLACE(ek.plate, ' ', ''), '-', '')) = @plate
      AND ek.closed_at IS NULL

    UNION ALL

    SELECT
        y.plate,
        'YUBNK' AS doc_type,
        y.book_no AS doc_number,
        y.from_post AS doc_from_post,
        CONVERT(varchar(10), y.created_at, 104) AS doc_start_date,
        y.to_post AS doc_to_post,
        CASE
            WHEN y.deadline < GETDATE() THEN CONVERT(varchar(10), y.deadline, 104) + ' da tugagan'
            ELSE CONVERT(varchar(10), y.deadline, 104) + ' gacha'
        END AS doc_deadline,
        CASE WHEN y.deadline < GETDATE() THEN 'Muddati o''tgan' ELSE 'Muddati o''tmagan' END AS doc_state,
        CASE WHEN y.deadline < GETDATE() THEN 'danger' ELSE 'ok' END AS doc_level
    FROM dbo.yubnk y
    WHERE UPPER(REPLACE(REPLACE(y.plate, ' ', ''), '-', '')) = @plate
      AND y.closed_at IS NULL
),
commitment AS (
    SELECT
        mb.plate,
        'Majburiyatnoma' AS doc_type,
        mb.commitment_no AS doc_number,
        mb.from_post AS doc_from_post,
        CONVERT(varchar(10), mb.created_at, 104) AS doc_start_date,
        CAST(NULL AS varchar(200)) AS doc_to_post,
        CASE
            WHEN mb.deadline < GETDATE() THEN CONVERT(varchar(10), mb.deadline, 104) + ' da tugagan'
            ELSE CONVERT(varchar(10), mb.deadline, 104) + ' gacha'
        END AS doc_deadline,
        CASE
            WHEN mb.deadline < GETDATE() THEN 'Muddati o''tgan'
            WHEN DATEDIFF(day, GETDATE(), mb.deadline) BETWEEN 0 AND 3 THEN 'Tugashiga 3 kun qoldi'
            ELSE 'Muddati o''tmagan'
        END AS doc_state,
        CASE
            WHEN mb.deadline < GETDATE() THEN 'danger'
            WHEN DATEDIFF(day, GETDATE(), mb.deadline) BETWEEN 0 AND 3 THEN 'warn'
            ELSE 'ok'
        END AS doc_level
    FROM dbo.vehicle_commitment mb
    INNER JOIN vehicle v ON v.plate = UPPER(REPLACE(REPLACE(mb.plate, ' ', ''), '-', ''))
    WHERE UPPER(REPLACE(REPLACE(mb.plate, ' ', ''), '-', '')) = @plate
      AND v.origin = 'Xorijiy'
      AND mb.closed_at IS NULL
),
docs AS (
    /*
      TD/EK/YUBNK bir vaqtda rasmiylashtirilmaydi.
      Agar real bazada bir nechta chiqsa, oxirgi yaratilgan hujjatni tanlash qoidasini shu joyda belgilang.
      Majburiyatnoma faqat xorijiy transport uchun alohida qo'shiladi.
    */
    SELECT * FROM cargo_docs
    UNION ALL
    SELECT * FROM commitment
),
checks AS (
    SELECT
        @plate AS plate,
        CASE WHEN ISNULL(d.debt_amount, 0) > 0 THEN 'warn' ELSE 'ok' END AS debt_level,
        CASE WHEN ISNULL(d.debt_amount, 0) > 0
             THEN 'bor - ' + FORMAT(d.debt_amount, 'N0', 'uz-Latn-UZ') + ' so''m'
             ELSE 'yo''q'
        END AS debt_text,
        CASE WHEN ISNULL(f.fine_count, 0) > 0 THEN 'warn' ELSE 'ok' END AS fine_level,
        CASE WHEN ISNULL(f.fine_count, 0) > 0
             THEN CAST(f.fine_count AS varchar(10)) + ' ta, jami ' + FORMAT(f.fine_amount, 'N0', 'uz-Latn-UZ') + ' so''m'
             ELSE 'yo''q'
        END AS fine_text,
        CASE WHEN b.ban_source IS NOT NULL THEN 'danger' ELSE 'ok' END AS ban_level,
        CASE WHEN b.ban_source IS NOT NULL
             THEN b.ban_source + ' qarori asosida boshqa taqiq mavjud'
             ELSE 'yo''q'
        END AS ban_text
    FROM (SELECT @plate AS plate) p
    LEFT JOIN dbo.customs_debt d ON UPPER(REPLACE(REPLACE(d.plate, ' ', ''), '-', '')) = p.plate
    LEFT JOIN dbo.yhxb_fines f ON UPPER(REPLACE(REPLACE(f.plate, ' ', ''), '-', '')) = p.plate
    LEFT JOIN dbo.exit_bans b ON UPPER(REPLACE(REPLACE(b.plate, ' ', ''), '-', '')) = p.plate
)
SELECT
    v.plate,
    v.origin,
    v.vehicle_type,
    CASE
        WHEN EXISTS (SELECT 1 FROM docs WHERE doc_level = 'danger') OR c.ban_level = 'danger' THEN 'danger'
        WHEN EXISTS (SELECT 1 FROM docs WHERE doc_level = 'warn') OR c.debt_level = 'warn' OR c.fine_level = 'warn' THEN 'warn'
        WHEN EXISTS (SELECT 1 FROM docs) THEN 'info'
        ELSE 'ok'
    END AS status,
    CASE
        WHEN EXISTS (SELECT 1 FROM cargo_docs WHERE doc_level = 'danger')
            THEN 'Nazoratdagi yuk hujjati muddati o''tgan. Belgilangan bojxona postida nazoratdan yechish talab etiladi.'
        WHEN EXISTS (SELECT 1 FROM cargo_docs)
            THEN 'Nazoratdagi yuk hujjati mavjud. Belgilangan bojxona postida nazoratdan yechish talab etiladi.'
        WHEN v.origin = 'Xorijiy' AND NOT EXISTS (SELECT 1 FROM commitment)
            THEN 'Xorijiy transport bo''yicha majburiyatnoma aniqlanmadi. Bojxona postida qayta tekshirish talab etiladi.'
        ELSE 'Transport bo''yicha nazoratdagi yuk hujjati aniqlanmadi.'
    END AS conclusion,
    d.doc_type,
    d.doc_number,
    d.doc_from_post,
    d.doc_start_date,
    d.doc_to_post,
    d.doc_deadline,
    d.doc_state,
    d.doc_level,
    c.debt_level,
    c.debt_text,
    c.fine_level,
    c.fine_text,
    c.ban_level,
    c.ban_text,
    CASE WHEN v.vehicle_type = 'Yuk mashinasi' AND NOT EXISTS (SELECT 1 FROM cargo_docs) THEN 1 ELSE 0 END AS cargo_control_missing_warning,
    0 AS system_error
FROM vehicle v
CROSS JOIN checks c
LEFT JOIN docs d ON UPPER(REPLACE(REPLACE(d.plate, ' ', ''), '-', '')) = v.plate
ORDER BY
    CASE d.doc_type
        WHEN 'Tranzit deklaratsiya' THEN 1
        WHEN 'Eksport 3 qadam' THEN 2
        WHEN 'YUBNK' THEN 3
        WHEN 'Majburiyatnoma' THEN 4
        ELSE 5
    END;
