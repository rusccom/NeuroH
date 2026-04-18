"""Translate machine state into operator-facing labels."""

from homeoorganism.domain.enums import ActionType, ResourceType, TargetSource
from homeoorganism.monitoring.domain.enums import BehaviorMode, DecisionSource


class StatusTranslator:
    def behavior_mode(self, active_need, action: ActionType | None) -> BehaviorMode:
        if action == ActionType.INTERACT:
            return BehaviorMode.INTERACT
        if action == ActionType.WAIT:
            return BehaviorMode.WAIT
        if active_need == ResourceType.FOOD:
            return BehaviorMode.SEEK_FOOD
        if active_need == ResourceType.WATER:
            return BehaviorMode.SEEK_WATER
        return BehaviorMode.EXPLORE

    def decision_source(self, source: TargetSource | None) -> DecisionSource:
        if source is None:
            return DecisionSource.NONE
        if source == TargetSource.FAST:
            return DecisionSource.FAST
        if source == TargetSource.SLOW:
            return DecisionSource.SLOW
        return DecisionSource.EXPLORE

    def alert_message(self, code: str) -> str:
        messages = {
            "LOW_ENERGY_WARN": "Низкий запас энергии",
            "LOW_WATER_WARN": "Низкий запас воды",
            "LOW_ENERGY_CRITICAL": "Критически низкий запас энергии",
            "LOW_WATER_CRITICAL": "Критически низкий запас воды",
            "NO_VALID_PLAN": "План недоступен слишком долго",
            "STUCK_LOOP": "Агент зациклился",
            "REPEATED_COLLISIONS": "Повторяющиеся столкновения",
            "NO_PROGRESS_TO_TARGET": "Нет прогресса к цели",
            "MEMORY_CONFLICT": "Конфликт между fast и slow памятью",
        }
        return messages.get(code, code)
