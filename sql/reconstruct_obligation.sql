WITH obligation AS (
    SELECT json_extract(payload_json, '$.id') AS obligation_id,
           payload_json AS obligation_json
    FROM current_record
    WHERE record_type = 'obligation'
      AND record_id = :obligation_id
),
source_record AS (
    SELECT s.payload_json AS source_json
    FROM current_record s
    JOIN obligation o
      ON s.record_id = json_extract(o.obligation_json, '$.source_id')
    WHERE s.record_type = 'regulatory_source'
),
assessments AS (
    SELECT json_group_array(json(payload_json)) AS assessment_json
    FROM current_record
    WHERE record_type = 'applicability_assessment'
      AND json_extract(payload_json, '$.obligation_id') = :obligation_id
),
controls AS (
    SELECT json_group_array(json(payload_json)) AS control_json
    FROM current_record
    WHERE record_type = 'control'
      AND EXISTS (
          SELECT 1
          FROM json_each(json_extract(payload_json, '$.obligation_ids'))
          WHERE value = :obligation_id
      )
),
evidence AS (
    SELECT json_group_array(json(e.payload_json)) AS evidence_json
    FROM current_record e
    JOIN current_record c
      ON c.record_type = 'control'
     AND EXISTS (
          SELECT 1
          FROM json_each(json_extract(c.payload_json, '$.obligation_ids'))
          WHERE value = :obligation_id
     )
     AND json_extract(e.payload_json, '$.control_id') = c.record_id
    WHERE e.record_type = 'evidence'
)
SELECT
    o.obligation_id,
    o.obligation_json,
    s.source_json,
    COALESCE(a.assessment_json, '[]') AS applicability_assessments,
    COALESCE(c.control_json, '[]') AS controls,
    COALESCE(e.evidence_json, '[]') AS evidence
FROM obligation o
LEFT JOIN source_record s ON 1 = 1
LEFT JOIN assessments a ON 1 = 1
LEFT JOIN controls c ON 1 = 1
LEFT JOIN evidence e ON 1 = 1;
