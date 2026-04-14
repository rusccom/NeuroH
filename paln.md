Ниже — **единое финальное ТЗ** для реализации экспериментальной платформы: сама система агента, среда, быстрая и медленная память, цикл эксперимента и операторский мониторинг. Это уже можно отдавать разработчику как **handoff-документ**.

Для среды базовый контракт лучше держать **совместимым с Gymnasium**, потому что это стандартный API для Python-env с `reset()/step()`, а Minigrid подтверждает, что быстрые, простые, настраиваемые 2D grid-world среды с дискретными действиями хорошо подходят для исследовательских задач. В финальной реализации здесь нужен **свой custom env**, а Minigrid — как референс по стилю и API, не как обязательная зависимость. ([Gymnasium][1])

Для live-мониторинга в первой версии основной стек должен быть таким: **FastAPI** как backend/API, **SSE/EventSource** как основной канал телеметрии сервер → браузер, **обычные HTTP POST** для команд оператора, **Apache ECharts** для живых графиков и **Three.js** для 3D-индикатора состояния. EventSource — односторонний канал, хорошо подходит для live-телеметрии и широко поддерживается в браузерах; WebSocket остаётся опциональным расширением на будущее для двустороннего интерактива. ECharts штатно поддерживает dynamic data, а в Three.js для анимационного цикла рекомендуется `setAnimationLoop()`. ([MDN Web Docs][2])

---

# Единое ТЗ v1.0

## Проект: `HomeoGrid Experimental Platform`

## 1. Назначение

Нужно реализовать минимальную, но полноценную экспериментальную платформу, в которой есть:

* простая замкнутая среда;
* простое тело агента;
* внутренние потребности;
* быстрая память текущего эпизода;
* медленная память между эпизодами;
* выбор действия на основе потребностей, памяти и текущего состояния;
* live-мониторинг для обычного оператора;
* запись эксперимента и replay;
* набор метрик и абляций.

Это **не конечная AGI-система**. Это **MVP-платформа для проверки идеи**.

---

## 2. Что именно должна доказать система

Система считается концептуально удачной, если показывает одновременно следующие эффекты:

1. **Потребности действительно управляют поведением.**
   Агент должен переключаться между поиском еды и воды в зависимости от внутреннего дефицита.

2. **Быстрая память помогает внутри эпизода.**
   Найдя ресурс, агент должен заметно быстрее возвращаться к нему в том же эпизоде.

3. **Медленная память помогает между эпизодами.**
   После обучения в знакомом биоме агент должен начинать поиск в правильной области карты раньше, чем baseline без медленной памяти.

4. **Быстрая память умеет переучиваться быстрее медленной.**
   При переносе ресурса в середине эпизода fast-memory должна быстрее перестраивать цель, чем slow-memory.

5. **Мониторинг позволяет оператору видеть всё это онлайн.**
   Оператор должен в реальном времени понимать:

   * жив ли агент;
   * что он ищет;
   * на что опирается;
   * где застрял;
   * насколько система стабильна.

---

## 3. Что не входит в эту версию

В MVP запрещено:

* 3D-мир;
* пиксельное зрение;
* язык, текстовые инструкции, LLM;
* многoагентность;
* непрерывная физика;
* end-to-end монолитная нейросеть;
* внешняя награда вида “дойди до цели X” как основной смысл задачи;
* сложная инфраструктура мониторинга вроде Prometheus/Grafana;
* распределённое исполнение;
* Redis, Kafka, брокеры сообщений;
* несколько активных раннов одновременно.

---

## 4. Главные инварианты системы

Эти правила нельзя ломать даже при рефакторинге.

1. **Быстрая память** хранит конкретику текущего эпизода.
2. **Медленная память** хранит статистическую структуру по биомам между эпизодами.
3. Решение на шаге принимается только из связки:
   `NeedState + BeliefMap + FastMemory + SlowMemory + BodyState`.
4. Агент **никогда** не читает скрытую карту среды напрямую.
5. Медленная память обучается **только через replay/consolidation**, а не напрямую в каждом шаге.
6. Мониторинг не должен блокировать симуляцию.
7. Команды оператора применяются только на границе шага, не в середине `env.step()`.

---

## 5. Общая архитектура

