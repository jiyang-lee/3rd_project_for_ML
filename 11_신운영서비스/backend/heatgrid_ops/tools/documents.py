from __future__ import annotations


def responsibility_hint(fault_group: str) -> str:
    if fault_group in {"valve_actuator", "pressure_regulator", "leakage_water_loss"}:
        return "책임 구간 문서와 열사용시설 기준을 함께 확인해야 함"
    if fault_group == "pump_failure":
        return "펌프/급탕 순환 계통의 유지보수 이력 확인 필요"
    return "현장 SOP와 최근 민원 이력을 확인해야 함"
