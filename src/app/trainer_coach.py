import time
import random
import sys
from pathlib import Path
from collections import deque
from typing import Optional, Dict, Any, List

# Ensure src/ is on python path
_SRC_DIR = str(Path(__file__).resolve().parents[1])
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from bodyPartAngle import BodyPartAngle


# ==============================================================================
# Dynamic Trainer Cue Banks - Distinct, Motivational, & Exercise-Specific
# ==============================================================================

COACH_PHRASES = {
    "squat": {
        "start": [
            "Alright, let's fire up those legs with squats! Feet shoulder-width, chest proud, let's work!",
            "Squats time! Drive through your heels and sit deep, make every rep count!",
            "Let's get this squat session rolling! Keep that core braced and eyes forward."
        ],
        "depth_warning": [
            "Sink a little deeper—aim for hips parallel to knees!",
            "Don't cut that rep short! Sit back into the chair, full range of motion!",
            "Drop a couple inches lower, let those quads and glutes do the work!",
            "Break parallel on this next one, stay in control!"
        ],
        "chest_warning": [
            "Chest up, eyes on the horizon! Don't let your torso tip forward.",
            "Keep that spine tall and proud—fight the forward lean!",
            "Proud chest! Keep your shoulders back and weight on your heels."
        ],
        "lockout_cue": [
            "Squeeze the glutes and stand tall at the top!",
            "Drive through those heels, power all the way up!",
            "Lock the hips out smoothly at the peak, beautiful!"
        ],
        "improved_form": [
            "Much better depth on that one, that's textbook!",
            "Great adjustment! Hold that standard on the next rep!",
            "Clean depth right there! Keep that exact tempo."
        ],
        "milestones": {
            1: ["First squat down! That's our baseline, let's build from here!", "One solid rep in the books!"],
            3: ["Three down! Rhythm is looking smooth, keep breathing!", "Nice work on three, settle into your groove!"],
            5: ["Five reps locked in! Legs are warming up, stay disciplined!", "Five strong squats! Keep pushing the floor away!"],
            8: ["Eight down! Halfway through the burn, don't let up!", "Eight clean reps, maintain that chest height!"],
            10: ["Double digits—ten strong squats! You've got momentum!", "Ten reps! Pure power in the legs, keep it going!"],
            15: ["Fifteen! Feel that quad burn, embrace it, finish strong!", "Fifteen down! Dig deep, drive through your heels!"],
            20: ["Twenty monster squats! Absolutely incredible work!", "Twenty reps! That is true championship endurance!"]
        }
    },
    "push-up": {
        "start": [
            "Push-ups on deck! Hands just outside shoulder-width, body in a tight plank line.",
            "Let's build that chest and arm strength! Lock your glutes and core, let's move!",
            "Set that solid plank. Push the ground away on every single rep!"
        ],
        "sagging_core": [
            "Squeeze your glutes and brace your abs—don't let those hips sag!",
            "Keep your body like a rigid steel bar! Pull your belly button in.",
            "Hips up slightly! Maintain a straight line from heels to shoulders."
        ],
        "depth_warning": [
            "Bring your chest closer to the deck—aim for ninety degrees at the elbows!",
            "A little lower! Don't short-change the bottom half of the push-up.",
            "Chest all the way down, then explode back up!",
            "Deep rep! Tap near the floor before pressing."
        ],
        "lockout_cue": [
            "Full lockout at the top—push the floor away from you!",
            "Extend those arms completely, separate your shoulder blades!",
            "Good solid lockout at the top, reset and breathe."
        ],
        "improved_form": [
            "Great core alignment! That looked rock solid.",
            "Much better depth on that push! Keep that standard.",
            "There's the lockout! That's a true power rep."
        ],
        "milestones": {
            1: ["First push-up locked! Good tempo, feel that chest engagement.", "One down, great setup!"],
            3: ["Three clean push-ups! Keep that spine rigid, smooth press.", "Three reps in, pacing is perfect."],
            5: ["Five reps in the bank! Upper body is firing, hold that form!", "Five strong push-ups! Keep that core tight."],
            8: ["Eight down! Don't let your elbows flare too wide, drive up!", "Eight reps! Pushing through with solid power!"],
            10: ["Ten push-ups! That is serious upper body endurance!", "Ten reps! You're dominating this set!"],
            15: ["Fifteen! Dig deep, breathe out on the press up!", "Fifteen reps! Mind over muscle, finish this strong!"],
            20: ["Twenty incredible push-ups! Phenomenal upper body strength!", "Twenty reps crushed! You are unstoppable!"]
        }
    },
    "sit-up": {
        "start": [
            "Core workout time! Plant your feet, engage those abs, curl up smoothly.",
            "Sit-ups ready! Focus on curling your spine, make the abdominals do the work.",
            "Let's strengthen that midsection! Controlled ascent, controlled descent."
        ],
        "neck_pull_warning": [
            "Relax your neck and jaw—pull with your abs, not your head!",
            "Don't yank on your neck! Keep your chin slightly lifted off your chest.",
            "Let the core do all the lifting, keep your neck neutral."
        ],
        "descent_warning": [
            "Control the descent! Don't just flop backward onto the mat.",
            "Slow and steady on the way down—that's where the strength is built!",
            "Resist gravity on the lowering phase, stay in control."
        ],
        "range_warning": [
            "Curl all the way up, bring your ribcage toward your knees!",
            "Full contraction at the top! Squeeze the abs hard."
        ],
        "improved_form": [
            "That's the control we want! Excellent abdominal engagement.",
            "Beautiful smooth curl, that was textbook!",
            "Much better tempo on the descent, great core control."
        ],
        "milestones": {
            1: ["First sit-up down! Smooth curl, love that control.", "One rep in! Core is activated."],
            3: ["Three reps down! Maintain that smooth breathing rhythm.", "Three clean curls, keep that tension on the abs."],
            5: ["Five sit-ups! Midsection is heating up, stay locked in!", "Five reps! Solid abdominal drive."],
            8: ["Eight down! Don't let momentum take over, stay strict!", "Eight reps! Working that core with authority."],
            10: ["Ten sit-ups! Double digits on core power, keep pushing!", "Ten reps! Halfway through a monster set!"],
            15: ["Fifteen! Feel that burn, push through to the end!", "Fifteen reps! Your core is made of steel!"],
            20: ["Twenty sit-ups crushed! Elite core endurance right there!", "Twenty reps! Absolutely phenomenal work!"]
        }
    },
    "pull-up": {
        "start": [
            "Pull-up session! Overhand grip, engage your lats, pull with authority.",
            "Hang with active shoulders. Drive your elbows down to lift your chest."
        ],
        "range_warning": [
            "Pull all the way until your chin clears the bar!",
            "Drive your elbows straight down into your back pockets!",
            "Full stretch at the bottom before initiating the next pull!"
        ],
        "improved_form": [
            "Clean pull to the bar, that was crisp!",
            "Strict form right there, great vertical pulling power."
        ],
        "milestones": {
            1: ["First strict pull-up nailed! Looking powerful.", "One rep down, great deadhang control."],
            3: ["Three strict pull-ups! Back muscles are firing hard.", "Three down! Great lat engagement."],
            5: ["Five pull-ups! That is serious upper body pulling power!", "Five strict reps! You're crushing the bar."],
            8: ["Eight pull-ups! Elite back strength, stay disciplined!", "Eight reps! Fight for every inch."],
            10: ["Ten pull-ups! Incredible pulling strength, absolute beast mode!", "Ten reps! Top-tier fitness!"]
        }
    },
    "walk": {
        "start": [
            "Walking cardio session initiated! Find an easy, natural stride rhythm.",
            "Keep your posture tall, shoulders relaxed, arms swinging naturally."
        ],
        "posture_warning": [
            "Check posture: roll your shoulders back and keep eyes on the horizon.",
            "Avoid looking down at your feet—lift your chin and open your chest."
        ],
        "stride_cue": [
            "Keep a steady, brisk, purposeful cadence!",
            "Roll smoothly from heel to toe with each step."
        ],
        "improved_form": [
            "Posture looks great, that's a smooth, confident stride.",
            "Great upright rhythm, keep this pace rolling."
        ],
        "milestones": {
            10: ["Ten strides down! Settle into this walking rhythm.", "Ten paces in, breathing steady."],
            30: ["Thirty strides! Great steady cardiovascular cadence.", "Thirty paces, feeling light and active."],
            50: ["Fifty strides! Looking strong, great sustained rhythm!", "Fifty paces! Halfway to a century, keep moving!"]
        }
    }
}