```text
┌─────────────────────────────── ExperimentOrchestrator ───────────────────────────────┐
│                                                                                        │
│   ┌───────────────┐       ┌────────────────────┐       ┌──────────────────────────┐   │
│   │ HomeoGridEnv  │──────▶│      AgentCore     │──────▶│      MonitoringFacade     │   │
│   │ world + body  │◀──────│ decision + memory  │◀──────│ telemetry + alerts + UI  │   │
│   └──────┬────────┘       └──────────┬─────────┘       └──────────┬───────────────┘   │
│          │                           │                             │                   │
│          │                           │                             │                   │
│          ▼                           ▼                             ▼                   │
│   hidden world                metrics / events               stream / record / replay  │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Логика цикла

```text
среда → наблюдение → belief map → потребность → fast/slow память → выбор цели
→ план → действие → новое состояние тела/среды → запись событий → replay → slow memory
```

---

## 6. Технологическая база

### 6.1. Runtime stack

Обязательные Python-зависимости:

* `python`
* `numpy`
* `gymnasium`
* `pyyaml`
* `fastapi`
* `uvicorn`
* `pydantic`

Обязательные dev-зависимости:

* `pytest`
* `mypy`
* `ruff`

Frontend-ассеты:

* локальная копия `echarts`
* локальная копия `three.js`

### 6.2. Ограничения по стеку

* `minigrid` можно держать как **dev/reference dependency**, но не как обязательную runtime-зависимость;
* `torch` запрещён в core-MVP;
* `tensorflow` запрещён;
* React/Vue запрещены;
* все JS-ассеты должны быть локальными, без CDN;
* версии пакетов должны быть зафиксированы в `requirements.lock`.

### 6.3. Сетевые ограничения мониторинга

Для live-телеметрии основной транспорт — SSE. Нужно помнить, что без HTTP/2 у SSE есть низкий лимит одновременных соединений на браузер+домен, поэтому MVP должен быть рассчитан на **одну основную операторскую страницу и 1–2 дополнительные вкладки**, а не на большой wallboard. ([MDN Web Docs][2])

---

## 7. Runtime-модель

### 7.1. Процессная модель

Первая версия работает в **одном Python-процессе**:

* поток 1: ASGI/HTTP сервер FastAPI;
* поток 2: simulation worker;
* общие thread-safe объекты:

  * `MonitoringFacade`
  * `FrameRingBuffer`
  * `CommandBus`
  * `SlowMemory`
  * `RunStateStore`

### 7.2. Почему так

Это упрощает:

* воспроизводимость;
* локальную отладку;
* контроль состояния;
* запись артефактов;
* live-мониторинг.

Для первой версии не нужна многопроцессность. FastAPI сам показывает WebSocket-пример с in-memory connection manager, который подходит только для одного процесса; это совпадает с нашим MVP-ограничением. ([FastAPI][3])

---

## 8. Структура проекта

```text
src/homeogrid/
    domain/
        enums.py
        types.py
        events.py

    config/
        env_config.py
        body_config.py
        reward_config.py
        memory_config.py
        planner_config.py
        monitor_config.py
        experiment_config.py

    env/
        biome_templates.py
        world_state.py
        world_generator.py
        physiology.py
        reward_model.py
        observation_encoder.py
        gym_env.py

    memory/
        interfaces.py
        fast_memory.py
        slow_memory.py
        replay_manager.py

    decision/
        drive_model.py
        biome_inferer.py
        arbiter.py
        explorer_policy.py
        event_detector.py
        status_translator.py

    planning/
        planner.py
        controller.py

    agent/
        belief_map.py
        working_buffer.py
        core.py

    analytics/
        metrics.py
        report_writer.py

    monitoring/
        domain/
            enums.py
            dto.py
            alerts.py
            commands.py
        interfaces.py
        core/
            monitoring_facade.py
            snapshot_builder.py
            alert_engine.py
            frame_ring_buffer.py
            session_recorder.py
            replay_loader.py
            stream_hub.py
        web/
            api.py
            static/
                index.html
                app.js
                charts.js
                map.js
                blob3d.js
                styles.css
                vendor/
                    echarts.min.js
                    three.module.js

    orchestration/
        command_bus.py
        run_state_store.py
        experiment_orchestrator.py

    app/
        main.py
        run.py
        replay.py

tests/
    unit/
    integration/
    monitoring/
    ablation/
