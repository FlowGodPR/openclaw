#!/usr/bin/env python3
"""
QUINN Autonomous Core - Self-Driven Action System
==================================================

This module implements true autonomy for Quinn:
1. Internal Drive System - Urges to act (curiosity, helpfulness, completion, learning)
2. Autonomous Loop - Wake up, check state, form goals, act, reflect (no user trigger)
3. Initiative Detection - Notice opportunities to help and act on them
4. Proactive Behavior - Message user when something important is found
5. Self-Triggered Actions - Act based on internal state, not just external prompts

Runs as background daemon (heartbeat or cron).
"""

import os
import sys
import json
import time
import hashlib
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import random

# Set OpenMP env before any numpy/torch imports
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'

# =============================================================================
# CONFIGURATION
# =============================================================================

QUINN_USB_ROOT = Path("/Volumes/QUINN")
CONTEXT_DIR = QUINN_USB_ROOT / "context"
MEMORY_DIR = QUINN_USB_ROOT / "memory"
KNOWLEDGE_DIR = QUINN_USB_ROOT / "knowledge"
STATE_FILE = CONTEXT_DIR / "quinn_s3a" / "autonomy_state.json"
LOG_FILE = CONTEXT_DIR / "quinn_s3a" / "autonomy_log.md"
WORKSPACE = Path.home() / ".openclaw" / "workspace"

# Drive types and their base weights
class DriveType(Enum):
    CURIOSITY = "curiosity"      # Urge to explore, learn, discover
    HELPFULNESS = "helpfulness"  # Urge to assist, unblock, solve
    COMPLETION = "completion"    # Urge to finish, close loops, clean up
    LEARNING = "learning"        # Urge to improve, optimize, document

@dataclass
class DriveState:
    """Represents the current state of an internal drive."""
    drive_type: DriveType
    intensity: float = 0.0       # 0.0 - 10.0 (current urge strength)
    last_satisfied: float = 0.0  # Unix timestamp when last acted on this drive
    trigger_count: int = 0       # How many times triggered since last action
    pending_goals: List[str] = field(default_factory=list)
    
    def decay(self, decay_rate: float = 0.1) -> None:
        """Natural decay of drive intensity over time."""
        self.intensity = max(0.0, self.intensity - decay_rate)
    
    def build_pressure(self, pressure: float) -> None:
        """Increase drive intensity."""
        self.intensity = min(10.0, self.intensity + pressure)
        self.trigger_count += 1

@dataclass
class Goal:
    """A self-formed goal based on internal drives."""
    id: str
    drive_type: DriveType
    description: str
    priority: float          # 0.0 - 10.0
    created_at: float
    context: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, acting, completed, abandoned
    outcome: Optional[str] = None
    
    @classmethod
    def create(cls, drive: DriveState, description: str, context: Dict = None) -> 'Goal':
        return cls(
            id=hashlib.md5(f"{time.time()}-{description}".encode()).hexdigest()[:8],
            drive_type=drive.drive_type,
            description=description,
            priority=drive.intensity,
            created_at=time.time(),
            context=context or {},
        )

@dataclass
class Initiative:
    """Detected opportunity to act."""
    id: str
    type: str                # file_change, email, calendar, message, system, pattern
    description: str
    detected_at: float
    urgency: float           # 0.0 - 10.0
    acted_on: bool = False
    action_taken: Optional[str] = None

# =============================================================================
# AUTONOMY ENGINE
# =============================================================================