class TrainerCoach:
    """
    Intelligent Personal Trainer AI Coach.
    Features:
    - Contextual real-time form diagnostics for each exercise
    - Natural conversational variety (never repeats robotic identical lines)
    - Milestone celebrations and encouragement
    - Anti-spam throttling and memory of recent feedback
    """
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.last_exercise = None
        self.last_reps = 0
        self.last_status = True
        self.last_cue_time = 0.0
        self.start_time = time.time()
        
        # Debounce and anti-repetition memory
        self.cue_history: deque = deque(maxlen=6)
        self.announced_start = False
        self.celebrated_milestones = set()
        
        # Form history smoothing
        self.consecutive_bad_form = 0
        self.consecutive_good_form = 0
        self.had_form_issue = False

    def reset_for_exercise(self, exercise: str):
        if self.last_exercise != exercise:
            self.last_exercise = exercise
            self.last_reps = 0
            self.last_status = True
            self.last_cue_time = 0.0
            self.start_time = time.time()
            self.announced_start = False
            self.celebrated_milestones.clear()
            self.cue_history.clear()
            self.consecutive_bad_form = 0
            self.consecutive_good_form = 0
            self.had_form_issue = False

    def _choose_variant(self, phrases: List[str]) -> str:
        """Select a phrase variant that hasn't been used recently in this session."""
        available = [p for p in phrases if p not in self.cue_history]
        if not available:
            available = phrases
        chosen = random.choice(available)
        self.cue_history.append(chosen)
        return chosen

    def evaluate_form_and_get_cue(
        self,
        landmarks,
        exercise: str,
        current_reps: int,
        status: bool
    ) -> Optional[str]:
        """
        Analyzes the posture landmarks, rep progression, and state transitions
        to deliver lifelike, dynamic trainer speech cues.
        """
        self.reset_for_exercise(exercise)
        now = time.time()

        phrases_bank = COACH_PHRASES.get(exercise, COACH_PHRASES["squat"])

        # ----------------------------------------------------------------------
        # 1. Warm-up & Workout Launch Greeting
        # ----------------------------------------------------------------------
        if not self.announced_start:
            self.announced_start = True
            self.last_cue_time = now
            return self._choose_variant(phrases_bank["start"])

        # ----------------------------------------------------------------------
        # 2. Dynamic Rep Milestones (High priority, celebration)
        # ----------------------------------------------------------------------
        if current_reps > self.last_reps:
            self.last_reps = current_reps
            milestones = phrases_bank.get("milestones", {})
            if current_reps in milestones and current_reps not in self.celebrated_milestones:
                self.celebrated_milestones.add(current_reps)
                self.last_cue_time = now
                self.consecutive_bad_form = 0
                self.consecutive_good_form = 0
                return self._choose_variant(milestones[current_reps])

        # Respect cooldown between general form corrections (minimum 4.2 seconds)
        if (now - self.last_cue_time) < 4.2:
            return None

        # ----------------------------------------------------------------------
        # 3. Biomechanical Form Diagnostics (Exercise-Specific)
        # ----------------------------------------------------------------------
        if landmarks is None:
            return None

        try:
            bpa = BodyPartAngle(landmarks)
        except Exception:
            return None

        form_cue = None

        # --- SQUAT DIAGNOSTICS ---
        if exercise == "squat":
            try:
                left_k = bpa.angle_of_the_left_leg()
                right_k = bpa.angle_of_the_right_leg()
                avg_knee = (left_k + right_k) / 2.0
            except Exception:
                avg_knee = 180.0

            # Bottom of rep (depth check)
            if not status and 115 < avg_knee < 145:
                self.consecutive_bad_form += 1
                if self.consecutive_bad_form >= 2:
                    form_cue = self._choose_variant(phrases_bank["depth_warning"])
                    self.had_form_issue = True
            # Good bottom depth achieved
            elif not status and avg_knee <= 100:
                self.consecutive_good_form += 1
                if self.had_form_issue and self.consecutive_good_form >= 2:
                    form_cue = self._choose_variant(phrases_bank["improved_form"])
                    self.had_form_issue = False
                    self.consecutive_bad_form = 0
            # Standing tall at the top lockout
            elif status and avg_knee > 168 and (now - self.last_cue_time) > 7.0:
                if random.random() < 0.35:
                    form_cue = self._choose_variant(phrases_bank["lockout_cue"])

        # --- PUSH-UP DIAGNOSTICS ---
        elif exercise == "push-up":
            try:
                left_a = bpa.angle_of_the_left_arm()
                right_a = bpa.angle_of_the_right_arm()
                avg_arm = (left_a + right_a) / 2.0
            except Exception:
                avg_arm = 180.0

            try:
                core_angle = bpa.angle_of_the_abdomen()
            except Exception:
                core_angle = 180.0

            # Core sagging or piking
            if core_angle < 155:
                self.consecutive_bad_form += 1
                if self.consecutive_bad_form >= 2:
                    form_cue = self._choose_variant(phrases_bank["sagging_core"])
                    self.had_form_issue = True
            # Shallow depth at bottom
            elif not status and 115 < avg_arm < 140:
                self.consecutive_bad_form += 1
                if self.consecutive_bad_form >= 2:
                    form_cue = self._choose_variant(phrases_bank["depth_warning"])
                    self.had_form_issue = True
            # Full lockout at top
            elif status and avg_arm > 165 and self.had_form_issue:
                form_cue = self._choose_variant(phrases_bank["improved_form"])
                self.had_form_issue = False
                self.consecutive_bad_form = 0
            elif status and avg_arm > 168 and (now - self.last_cue_time) > 7.5:
                if random.random() < 0.3:
                    form_cue = self._choose_variant(phrases_bank["lockout_cue"])

        # --- SIT-UP DIAGNOSTICS ---
        elif exercise == "sit-up":
            try:
                core_angle = bpa.angle_of_the_abdomen()
            except Exception:
                core_angle = 180.0

            if status and core_angle > 115:
                # Descent phase
                if (now - self.last_cue_time) > 6.0 and random.random() < 0.4:
                    form_cue = self._choose_variant(phrases_bank["descent_warning"])
            elif not status and core_angle < 60:
                # Good crunch top
                if self.had_form_issue:
                    form_cue = self._choose_variant(phrases_bank["improved_form"])
                    self.had_form_issue = False

        # --- PULL-UP DIAGNOSTICS ---
        elif exercise == "pull-up":
            if not status and (now - self.last_cue_time) > 6.0:
                form_cue = self._choose_variant(phrases_bank["range_warning"])

        # --- WALK DIAGNOSTICS ---
        elif exercise == "walk":
            try:
                neck_angle = bpa.angle_of_the_neck()
            except Exception:
                neck_angle = 180.0

            if neck_angle < 165:
                form_cue = self._choose_variant(phrases_bank["posture_warning"])
            elif (now - self.last_cue_time) > 8.0:
                form_cue = self._choose_variant(phrases_bank["stride_cue"])

        if form_cue:
            self.last_cue_time = now
            return form_cue

        return None


# Global registry of coach instances per session id
_COACHES: Dict[str, TrainerCoach] = {}

def get_trainer_coach(session_id: str = "default") -> TrainerCoach:
    if session_id not in _COACHES:
        _COACHES[session_id] = TrainerCoach(session_id=session_id)
    return _COACHES[session_id]