```

---

## 9. Правила зависимостей

Импортные зависимости должны быть строго слоистыми.

### Разрешённые зависимости

* `domain` — ни от кого
* `config` → `domain`
* `env` → `domain`, `config`
* `memory` → `domain`, `config`
* `decision` → `domain`, `config`, `memory.interfaces`
* `planning` → `domain`, `config`
* `agent` → `domain`, `config`, `memory`, `decision`, `planning`
* `analytics` → `domain`, `agent`-DTO, `monitoring.interfaces`
* `monitoring.domain` → `domain`
* `monitoring.interfaces` → `monitoring.domain`, `domain`
* `monitoring.core` → `monitoring.domain`, `monitoring.interfaces`, `analytics`, `agent`-DTO
* `monitoring.web` → `monitoring.core`, `monitoring.domain`, `fastapi`
* `orchestration` → всё необходимое
* `app` → всё

### Запрещённые зависимости

* `env` не импортирует `agent`
* `env` не импортирует `monitoring.web`
* `memory` не импортирует `env`
* `planner` не читает hidden map мира
* `agent` не импортирует FastAPI, ECharts, Three.js
* `monitoring.web` не читает hidden map среды напрямую

---

## 10. Конфигурационные объекты

Все конфиги — `dataclass(frozen=True)` и должны загружаться из YAML.

### 10.1. `EnvConfig`

```python
grid_size: int = 11
view_size: int = 5
episode_limit: int = 400
enable_relocation: bool = False
relocation_step: int = 150
relocation_probability: float = 0.25
food_nodes_per_episode: int = 2
water_nodes_per_episode: int = 2
rough_patches_per_episode: int = 3
```

### 10.2. `BodyConfig`

```python
energy_start: int = 70
water_start: int = 70
energy_max: int = 100
water_max: int = 100
base_energy_cost: int = 1
base_water_cost: int = 1
move_extra_energy_cost: int = 1
rough_extra_energy_cost: int = 2
rough_extra_water_cost: int = 1
low_state_threshold: int = 15
low_state_move_extra_energy_cost: int = 1
interact_gain: int = 35
```

### 10.3. `RewardConfig`

```python
energy_setpoint: int = 70
water_setpoint: int = 70
weight_energy: float = 0.5
weight_water: float = 0.5
action_cost_weight: float = 0.02
collision_penalty: float = 0.2
death_penalty: float = 5.0
```

### 10.4. `MemoryConfig`

```python
fast_max_age: int = 80
fast_max_events: int = 256
slow_decay: float = 0.995
slow_conf_threshold: float = 0.15
slow_top_k: int = 8
```

### 10.5. `PlannerConfig`

```python
turn_cost: float = 0.2
rough_cost: float = 3.0
unknown_cost: float = 1.5
max_plan_len: int = 64
```

### 10.6. `MonitorConfig`

```python
ui_hz: int = 5
chart_history_sec: int = 120
frame_buffer_size: int = 600
raw_event_buffer_size: int = 4096
sse_ping_sec: float = 2.0
enable_debug_overlay: bool = False
enable_blob3d: bool = True
max_alerts_in_panel: int = 100
bind_host: str = "127.0.0.1"
bind_port: int = 8000
```

### 10.7. `ExperimentConfig`

```python
run_id: str
base_seed: int = 42
train_episodes: int = 200
eval_episodes_seen: int = 100
eval_episodes_relocation: int = 50
enable_monitoring: bool = True
save_monitor_stream: bool = True
save_metrics: bool = True
run_ablations: bool = True
ablation_modes: list[str] = [
    "full",
    "no_fast",
    "no_slow",
    "no_interoception",
    "no_rough_cost",
    "full_observation"
]
```

---

## 11. Доменная модель

### 11.1. Enum’ы

Обязательные enum’ы:

* `Direction = {N, E, S, W}`
* `ActionType = {TURN_LEFT, TURN_RIGHT, MOVE_FORWARD, INTERACT, WAIT}`
* `CellType = {UNKNOWN, EMPTY, WALL, FOOD, WATER, ROUGH, LANDMARK}`
* `ResourceType = {FOOD, WATER}`
* `BiomeId = {A, B, C, D}`
* `TargetSource = {FAST, SLOW, EXPLORE}`
* `EventType = {RESOURCE_OBSERVED, RESOURCE_CONSUMED, EXPECTATION_VIOLATED, RESOURCE_RELOCATED, COLLISION, DEATH, NEED_SWITCH, BIOME_IDENTIFIED}`

### 11.2. Основные value objects

Обязательные dataclass-объекты:

* `Vec2(x, y)`
* `Pose(x, y, dir)`
* `BodyState(energy, water, last_collision, alive)`
* `NeedState(energy_deficit, water_deficit, active_need, critical)`
* `Observation(tiles, landmark_ids, pose, body, step_idx)`
* `TargetProposal(source, resource_type, confidence, exact_cell, region_cells, stance_pose)`
* `Plan(valid, waypoints, final_dir, cost)`
* `StepInfo(collision, entered_rough, consumed_food, consumed_water, action_cost_energy, action_cost_water, resource_relocated, death_reason)`
* `Transition(prev_obs, action, next_obs, reward, terminated, truncated, info)`
* `SalientEvent(event_type, step_idx, biome_id, pose, resource_type, action, salience, position)`
* `ReplaySample(biome_id, resource_type, position, weight)`
* `EpisodeSummary(episode_id, biome_id, steps, total_reward, died, death_reason)`

---

## 12. Подсистема среды

## 12.1. Общий смысл среды

Среда — это простой 2D мир выживания с двумя внутренними дефицитами:

* `energy`
* `water`

Этого достаточно, чтобы проверить:

* конкуренцию потребностей;
* embodied стоимость действий;
* быструю память внутри эпизода;
* медленную статистическую память между эпизодами.

## 12.2. Геометрия среды

* карта: `11x11`
* рамка по краям: стены
* наблюдение: эгоцентрическое окно `5x5`
* лимит эпизода: `400` шагов
* старт агента: `(5, 6)`, направление `N`
* landmark: `(5, 5)`

## 12.3. Биомы

Нужно четыре биома.

### `Biome A`

* `landmark_id = 1`
* food_center = `(2, 2)`
* water_center = `(8, 8)`
* rough_centers = `[(8,2), (7,3), (8,3)]`

### `Biome B`

* `landmark_id = 2`
* food_center = `(8, 2)`
* water_center = `(2, 8)`
* rough_centers = `[(2,2), (3,2), (2,3)]`

### `Biome C`

* `landmark_id = 3`
* food_center = `(5, 2)`
* water_center = `(5, 8)`
* rough_centers = `[(2,5), (3,5), (2,6)]`

### `Biome D`

* `landmark_id = 4`
* food_center = `(2, 5)`
* water_center = `(8, 5)`
* rough_centers = `[(5,2), (5,3), (6,2)]`

### Правила генерации

* в каждом эпизоде биом выбирается равновероятно;
* координаты ресурсов шумятся в радиусе 1 клетки;
* rough-зоны шумятся аналогично;
* ресурсы не ставятся:

  * на стену,
  * на landmark,
  * на старт агента,
  * друг на друга.

### Mid-episode relocation

Если `enable_relocation=True`, то:

* на шаге `relocation_step` с вероятностью `relocation_probability` один ресурс переносится;
* перенос должен менять локальную фактическую карту;
* агент узнаёт об этом только через несоответствие ожидания и наблюдения.

---

## 13. Объекты среды

## 13.1. `GridWorldState`

**Слой:** `env`
**Зависит от:** `domain.types`, `domain.enums`
**Поля:**

* `biome_id`
* `landmark_id`
* `tiles: np.ndarray[11,11]`
* `pose`
* `body`
* `step_idx`

**Ответственность:**
Единственный источник истины по скрытому состоянию мира.

---

## 13.2. `WorldGenerator`

**Слой:** `env`
**Зависит от:** `EnvConfig`, `BodyConfig`, `BiomeTemplate`, `numpy.random.Generator`

**Метод:**

```python
generate(seed: int | None = None) -> GridWorldState
```

**Обязанности:**

* выбрать биом;
* построить сетку мира;
* поставить стены, landmark, rough, ресурсы;
* создать стартовое `BodyState`;
* вернуть `GridWorldState`.

---

## 13.3. `ObservationEncoder`

**Слой:** `env`
**Зависит от:** `EnvConfig`

**Метод:**

```python
encode(state: GridWorldState) -> Observation
```

**Обязанности:**

* вырезать `5x5` локальное окно;
* повернуть его так, чтобы “вперёд” агента всегда было вверх;
* вложить в observation:

  * `tiles`,
  * `landmark_ids`,
  * `pose`,
  * `body`,
  * `step_idx`.

---

## 13.4. `PhysiologyModel`

**Слой:** `env`
**Зависит от:** `BodyConfig`

**Метод:**

```python
apply(state: GridWorldState, action: ActionType) -> tuple[GridWorldState, StepInfo]
```

### Правила тела

На каждом шаге всегда:

* `energy -= 1`
* `water -= 1`

Если `MOVE_FORWARD`:

* `energy -= 1`

Если вошёл в `ROUGH`:

* `energy -= 2`
* `water -= 1`

Если `energy < 15` или `water < 15`, и действие `MOVE_FORWARD`:

* ещё `energy -= 1`

Если `INTERACT` и перед агентом `FOOD`:

* `energy += 35`

Если `INTERACT` и перед агентом `WATER`:

* `water += 35`

После обновления:

* clamp в `[0,100]`
* если `energy <= 0` или `water <= 0`, агент умирает

### Столкновения

Если агент идёт в стену:

* позиция не меняется
* `collision=True`
* стоимость действия всё равно списывается

---

## 13.5. `RewardModel`

**Слой:** `env`
**Зависит от:** `RewardConfig`

**Метод:**

```python
compute(body: BodyState, info: StepInfo) -> float
```

### Формула

```python
dE = max(0, 70 - body.energy) / 70
dW = max(0, 70 - body.water) / 70