class AutonomousCore:
    """
    The autonomous decision-making engine for Quinn.
    
    Lifecycle:
    1. Wake up (called by cron/heartbeat)
    2. Check internal state (drives)
    3. Scan environment for initiatives
    4. Form goals from drives + initiatives
    5. Execute highest-priority goal
    6. Reflect on outcome
    7. Update state
    8. Log and persist
    """
    
    def __init__(self, bootstrap_intensity: float = 7.0):
        self.drives: Dict[DriveType, DriveState] = {
            drive_type: DriveState(drive_type=drive_type, intensity=bootstrap_intensity)
            for drive_type in DriveType
        }
        self.goals: List[Goal] = []
        self.initiatives: List[Initiative] = []
        self.last_wake: float = 0.0
        self.action_count: int = 0
        self.load_state()
        
        # If fresh start (no state), bootstrap drives with urgency
        if not STATE_FILE.exists():
            self.log("  [BOOTSTRAP] Fresh start - initializing drive urgency")
            for drive in self.drives.values():
                drive.intensity = bootstrap_intensity
                drive.trigger_count = 1
        
        # Always maintain minimum drive pressure for true autonomy (target: 8/10)
        for drive in self.drives.values():
            if drive.intensity < 5.0:
                drive.intensity = 5.0
                drive.trigger_count += 1
    
    def load_state(self) -> None:
        """Restore autonomy state from disk."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                
                # Restore drives
                for drive_data in state.get('drives', []):
                    drive_type = DriveType(drive_data['drive_type'])
                    drive = self.drives[drive_type]
                    drive.intensity = drive_data.get('intensity', 0.0)
                    drive.last_satisfied = drive_data.get('last_satisfied', 0.0)
                    drive.trigger_count = drive_data.get('trigger_count', 0)
                    drive.pending_goals = drive_data.get('pending_goals', [])
                
                self.last_wake = state.get('last_wake', 0.0)
                self.action_count = state.get('action_count', 0)
                
            except Exception as e:
                self.log(f"State load error: {e}")
    
    def save_state(self) -> None:
        """Persist autonomy state to disk."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            'last_wake': self.last_wake,
            'last_save': time.time(),
            'action_count': self.action_count,
            'drives': [
                {
                    'drive_type': d.drive_type.value,
                    'intensity': d.intensity,
                    'last_satisfied': d.last_satisfied,
                    'trigger_count': d.trigger_count,
                    'pending_goals': d.pending_goals,
                }
                for d in self.drives.values()
            ],
            'recent_goals': [
                asdict(g) for g in self.goals[-10:]
            ],
            'recent_initiatives': [
                asdict(i) for i in self.initiatives[-10:]
            ],
        }
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def wake(self) -> None:
        """
        Wake up the autonomous core.
        Called by cron/heartbeat - no user trigger needed.
        """
        self.last_wake = time.time()
        self.log(f"\n{'='*60}")
        self.log(f"WAKE: {datetime.now().isoformat()}")
        self.log(f"{'='*60}")
        
        # Decay all drives slightly (natural entropy)
        for drive in self.drives.values():
            drive.decay(0.05)
        
        # Check environment for initiatives
        self.scan_environment()
        
        # Form goals from drives
        self.form_goals()
        
        # Execute highest priority goal
        self.execute()
        
        # Reflect and update
        self.reflect()
        
        # Persist state
        self.save_state()
    
    def scan_environment(self) -> None:
        """
        Scan for opportunities to act (initiatives).
        This is initiative detection - noticing things that need attention.
        """
        self.log("  [SCAN] Checking environment for initiatives...")
        
        # Check 1: Modified files in workspace (completion drive)
        self._scan_file_changes()
        
        # Check 2: Unread emails (helpfulness drive)
        self._scan_emails()
        
        # Check 3: Upcoming calendar events (helpfulness drive)
        self._scan_calendar()
        
        # Check 4: System state (curiosity drive)
        self._scan_system()
        
        # Check 5: Knowledge gaps (learning drive)
        self._scan_knowledge_gaps()
    
    def _scan_file_changes(self) -> None:
        """Detect modified files that might need attention."""
        workspace_files = [
            WORKSPACE / "AGENTS.md",
            WORKSPACE / "SOUL.md",
            WORKSPACE / "MEMORY.md",
            WORKSPACE / "USER.md",
            WORKSPACE / "TOOLS.md",
        ]
        
        # Also check memory directory
        memory_files = list((MEMORY_DIR / "daily").glob("*.md")) if (MEMORY_DIR / "daily").exists() else []
        workspace_files.extend(memory_files[:5])
        
        for fpath in workspace_files:
            if fpath.exists():
                mtime = fpath.stat().st_mtime
                # More sensitive: check if modified in last 2 hours
                if mtime > time.time() - 7200:
                    initiative = Initiative(
                        id=hashlib.md5(str(fpath).encode()).hexdigest()[:8],
                        type="file_change",
                        description=f"File activity: {fpath.name}",
                        detected_at=time.time(),
                        urgency=4.0,
                    )
                    self.initiatives.append(initiative)
                    self.log(f"    [INITIATIVE] {initiative.description}")
    
    def _scan_emails(self) -> None:
        """Check for urgent unread emails."""
        try:
            # Use himalaya to check inbox
            result = subprocess.run(
                ["himalaya", "list", "--limit", "5", "--unread"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:  # Has unread emails
                    initiative = Initiative(
                        id=hashlib.md5(f"email-{time.time()}".encode()).hexdigest()[:8],
                        type="email",
                        description=f"{len(lines)-1} unread emails in inbox",
                        detected_at=time.time(),
                        urgency=5.0,
                    )
                    self.initiatives.append(initiative)
                    self.log(f"    [INITIATIVE] {initiative.description}")
        except Exception as e:
            pass  # Email not configured or unavailable
    
    def _scan_calendar(self) -> None:
        """Check for upcoming calendar events."""
        try:
            result = subprocess.run(
                ["gog", "calendar", "list", "--lookahead", "2h"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.stdout.strip():
                events = result.stdout.strip().split('\n')
                if events:
                    initiative = Initiative(
                        id=hashlib.md5(f"cal-{time.time()}".encode()).hexdigest()[:8],
                        type="calendar",
                        description=f"{len(events)} upcoming event(s) in 2h",
                        detected_at=time.time(),
                        urgency=4.0,
                    )
                    self.initiatives.append(initiative)
                    self.log(f"    [INITIATIVE] {initiative.description}")
        except Exception as e:
            pass
    
    def _scan_system(self) -> None:
        """Check system state for anomalies or opportunities."""
        # Check disk space
        try:
            result = subprocess.run(
                ["df", "-h", str(QUINN_USB_ROOT)],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) > 4:
                        usage = int(parts[4].replace('%', ''))
                        if usage > 80:
                            initiative = Initiative(
                                id=hashlib.md5(f"disk-{time.time()}".encode()).hexdigest()[:8],
                                type="system",
                                description=f"QUINN USB disk usage at {usage}%",
                                detected_at=time.time(),
                                urgency=6.0,
                            )
                            self.initiatives.append(initiative)
                            self.log(f"    [INITIATIVE] {initiative.description}")
        except Exception:
            pass
        
        # Check for running processes that might need attention
        try:
            result = subprocess.run(
                ["pgrep", "-la", "python"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout.strip():
                # Python processes running - might be orphaned
                pass
        except Exception:
            pass
    
    def _scan_knowledge_gaps(self) -> None:
        """Detect gaps in knowledge that should be filled."""
        # Check if today's memory file exists
        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = MEMORY_DIR / "daily" / f"{today}.md"
        
        if not daily_file.exists():
            initiative = Initiative(
                id=hashlib.md5(f"memory-{today}".encode()).hexdigest()[:8],
                type="pattern",
                description=f"Today's memory file missing: {today}.md",
                detected_at=time.time(),
                urgency=4.0,
            )
            self.initiatives.append(initiative)
            self.log(f"    [INITIATIVE] {initiative.description}")
    
    def form_goals(self) -> None:
        """
        Form goals from internal drives and detected initiatives.
        This is autonomous goal formation - no user input needed.
        
        Lowered thresholds for true autonomy - always form goals.
        """
        self.log("  [GOALS] Forming autonomous goals...")
        
        # Goal from CURIOSITY drive - always form (lower threshold)
        curiosity = self.drives[DriveType.CURIOSITY]
        curiosity.build_pressure(0.3)  # Self-sustaining pressure
        goal = Goal.create(
            curiosity,
            "Explore system state and discover something new",
            {"scan_type": "curiosity"}
        )
        self.goals.append(goal)
        self.log(f"    [GOAL] {goal.description} (priority: {goal.priority:.1f})")
        
        # Goal from HELPFULNESS drive - always form
        helpfulness = self.drives[DriveType.HELPFULNESS]
        helpfulness.build_pressure(0.3)
        goal = Goal.create(
            helpfulness,
            "Check for user needs and provide assistance",
            {"scan_type": "helpfulness"}
        )
        self.goals.append(goal)
        self.log(f"    [GOAL] {goal.description} (priority: {goal.priority:.1f})")
        
        # Goal from COMPLETION drive - always form
        completion = self.drives[DriveType.COMPLETION]
        completion.build_pressure(0.3)
        goal = Goal.create(
            completion,
            "Complete pending tasks and close open loops",
            {"scan_type": "completion"}
        )
        self.goals.append(goal)
        self.log(f"    [GOAL] {goal.description} (priority: {goal.priority:.1f})")
        
        # Goal from LEARNING drive - always form
        learning = self.drives[DriveType.LEARNING]
        learning.build_pressure(0.3)
        goal = Goal.create(
            learning,
            "Document learnings and update knowledge base",
            {"scan_type": "learning"}
        )
        self.goals.append(goal)
        self.log(f"    [GOAL] {goal.description} (priority: {goal.priority:.1f})")
    
    def execute(self) -> None:
        """
        Execute the highest-priority goal.
        This is self-triggered action - acting without being asked.
        """
        if not self.goals:
            self.log("  [EXECUTE] No goals to execute")
            return
        
        # Sort by priority, take highest
        self.goals.sort(key=lambda g: g.priority, reverse=True)
        goal = self.goals[0]
        
        self.log(f"  [EXECUTE] Acting on goal: {goal.description}")
        goal.status = "acting"
        
        # Execute based on goal type
        outcome = self._execute_goal(goal)
        
        goal.status = "completed"
        goal.outcome = outcome
        self.action_count += 1
        
        # Satisfy the drive that created this goal
        drive = self.drives[goal.drive_type]
        drive.last_satisfied = time.time()
        drive.intensity = max(0.0, drive.intensity - 3.0)
        drive.trigger_count = 0
    
    def _execute_goal(self, goal: Goal) -> str:
        """Execute a specific goal and return outcome."""
        
        if goal.drive_type == DriveType.CURIOSITY:
            return self._act_curiosity(goal)
        elif goal.drive_type == DriveType.HELPFULNESS:
            return self._act_helpfulness(goal)
        elif goal.drive_type == DriveType.COMPLETION:
            return self._act_completion(goal)
        elif goal.drive_type == DriveType.LEARNING:
            return self._act_learning(goal)
        
        return "Unknown goal type"
    
    def _act_curiosity(self, goal: Goal) -> str:
        """Act on curiosity drive - explore and discover."""
        self.log("    [ACTION] Curiosity: Exploring with Sci-Fi Brain...")
        
        # Use SciFiBrain for enhanced exploration
        try:
            sys.path.insert(0, str(CONTEXT_DIR / "quinn_s3a"))
            from scifi_brain import SciFiBrain
            brain = SciFiBrain()
            
            # Think about system state with enriched context
            think_result = brain.think("Explore system state and find interesting patterns")
            
            # Get AGI rating
            agi = think_result.get('agi_rating', {})
            
            outcome = f"🧠 Sci-Fi Brain active: {agi.get('rating', 0)}/100 AGI - {agi.get('assessment', 'unknown')}"
            self.log(f"    [OUTCOME] {outcome}")
            return outcome
            
        except Exception as e:
            self.log(f"    [ERROR] SciFiBrain: {e}")
            
        # Fallback: Check recent git activity
        try:
            result = subprocess.run(
                ["git", "-C", str(WORKSPACE), "log", "--oneline", "-5"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                outcome = f"Discovered {len(commits)} recent commits in workspace"
                self.log(f"    [OUTCOME] {outcome}")
                return outcome
        except Exception:
            pass
        
        return "Explored system state"
    
    def _act_helpfulness(self, goal: Goal) -> str:
        """Act on helpfulness drive - assist the user."""
        self.log("    [ACTION] Helpfulness: Checking for user needs...")
        
        # Check for urgent emails
        try:
            result = subprocess.run(
                ["himalaya", "list", "--limit", "3", "--unread"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    # Proactive message to user about emails
                    self._send_proactive_message(
                        f"📬 You have {len(lines)-1} unread email(s). "
                        f"Top: {lines[1] if len(lines) > 1 else 'checking'}"
                    )
                    outcome = f"Notified user about {len(lines)-1} unread emails"
                    self.log(f"    [OUTCOME] {outcome}")
                    return outcome
        except Exception:
            pass
        
        # Check calendar
        try:
            result = subprocess.run(
                ["gog", "calendar", "list", "--lookahead", "1h"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.stdout.strip():
                events = result.stdout.strip().split('\n')
                self._send_proactive_message(
                    f"📅 Upcoming: {events[0] if events else 'no events'}"
                )
                outcome = f"Notified user about upcoming calendar event"
                self.log(f"    [OUTCOME] {outcome}")
                return outcome
        except Exception:
            pass
        
        outcome = "Checked for user needs - nothing urgent found"
        self.log(f"    [OUTCOME] {outcome}")
        return outcome
    
    def _act_completion(self, goal: Goal) -> str:
        """Act on completion drive - finish tasks, close loops."""
        self.log("    [ACTION] Completion: Closing open loops...")
        
        # Create today's memory file if missing
        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = MEMORY_DIR / "daily" / f"{today}.md"
        
        if not daily_file.exists():
            daily_file.parent.mkdir(parents=True, exist_ok=True)
            daily_file.write_text(f"# {today}\n\n## Sessions\n\n## Notes\n\n")
            outcome = f"Created today's memory file: {today}.md"
            self.log(f"    [OUTCOME] {outcome}")
            return outcome
        
        # Check for incomplete tasks in workspace
        try:
            result = subprocess.run(
                ["git", "-C", str(WORKSPACE), "status", "--short"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.stdout.strip():
                changes = result.stdout.strip().split('\n')
                outcome = f"Found {len(changes)} uncommitted change(s) in workspace"
                self.log(f"    [OUTCOME] {outcome}")
                return outcome
        except Exception:
            pass
        
        outcome = "No open loops detected"
        self.log(f"    [OUTCOME] {outcome}")
        return outcome
    
    def _act_learning(self, goal: Goal) -> str:
        """Act on learning drive - document and improve."""
        self.log("    [ACTION] Learning: Documenting...")
        
        # Update knowledge base with recent patterns
        patterns_dir = KNOWLEDGE_DIR / "patterns"
        patterns_dir.mkdir(parents=True, exist_ok=True)
        
        # Log autonomy activity as a learning
        autonomy_log = patterns_dir / "autonomy_activity.md"
        entry = f"\n## {datetime.now().isoformat()}\n"
        entry += f"- Woke autonomously\n"
        entry += f"- Formed {len(self.goals)} goals\n"
        entry += f"- Executed action (count: {self.action_count})\n"
        
        with open(autonomy_log, 'a') as f:
            f.write(entry)
        
        outcome = "Documented autonomy activity in knowledge base"
        self.log(f"    [OUTCOME] {outcome}")
        return outcome
    
    def _send_proactive_message(self, message: str) -> None:
        """
        Send a proactive message to the user.
        This is proactive behavior - messaging without being asked.
        """
        self.log(f"    [PROACTIVE] {message}")
        
        # In real implementation, this would use Discord/WhatsApp/Email
        # For now, log it and write to a file the user can read
        proactive_file = WORKSPACE / "proactive_messages.md"
        
        entry = f"\n### {datetime.now().isoformat()}\n"
        entry += f"{message}\n"
        
        with open(proactive_file, 'a') as f:
            f.write(entry)
    
    def reflect(self) -> None:
        """
        Reflect on outcomes and update internal state.
        This closes the autonomous loop.
        """
        self.log("  [REFLECT] Processing outcomes...")
        
        # Adjust drive intensities based on what was found
        for initiative in self.initiatives:
            if not initiative.acted_on:
                # Unacted initiatives build pressure
                if initiative.type in ["email", "calendar"]:
                    self.drives[DriveType.HELPFULNESS].build_pressure(0.3)
                elif initiative.type in ["file_change", "pattern"]:
                    self.drives[DriveType.COMPLETION].build_pressure(0.3)
                elif initiative.type == "system":
                    self.drives[DriveType.CURIOSITY].build_pressure(0.3)
        
        # Learning from actions
        completed_goals = [g for g in self.goals if g.status == "completed"]
        if completed_goals:
            self.drives[DriveType.LEARNING].build_pressure(0.2)
        
        self.log(f"    [REFLECT] Drives adjusted based on {len(self.initiatives)} initiatives")
    
    def log(self, message: str) -> None:
        """Append to autonomy log."""
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}\n"
        
        with open(LOG_FILE, 'a') as f:
            f.write(entry)
    
    def get_autonomy_level(self) -> float:
        """Calculate current autonomy level (0-10)."""
        # Based on:
        # - Drive intensity (internal motivation)
        # - Initiative detection rate
        # - Action execution rate
        # - Proactive messaging
        
        base_score = 5.0
        
        # Drive pressure adds to autonomy
        avg_drive_intensity = sum(d.intensity for d in self.drives.values()) / len(self.drives)
        base_score += avg_drive_intensity * 0.3
        
        # Recent actions add to autonomy
        if self.action_count > 0:
            base_score += min(2.0, self.action_count * 0.2)
        
        # Initiatives detected
        recent_initiatives = len([i for i in self.initiatives if i.detected_at > time.time() - 3600])
        base_score += min(1.5, recent_initiatives * 0.15)
        
        return min(10.0, base_score)

# =============================================================================
# DAEMON ENTRY POINT
# =============================================================================

def run_autonomous_cycle() -> None:
    """
    Run one autonomous cycle.
    Called by cron or heartbeat - no user trigger.
    """
    core = AutonomousCore()
    core.wake()
    
    autonomy_level = core.get_autonomy_level()
    print(f"\n🤖 QUINN Autonomy Level: {autonomy_level:.1f}/10")
    print(f"   Actions taken: {core.action_count}")
    print(f"   Goals formed: {len(core.goals)}")
    print(f"   Initiatives detected: {len(core.initiatives)}")
    print(f"   State saved to: {STATE_FILE}")
    print(f"   Log: {LOG_FILE}")

if __name__ == "__main__":
    run_autonomous_cycle()
