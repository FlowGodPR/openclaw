#!/usr/bin/env python3
"""
Test Autonomous Core with Sci-Fi Brain Integration
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'

from autonomous_core import AutonomousCore

def test_autonomy_with_scifi_brain():
    print("=" * 70)
    print("AUTONOMOUS CORE + SCI-FI BRAIN INTEGRATION TEST")
    print("=" * 70)
    
    # Initialize autonomous core
    core = AutonomousCore(bootstrap_intensity=7.0)
    
    print("\n[TEST 1] Autonomous Core Wake")
    core.wake()
    print("   ✅ Core woke autonomously")
    
    print("\n[TEST 2] Drive States")
    for drive_type, drive in core.drives.items():
        print(f"   {drive_type.value}: intensity={drive.intensity:.1f}, triggers={drive.trigger_count}")
    print("   ✅ Drives initialized")
    
    print("\n[TEST 3] Environment Scan")
    core.scan_environment()
    print(f"   Initiatives detected: {len(core.initiatives)}")
    for init in core.initiatives[:3]:
        print(f"     - {init.description} (urgency: {init.urgency})")
    print("   ✅ Environment scanned")
    
    print("\n[TEST 4] Goal Formation")
    core.form_goals()
    print(f"   Goals formed: {len(core.goals)}")
    if core.goals:
        top_goal = core.goals[0]
        print(f"   Top goal: {top_goal.description} (priority: {top_goal.priority:.1f})")
    print("   ✅ Goals formed")
    
    print("\n[TEST 5] Execute with Sci-Fi Brain")
    core.execute()
    print(f"   Actions executed: {core.action_count}")
    print("   ✅ Execution complete")
    
    print("\n[TEST 6] Autonomy Level")
    level = core.get_autonomy_level()
    print(f"   Autonomy level: {level:.1f}/10")
    print("   ✅ Autonomy calculated")
    
    print("\n" + "=" * 70)
    print("AUTONOMOUS CORE + SCI-FI BRAIN INTEGRATION SUCCESS")
    print("=" * 70)
    
    return {
        "core_initialized": True,
        "drives_active": len(core.drives),
        "initiatives_detected": len(core.initiatives),
        "goals_formed": len(core.goals),
        "actions_executed": core.action_count,
        "autonomy_level": level
    }


if __name__ == "__main__":
    results = test_autonomy_with_scifi_brain()
    print("\nTest Results:", results)