reward = -(0.5 * dE + 0.5 * dW)
reward -= 0.02 * (info.action_cost_energy + info.action_cost_water)
reward -= 0.2 if info.collision else 0.0
reward -= 5.0 if info.death_reason is not None else 0.0
```

Награда нужна для логов, baseline’ов и метрик. Основной policy loop может быть не-RL.

---

## 13.6. `HomeoGridEnv`

**Слой:** `env`
**Зависит от:** `WorldGenerator`, `ObservationEncoder`, `PhysiologyModel`, `RewardModel`

**Контракт:**

```python
reset(seed: int | None = None) -> tuple[Observation, dict]
step(action: ActionType) -> tuple[Observation, float, bool, bool, StepInfo]
```

**Правила:**

* совместим с Gymnasium;
* `terminated=True` только при смерти;
* `truncated=True` только при лимите шагов;
* hidden map не выдаётся агенту;
* debug-информация может выдаваться только логгеру/monitoring в debug-mode.

---

## 14. Подсистема агента

## 14.1. `BeliefMap`

**Слой:** `agent`
**Хранит:**

* `known_mask[11,11]`
* `tile_ids[11,11]`
* `last_seen_step[11,11]`
* `visit_count[11,11]`

**Методы:**

```python
reset() -> None
update(obs: Observation) -> None
get_known_resources(rtype: ResourceType, max_age: int) -> list[Vec2]
get_frontier_cells() -> list[Vec2]
is_walkable(pos: Vec2) -> bool
```

**Ответственность:**
Собрать внутреннюю карту текущего эпизода без доступа к hidden map.

---

## 14.2. `DriveModel`

**Слой:** `decision`
**Метод:**

```python
compute(body: BodyState) -> NeedState
```

**Логика:**

```python
energy_deficit = max(0, 70 - energy) / 70
water_deficit  = max(0, 70 - water) / 70

if max(energy_deficit, water_deficit) < 0.1:
    active_need = None
else:
    active_need = FOOD if energy_deficit > water_deficit else WATER

