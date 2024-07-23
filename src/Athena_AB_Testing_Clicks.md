## El primer CTE (Common Table Expression) define un rango de fechas.
 ```sql
WITH

fecha AS (
    SELECT
        cast('2024-01-16 12:30:00' AS timestamp) AS fecha_inicio,
        cast('2024-01-23 12:30:00' AS timestamp) AS fecha_fin
),
 ```


## El segundo CTE selecciona varias columnas de la tabla boti_intent_search y define algunas lógicas para nuevas columnas.
 ```sql
intents as (
    SELECT ts,
        id,
        session_id,
        message_id,
        message,
        results_intent_name,
        results_intent_id,
        parent_intent_id,
        parent_intent_name,
        model_type,
        results_showable,
        results_score,
        rule_id,
        (
            CASE
                WHEN (
                    parent_intent_id IS NOT NULL
                    AND parent_intent_id != ''
                ) THEN parent_intent_id ELSE results_intent_id
            END
        ) mostrado,
        (
            CASE
                WHEN (
                    parent_intent_name IS NOT NULL
                    AND parent_intent_name != ''
                ) THEN parent_intent_name ELSE results_intent_name
            END
        ) mostrado_name
    FROM boti_intent_search
    left join fecha on 1=1
    WHERE ts >= fecha_inicio
        and ts <= fecha_fin
)
 ```

Selecciona columnas de boti_intent_search:
```ts```, ```id```, ```session_id```, ```message_id```, ```message```, ```results_intent_name```, ```results_intent_id```, ```parent_intent_id```, ```parent_intent_name```, ```model_type```, ```results_showable```, ```results_score```, ```rule_id```.

Define dos nuevas columnas ```mostrado``` y ```mostrado_name``` utilizando una expresión **CASE**:
- ```mostrado```: Toma parent_intent_id si no es nulo o vacío, de lo contrario toma results_intent_id.
- ```mostrado_name```: Toma parent_intent_name si no es nulo o vacío, de lo contrario toma results_intent_name.

Filtra los registros por el rango de fechas definido en el CTE **fecha**.

# Consulta Principal
La consulta principal une los datos de ```intents``` con los de ```boti_intent_search_response``` y selecciona los resultados.

```sql
SELECT 
    a.*,
    b.ts AS response_ts,
    b.response_message,
    b.response_intent_id
FROM intents a
    LEFT JOIN fecha ON 1=1
    LEFT JOIN boti_intent_search_response b ON a.id = b.id
    AND b.ts >= fecha_inicio
    AND b.ts <= fecha_fin
ORDER BY a.ts DESC;
```
- Selecciona todas las columnas de ```intents``` (a.*).
- Añade tres columnas de ```boti_intent_search_response``` (b):
    - ```response_ts```: Marca de tiempo de la respuesta.
    - ```response_message```: Mensaje de la respuesta.
    - ```response_intent_id```: ID de la intención de la respuesta.  

Se realiza una **LEFT JOIN** con ```fecha``` (una tabla temporal con una única fila), lo que garantiza que las columnas de fecha (```fecha_inicio```, ```fecha_fin```) estén disponibles en la consulta.  

Se realiza una **LEFT JOIN** con ```boti_intent_search_response``` en base al id de ```intents``` **(a.id = b.id)**, filtrando por el mismo rango de fechas **(b.ts >= fecha_inicio AND b.ts <= fecha_fin)**.  

Los resultados finales se ordenan por ts en orden descendente **(ORDER BY a.ts DESC)**.
