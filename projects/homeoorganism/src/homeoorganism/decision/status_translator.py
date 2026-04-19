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
            "LOW_ENERGY_WARN": "РќРёР·РєРёР№ Р·Р°РїР°СЃ СЌРЅРµСЂРіРёРё",
            "LOW_WATER_WARN": "РќРёР·РєРёР№ Р·Р°РїР°СЃ РІРѕРґС‹",
            "LOW_ENERGY_CRITICAL": "РљСЂРёС‚РёС‡РµСЃРєРё РЅРёР·РєРёР№ Р·Р°РїР°СЃ СЌРЅРµСЂРіРёРё",
            "LOW_WATER_CRITICAL": "РљСЂРёС‚РёС‡РµСЃРєРё РЅРёР·РєРёР№ Р·Р°РїР°СЃ РІРѕРґС‹",
            "NO_VALID_PLAN": "РџР»Р°РЅ РЅРµРґРѕСЃС‚СѓРїРµРЅ СЃР»РёС€РєРѕРј РґРѕР»РіРѕ",
            "STUCK_LOOP": "РђРіРµРЅС‚ Р·Р°С†РёРєР»РёР»СЃСЏ",
            "REPEATED_COLLISIONS": "РџРѕРІС‚РѕСЂСЏСЋС‰РёРµСЃСЏ СЃС‚РѕР»РєРЅРѕРІРµРЅРёСЏ",
            "NO_PROGRESS_TO_TARGET": "РќРµС‚ РїСЂРѕРіСЂРµСЃСЃР° Рє С†РµР»Рё",
            "MEMORY_CONFLICT": "РљРѕРЅС„Р»РёРєС‚ РјРµР¶РґСѓ fast Рё slow РїР°РјСЏС‚СЊСЋ",
        }
        return messages.get(code, code)