critical = (energy < 20) or (water < 20)
```

---

## 14.3. `BiomeInferer`

**Слой:** `decision`
**Поля:**

* `current_biome: BiomeId | None`

**Методы:**

```python
reset() -> None
infer(obs: Observation, belief_map: BeliefMap) -> BiomeId | None
```

**Правило:**
Если landmark виден — биом определяется сразу. Иначе использовать последний известный биом.

---

## 14.4. `WorkingBuffer`

Это инженерный аналог “рабочего поля”.

**Поля:**

* `need_state`
* `biome_id`
* `fast_proposal`
* `slow_proposal`
* `selected_proposal`
* `selected_action`

**Жизненный цикл:**

* reset в начале эпизода;
* обновляется на каждом шаге;
* сериализуется в телеметрию.

---

## 14.5. `FastMemory`

**Слой:** `memory`
**Роль:** память текущего эпизода.

### Хранимые данные

1. `ResourceTrace`

* `resource_type`
* `position`
* `step_seen`
* `last_confirmed_step`
* `valid`
* `confidence`

2. `SalientEvent[]`

### Методы

```python
reset() -> None
observe_resource(rtype: ResourceType, pos: Vec2, step_idx: int) -> None
invalidate_resource(rtype: ResourceType, pos: Vec2, step_idx: int) -> None
query(rtype: ResourceType, from_pose: Pose, step_idx: int) -> TargetProposal | None
write_event(event: SalientEvent) -> None
export_events() -> list[SalientEvent]
```

### Query scoring

```python
freshness = max(0.0, 1.0 - (step_idx - trace.last_confirmed_step) / fast_max_age)
distance = abs(from_pose.x - pos.x) + abs(from_pose.y - pos.y)
score = 0.7 * freshness + 0.3 * (1.0 / (1 + distance))
```

Возвращается лучшая точная цель.

### Инвалидация

Если ожидаемый ресурс отсутствует:

* trace помечается `valid=False`
* confidence обнуляется
* пишется `EXPECTATION_VIOLATED`

---

## 14.6. `SlowMemory`

**Слой:** `memory`
**Роль:** долговременная статистическая память по биомам.

### Представление

```python
heatmaps: np.ndarray  # shape=(4, 2, 11, 11), float32
```

оси:

* биом
* тип ресурса
* x
* y

### Методы

```python
query(biome_id: BiomeId, rtype: ResourceType, belief_map: BeliefMap) -> TargetProposal | None
update(samples: list[ReplaySample]) -> None
save(path: str) -> None
load(path: str) -> None
```

### Правила query

* взять heatmap нужного биома и ресурса;
* занулить известные стены;
* занулить клетки, уже подтверждённые как не содержащие этот ресурс в текущем эпизоде;
* выбрать `top_k`;
* вернуть `TargetProposal(source=SLOW, region_cells=[...])`.

### Правила update

Для каждого sample:

* добавить вес в клетку;
* разнести часть веса на соседей 3x3 ядром;
* после эпизода применить decay:

```python
heatmaps *= 0.995
```

Медленная память никогда не возвращает “точный факт”. Только регион поиска.

---

## 14.7. `EventDetector`

**Слой:** `decision`
**Метод:**

```python
detect(
    transition: Transition,
    prev_need: NeedState | None,
    next_need: NeedState | None,
    biome_id: BiomeId | None,
    belief_map: BeliefMap,
) -> list[SalientEvent]
```

### Обязательные события и веса

* `RESOURCE_OBSERVED` → `2.0`
* `RESOURCE_CONSUMED` → `2.0`
* `EXPECTATION_VIOLATED` → `1.5`
* `RESOURCE_RELOCATED` → `1.5`
* `COLLISION` → `0.5`
* `DEATH` → `3.0`
* `NEED_SWITCH` → `1.0`
* `BIOME_IDENTIFIED` → `1.0`

---

## 14.8. `ReplayManager`

**Слой:** `memory`
**Метод:**

```python
build_samples(events: list[SalientEvent]) -> list[ReplaySample]
```

**Правила:**

* брать только события с координатой;
* брать только `FOOD/WATER`;
* использовать `salience` как вес;
* вызываться только в конце эпизода.

---

## 14.9. `Arbiter`

**Слой:** `decision`
**Метод:**

```python
choose(
    need_state: NeedState,
    fast: TargetProposal | None,
    slow: TargetProposal | None,
    belief_map: BeliefMap,
) -> TargetProposal
```

### Жёсткое правило

1. если `active_need is None` → `EXPLORE`
2. если fast даёт валидную точную цель → `FAST`
3. иначе если slow уверена выше порога → `SLOW`
4. иначе → `EXPLORE`

---

## 14.10. `ExplorerPolicy`

**Слой:** `decision`
**Методы:**

```python
propose_global(belief_map: BeliefMap, pose: Pose) -> TargetProposal
propose_in_region(belief_map: BeliefMap, pose: Pose, region_cells: list[Vec2]) -> TargetProposal
```

**Логика:**

* глобальный режим берёт ближайший frontier;
* региональный — frontier внутри slow-region;
* при пустом регионе — fallback на глобальный explore.

---

## 14.11. `Planner`

**Слой:** `planning`
**Метод:**

```python
plan(belief_map: BeliefMap, pose: Pose, proposal: TargetProposal) -> Plan
```

**Правила:**

* алгоритм: A*
* стены непроходимы
* unknown клетки проходимы, но дороже
* rough клетки дороже
* если цель — ресурс, planner должен построить `stance_pose`, из которого ресурс будет перед агентом

---

## 14.12. `LowLevelController`

**Слой:** `planning`
**Метод:**

```python
next_action(pose: Pose, proposal: TargetProposal, plan: Plan) -> ActionType
```

**Правила:**

* если агент уже в `stance_pose` и смотрит на ресурс → `INTERACT`
* если не смотрит в нужную сторону → поворот
* иначе → `MOVE_FORWARD`
* если plan invalid → `WAIT`

---

## 14.13. `AgentCore`

**Слой:** `agent`
**Зависимости внедряются только через конструктор.**

```python
class AgentCore:
    def __init__(
        self,
        drive_model: DriveModel,
        belief_map: BeliefMap,
        biome_inferer: BiomeInferer,
        working_buffer: WorkingBuffer,
        fast_memory: FastMemory,
        slow_memory: SlowMemory,
        arbiter: Arbiter,
        explorer: ExplorerPolicy,
        planner: Planner,
        controller: LowLevelController,
        event_detector: EventDetector,
        replay_manager: ReplayManager,
        telemetry: TelemetryPublisher,
    ): ...
```

### Методы

```python
begin_episode(initial_obs: Observation) -> None
act(obs: Observation) -> ActionType
observe_transition(transition: Transition) -> None
end_episode(summary: EpisodeSummary) -> None
```

### Важное правило

`AgentCore` не создаёт зависимости сам внутри себя.

---

## 15. Оркестрация эксперимента

## 15.1. `SimulationControlPort`

Интерфейс управления ранном со стороны мониторинга.

```python
class SimulationControlPort(Protocol):
    def get_run_state(self) -> str: ...
    def pause(self) -> bool: ...
    def resume(self) -> bool: ...
    def reset_episode(self) -> bool: ...
    def save_snapshot(self) -> str | None: ...
    def toggle_debug(self, enabled: bool | None = None) -> bool: ...
```

---

## 15.2. `CommandBus`

Thread-safe очередь команд оператора.

**Команды:**

* `PAUSE`
* `RESUME`
* `RESET_EPISODE`
* `SAVE_SNAPSHOT`
* `TOGGLE_DEBUG`

Команды применяются только между шагами симуляции.

---

## 15.3. `ExperimentOrchestrator`

Главный управляющий объект ранна.

**Зависит от:**

* `HomeoGridEnv`
* `AgentCore`
* `MetricsCollector`
* `MonitoringFacade`
* `CommandBus`
* `ExperimentConfig`

**Методы:**

```python
run_train() -> None
run_eval() -> None
run_ablation(mode: str) -> None
run_single_episode(seed: int) -> EpisodeSummary
```

**Обязанности:**

* запуск train/eval/ablation;
* вызов цикла шагов;
* реакция на команды;
* сохранение артефактов;
* публикация episode start/end.

---

## 16. Подсистема метрик

## 16.1. `MetricsCollector`

**Слой:** `analytics`

### Хранит

* `total_reward`
* `survival_steps`
* `collision_count`
* `source_counts: {FAST,SLOW,EXPLORE}`
* `steps_to_first_food`
* `steps_to_first_water`
* `return_steps_to_seen_food`
* `return_steps_to_seen_water`
* `mean_energy_deficit`
* `mean_water_deficit`
* `need_switch_count`
* `stuck_windows`
* `relocation_recovery_steps`
* `action_history`
* `pose_history`

### Методы

```python
begin_episode(obs: Observation) -> None
on_step(transition: Transition, selected_source: TargetSource | None) -> None
end_episode(summary: EpisodeSummary) -> dict
```

---

## 16.2. `ReportWriter`

Пишет:

* `metrics.csv`
* `episode_summaries.jsonl`
* `ablation_results.csv`

---

## 17. Подсистема мониторинга

## 17.1. Задача мониторинга

Мониторинг должен позволить обычному оператору наблюдать тест онлайн, не читая raw-логи.

Оператор должен видеть:

* общее состояние эксперимента;
* текущее состояние тела;
* активную потребность;
* текущее поведение;
* источник решения;
* живую карту belief map;
* историю ключевых параметров;
* сводный 3D-индикатор;
* последние события и тревоги.

---

## 17.2. Режимы UI

### `Operator Mode`

Показывает только понятные человеку данные.

### `Debug Mode`

Показывает дополнительно:

* fast confidence
* slow confidence
* plan cost
* path length
* frontier count
* replay pending
* true-map overlay
* slow-memory heatmap overlay

Debug-mode включается только вручную и визуально маркируется как `DEBUG ONLY`.

---

## 17.3. DTO мониторинга

### Enum’ы

* `RunState = {IDLE, RUNNING, PAUSED, ENDED, ERROR}`
* `BehaviorMode = {SEEK_FOOD, SEEK_WATER, EXPLORE, INTERACT, WAIT}`
* `DecisionSource = {FAST, SLOW, EXPLORE, NONE}`
* `AlertLevel = {INFO, WARN, CRITICAL}`
* `StreamEventType = {FRAME, ALERT, SUMMARY, HEARTBEAT}`
* `OperatorCommandType = {PAUSE, RESUME, RESET_EPISODE, SAVE_SNAPSHOT, TOGGLE_DEBUG}`

### Основные DTO

* `BodyTelemetry`
* `NeedTelemetry`
* `MemoryTelemetry`
* `PlannerTelemetry`
* `WorldTelemetry`
* `BeliefMapView`
* `BlobVisualState`
* `StepSnapshot`
* `OperatorEvent`
* `EpisodeSummaryView`
* `OperatorCommand`
* `CommandResult`

### Обязательные поля `StepSnapshot`

* `ts_ms`
* `run_id`
* `episode_id`
* `run_state`
* `behavior_mode`
* `body`
* `need`
* `memory`
* `planner`
* `world`
* `belief_map`
* `blob`

---

## 17.4. Интерфейс телеметрии

```python
class TelemetryPublisher(Protocol):
    def publish_step(self, snapshot: StepSnapshot) -> None: ...
    def publish_event(self, event: OperatorEvent) -> None: ...
    def publish_episode_end(self, summary: EpisodeSummaryView) -> None: ...
```

Обязателен `NullTelemetryPublisher`, который ничего не делает.

---

## 17.5. `SnapshotBuilder`

Собирает `StepSnapshot` из состояния агента и метрик.

**Зависит от:**

* `BeliefMap`
* `WorkingBuffer`
* `FastMemory`
* `SlowMemory`
* `MetricsCollector`
* `RunStateStore`

**Derived-поля:**

* `uncertainty = 1 - max(fast_confidence, slow_confidence, 0.0)`
* `survival_ratio = step_idx / episode_limit`
* `dominance = abs(energy_deficit - water_deficit)`

---

## 17.6. `StatusTranslator`

Переводит машинное состояние в понятные подписи.

Примеры:

* `SEEK_FOOD` → `Ищет еду`
* `DecisionSource.FAST` → `Опора: быстрая память`
* `critical + water<15` → `Критически низкий запас воды`

---

## 17.7. `AlertEngine`

Генерирует операторские тревоги.

### Обязательные правила

* `LOW_ENERGY_WARN` если `energy < 25`
* `LOW_WATER_WARN` если `water < 25`
* `LOW_ENERGY_CRITICAL` если `energy < 15`
* `LOW_WATER_CRITICAL` если `water < 15`
* `NO_VALID_PLAN` если `plan_valid=False` более 5 шагов
* `STUCK_LOOP` если поза почти не меняется 12 шагов
* `REPEATED_COLLISIONS` если 3+ столкновения за 10 шагов
* `NO_PROGRESS_TO_TARGET` если цель есть, но дистанция не сокращается 8 шагов
* `MEMORY_CONFLICT` если fast и slow обе уверены, но тянут в разные стороны
* `STREAM_STALE` если UI не получает frame более 2 секунд

---

## 17.8. `FrameRingBuffer`

Thread-safe кольцевой буфер последних UI-фреймов.

```python
append(frame: StepSnapshot) -> None
latest() -> StepSnapshot | None
tail(n: int) -> list[StepSnapshot]
```

---

## 17.9. `SessionRecorder`

Пишет историю мониторинга в:

```text
artifacts/monitoring/{run_id}/{episode_id}.jsonl
```

Типы записей:

* `frame`
* `alert`
* `summary`

Никогда не должен блокировать симуляцию.

---

## 17.10. `StreamHub`

Раздаёт live-данные подписчикам.

### Правила

* транспорт: SSE;
* heartbeat каждые `sse_ping_sec`;
* новому клиенту сначала отправляется `latest snapshot`;
* очереди bounded;
* старые frame’ы можно дропать;
* alerts и summaries дропать нельзя.

---

## 17.11. `MonitoringFacade`

Главный фасад мониторинга.

**Обязанности:**

* принимать публикации из симуляции;
* обновлять буферы;
* вызывать AlertEngine;
* писать историю;
* пушить данные в StreamHub.

### Жёсткое правило

`publish_step()` должен быть non-blocking.

---

## 18. Web-интерфейс оператора

## 18.1. URL

* `/monitor` — live dashboard
* `/replay/{run_id}/{episode_id}` — replay
* `/api/monitor/bootstrap`
* `/api/monitor/stream`
* `/api/monitor/command`
* `/api/monitor/history/{run_id}/{episode_id}`

---

## 18.2. Макет страницы

### Верхняя лента состояния

Показывает:

* run state
* episode id
* step
* sim speed
* elapsed time
* connection state
* общий уровень тревоги

### KPI-карточки

Показывают:

* энергия
* вода
* активная потребность
* текущее поведение
* источник решения
* уверенность
* total reward / survival
* биом

### Live-карта

Показывает:

* belief map агента
* rough
* замеченные food/water
* позу
* цель
* path
* frontier cells

### Осциллограф

Графики за последние 120 секунд:

* `energy_deficit`
* `water_deficit`
* `uncertainty`
* `selected_confidence`

В debug-mode дополнительно:

* `plan_cost`
* `path_len`
* `collision_rate_window`
* `action_switch_rate_window`

ECharts подходит сюда, потому что умеет live-обновление dynamic data с анимированным diff-обновлением. ([Apache ECharts][4])

### 3D-индикатор `Homeostat Globe`

Показывает сводное состояние системы.

#### Формулы

```python
stress = (energy_deficit + water_deficit) / 2
uncertainty = 1 - max(fast_confidence, slow_confidence, 0.0)
instability = min(1.0, 0.5 * collision_rate_window + 0.5 * action_switch_rate_window)

scale_x = 1.0 + 0.45 * energy_deficit
scale_y = 1.0 + 0.45 * water_deficit
scale_z = 1.0 + 0.45 * uncertainty

pulse_hz = 0.3 + 1.7 * stress
noise_amp = 0.01 + 0.08 * instability
halo_level = 0.2 + 0.8 * (1.0 if critical else 0.0)
```

#### Семантика

* вытянут по X → дефицит энергии
* вытянут по Y → дефицит воды
* вытянут по Z → высокая неопределённость
* быстрый пульс → высокий стресс
* дрожание поверхности → нестабильность политики
* halo → уровень тревоги

#### Техническое правило

Three.js-анимация должна работать через `setAnimationLoop()` для лучшей совместимости. ([Three.js][5])

#### Fallback

Если WebGL недоступен:

* показывать 2D radial widget с теми же параметрами.

### Лента событий

Показывает последние:

* обнаружение ресурса
* потребление ресурса
* смену потребности
* переключение fast/slow
* потерю цели
* relocation
* repeated collisions
* death
* episode end

---

## 19. API мониторинга

## 19.1. `GET /api/monitor/bootstrap`

Возвращает:

```json
{
  "run_state": "running",
  "latest_frame": { "...": "..." },
  "recent_alerts": []
}
```

## 19.2. `GET /api/monitor/stream`

SSE stream.

События:

* `event: frame`
* `event: alert`
* `event: summary`
* `event: heartbeat`

## 19.3. `POST /api/monitor/command`

Принимает `OperatorCommand`.

Поддерживаемые команды:

* `pause`
* `resume`
* `reset_episode`
* `save_snapshot`
* `toggle_debug`

Возвращает:

```json
{
  "accepted": true,
  "run_state": "paused",
  "message": "Simulation paused"
}
```

## 19.4. `GET /api/monitor/history/{run_id}/{episode_id}`

Возвращает сохранённый JSONL или готовый replay payload.

---

## 20. Последовательность выполнения на каждом шаге

```text
1. env.reset() -> Observation
2. agent.begin_episode()

Цикл:
3. belief_map.update(obs)
4. need_state = drive_model.compute(obs.body)
5. biome_id = biome_inferer.infer(obs, belief_map)
6. fast = fast_memory.query(...)
7. slow = slow_memory.query(...)
8. selected = arbiter.choose(...)
9. explorer fallback if needed
10. plan = planner.plan(...)
11. action = controller.next_action(...)
12. env.step(action) -> next_obs, reward, terminated, truncated, info
13. transition = Transition(...)
14. events = event_detector.detect(...)
15. fast_memory.observe/invalidate/write_event(...)
16. metrics.on_step(...)
17. telemetry.publish_step(...)
18. telemetry.publish_event(...) for alerts/events
19. if episode end:
    19.1 replay_samples = replay_manager.build_samples(...)
    19.2 slow_memory.update(replay_samples)
    19.3 metrics.end_episode(...)
    19.4 telemetry.publish_episode_end(...)
```

---

## 21. Артефакты и форматы хранения

### 21.1. Медленная память

```text
artifacts/memory/slow_memory.npz
```

Поля:

* `heatmaps`
* `episode_count`
* `config_hash`

### 21.2. Метрики

```text
artifacts/reports/metrics.csv
artifacts/reports/ablation_results.csv
```

### 21.3. Логи эпизодов

```text
artifacts/logs/episode_summaries.jsonl
```

### 21.4. Мониторинг

```text
artifacts/monitoring/{run_id}/{episode_id}.jsonl
```

### 21.5. Скриншоты по команде оператора

```text
artifacts/snapshots/{run_id}/{episode_id}/{step_idx}.json
artifacts/snapshots/{run_id}/{episode_id}/{step_idx}.png  # опционально
```

---

## 22. Режимы эксперимента

## 22.1. `sanity`

* 10 эпизодов
* без relocation
* с мониторингом
* цель: проверить, что всё работает

## 22.2. `train`

* 200 эпизодов
* без relocation по умолчанию
* slow memory сохраняется

## 22.3. `eval_seen`

* 100 эпизодов
* seen biomes
* фиксированный набор seed’ов

## 22.4. `eval_relocation`

* 50 эпизодов
* relocation включён
* проверка fast-memory адаптации

## 22.5. `ablation`

Режимы:

* `full`
* `no_fast`
* `no_slow`
* `no_interoception`
* `no_rough_cost`
* `full_observation`

---

## 23. Правила абляций

### `no_fast`

* `FastMemory.query()` всегда `None`
* replay в slow можно оставить, чтобы проверить только online-роль fast

### `no_slow`

* `SlowMemory.query()` всегда `None`
* `SlowMemory.update()` отключён

### `no_interoception`

* `DriveModel` не видит `energy/water`
* активная цель фиксируется или выбирается тупо

### `no_rough_cost`

* rough не дороже обычных клеток

### `full_observation`

* belief map сразу знает всю карту

---

## 24. Метрики успеха

Система считается принятой как исследовательская платформа, если после train+eval видны следующие эффекты:

1. **Межэпизодический эффект slow-memory**
   `steps_to_first_needed_resource` в `full` лучше `no_slow` минимум на 20%.

2. **Внутриэпизодический эффект fast-memory**
   `return_steps_to_seen_resource` в `full` лучше `no_fast` минимум на 25%.

3. **Эффект интероцепции**
   survival в `full` лучше `no_interoception` минимум на 30%.

4. **Relocation robustness**
   в `eval_relocation` full-system должна инвалидировать старую цель быстрее baseline без fast-memory.

5. **Мониторинг**
   оператор должен в live-режиме видеть:

   * источник решения;
   * изменение потребности;
   * срабатывание тревоги;
   * перестройку цели после relocation.

---

## 25. Требования к производительности

### Core

* симуляция должна идти детерминированно при фиксированном seed;
* мониторинг не должен менять поведение агента;
* отключение браузера не должно ломать ран.

### Monitoring

* ingest кадров — на каждом шаге;
* UI update rate — 5 Гц;
* alerts — мгновенно;
* запись JSONL — асинхронная или buffered;
* при переполнении очереди можно терять только старые `frame`, но не `alert` и не `summary`.

---

## 26. Тесты

## 26.1. Unit

Обязательны тесты на:

* `WorldGenerator`
* `ObservationEncoder`
* `PhysiologyModel`
* `RewardModel`
* `BeliefMap`
* `DriveModel`
* `FastMemory`
* `SlowMemory`
* `EventDetector`
* `ReplayManager`
* `Arbiter`
* `Planner`
* `LowLevelController`
* `AlertEngine`
* `FrameRingBuffer`
* `SessionRecorder`
* `StatusTranslator`

## 26.2. Integration

Обязательны тесты на:

* один полный эпизод без падений;
* корректную смерть агента;
* корректное `INTERACT`;
* влияние slow-memory на ранний поиск;
* relocation + fast invalidation;
* live-stream `/api/monitor/stream`;
* bootstrap страницы;
* команды `pause/resume/reset_episode`;
* replay из JSONL.

## 26.3. Ablation regression

Обязательны автоматические регрессии:

* `full` vs `no_fast`
* `full` vs `no_slow`
* `full` vs `no_interoception`

---

## 27. Критерии приёмки

### Функциональные

* среда корректно работает;
* тело и ресурсы реально влияют на выбор;
* fast-memory используется внутри эпизода;
* slow-memory влияет между эпизодами;
* replay обучает slow-memory только в конце эпизода;
* мониторинг показывает live-состояние;
* replay воспроизводит завершённый эпизод.

### Архитектурные

* нет циклических импортов;
* нет чтения hidden map агентом;
* нет блокировки симуляции из-за UI;
* все зависимости внедряются через конструкторы;
* все конфиги вынесены в YAML.

### Операторские

* оператор по одному экрану понимает:

  * что делает агент;
  * почему делает;
  * насколько он стабилен;
  * есть ли проблема;
* критические тревоги появляются сразу;
* карта, графики и 3D-индикатор реально отражают состояние, а не “живут отдельно”.

---

## 28. Что команда должна сдать

1. Рабочий пакет `homeogrid`
2. YAML-конфиги
3. Полный набор тестов
4. CLI-запуск:

   * `python -m homeogrid.app.main run --config configs/full.yaml`
   * `python -m homeogrid.app.main ablate --config configs/ablation.yaml`
   * `python -m homeogrid.app.main replay --file artifacts/monitoring/...jsonl`
5. HTML-страницу `/monitor`
6. Replay-страницу
7. `slow_memory.npz`
8. `metrics.csv`
9. `ablation_results.csv`
10. README с инструкцией запуска

---

## 29. Самый важный смысл платформы

Эта система должна быть не просто “агентом в grid-world”, а **диагностической машиной для проверки идеи**:

* потребности задают направление;
* тело задаёт стоимость и допустимость;
* среда даёт последствия;
* быстрая память держит конкретику текущего эпизода;
* медленная память даёт priors между эпизодами;
* мониторинг делает весь процесс наблюдаемым для человека в реальном времени.

Именно в таком виде платформа уже годится для контролируемых экспериментов, абляций и последующего усложнения архитектуры.

[1]: https://gymnasium.farama.org/introduction/create_custom_env/ "https://gymnasium.farama.org/introduction/create_custom_env/"
[2]: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events "https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events"
[3]: https://fastapi.tiangolo.com/advanced/websockets/ "https://fastapi.tiangolo.com/advanced/websockets/"
[4]: https://echarts.apache.org/en/feature.html "https://echarts.apache.org/en/feature.html"
[5]: https://threejs.org/docs/pages/Renderer.html "https://threejs.org/docs/pages/Renderer.html"
