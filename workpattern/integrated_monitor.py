"""
Integrated Work Pattern System
Combines adaptive monitoring + API server with real-time updates
"""
import time
import threading
from datetime import datetime, timedelta
from collections import deque
from pynput import keyboard, mouse
import statistics
import sys
import os
import json
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Add parent directory for module_bridge
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
try:
    from module_bridge import push_event as _push_event
except ImportError:
    def _push_event(*a, **k): pass

class IntegratedMonitor:
    def __init__(self):
        # User profile
        self.profile_file = "user_profile.json"
        self.user_profile = self.load_or_create_profile()
        
        # Calibration
        self.calibration_mode = not self.user_profile.get('calibrated', False)
        self.calibration_data = []
        self.calibration_samples_needed = 10
        
        # Metrics tracking
        self.keystrokes = deque(maxlen=300)
        self.mouse_clicks = deque(maxlen=300)
        self.errors = deque(maxlen=100)
        self.session_start = datetime.now()
        self.last_activity = datetime.now()
        
        # Real-time data for API
        self.current_metrics = {}
        self.current_analysis = {}
        self.analysis_history = []
        
        # Counters
        self.total_keystrokes = 0
        self.total_mouse_clicks = 0
        self.backspace_count = 0
        
        # Settings
        self.analysis_interval = 1800  # Analyze every 30 minutes
        self.last_popup = datetime.now() - timedelta(seconds=1810)  # Allow first popup after 30 min
        
        # Baseline
        self.baseline_typing_speed = self.user_profile.get('avg_typing_speed', 250)
        self.baseline_error_rate = self.user_profile.get('avg_error_rate', 0.03)
        
        self.running = False
        self.monitor_thread = None
        self.keyboard_listener = None
        self.mouse_listener = None
        print(self.get_startup_banner())
    
    def load_or_create_profile(self):
        if os.path.exists(self.profile_file):
            try:
                with open(self.profile_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'user_name': 'User',
            'calibrated': False,
            'avg_typing_speed': 250,
            'avg_error_rate': 0.03,
            'sessions_tracked': 0,
            'created_at': datetime.now().isoformat()
        }
    
    def save_profile(self):
        with open(self.profile_file, 'w') as f:
            json.dump(self.user_profile, f, indent=2)
    
    def get_startup_banner(self):
        banner = "\n" + "="*70 + "\n"
        banner += "🚀 INTEGRATED WORK PATTERN SYSTEM\n"
        banner += "="*70 + "\n"
        
        if self.calibration_mode:
            banner += "\n🔧 CALIBRATION MODE\n"
            banner += "📊 Learning YOUR typing patterns (5 minutes)...\n"
        else:
            banner += f"\n✅ PERSONALIZED MODE - User: {self.user_profile['user_name']}\n"
            banner += f"⚡ Baseline Typing: {self.baseline_typing_speed:.0f} keys/min\n"
        
        banner += "\n✓ Wellness tips every 30 minutes\n"
        banner += "✓ API server integration\n"
        banner += "✓ Monitoring ALL applications\n"
        banner += "✓ Monitoring ALL applications\n"
        banner += "="*70 + "\n"
        return banner
    
    def on_key_press(self, key):
        try:
            now = datetime.now()
            self.keystrokes.append(now.timestamp())
            self.total_keystrokes += 1
            self.last_activity = now
            
            if key == keyboard.Key.backspace:
                self.backspace_count += 1
                self.errors.append(now.timestamp())
        except:
            pass
    
    def on_mouse_click(self, x, y, button, pressed):
        if pressed:
            now = datetime.now()
            self.mouse_clicks.append(now.timestamp())
            self.total_mouse_clicks += 1
            self.last_activity = now
    
    def calculate_metrics(self):
        now = datetime.now().timestamp()
        
        recent_keys = [ts for ts in self.keystrokes if now - ts <= 60]
        typing_speed = len(recent_keys)
        
        idle_time = (datetime.now() - self.last_activity).total_seconds() / 60.0
        work_duration = (datetime.now() - self.session_start).total_seconds() / 60.0
        
        if len(recent_keys) > 5:
            intervals = [recent_keys[i+1] - recent_keys[i] for i in range(len(recent_keys)-1)]
            keystroke_variance = statistics.stdev(intervals) * 1000 if intervals else 20.0
        else:
            keystroke_variance = 20.0
        
        recent_errors = [ts for ts in self.errors if now - ts <= 120]
        recent_total = [ts for ts in self.keystrokes if now - ts <= 120]
        error_rate = len(recent_errors) / len(recent_total) if len(recent_total) > 10 else 0.02
        
        recent_clicks = [ts for ts in self.mouse_clicks if now - ts <= 60]
        mouse_activity = len(recent_clicks)
        
        return {
            'typing_speed': float(typing_speed),
            'idle_time': float(min(idle_time, 60.0)),
            'work_duration': float(work_duration),
            'keystroke_variance': float(min(keystroke_variance, 100.0)),
            'error_rate': float(min(error_rate, 1.0)),
            'mouse_activity': float(mouse_activity),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_time_based_tip(self, work_duration):
        """Get wellness tip based on work duration"""
        tips = {
            15: "💡 Tip: Every 20 minutes, look at something 20 feet away for 20 seconds (20-20-20 rule)",
            30: "💧 Tip: Stay hydrated! Take a sip of water",
            45: "🧘 Tip: Time for a 5-minute stretch break",
            60: "🚶 Tip: You've been working for 1 hour - take a short walk",
            90: "☕ Tip: 90 minutes completed - consider a coffee/tea break",
            120: "⚠️ Tip: 2 hours of work - take a 15-minute break to recharge"
        }
        
        # Find the closest tip
        for duration, tip in sorted(tips.items()):
            if work_duration <= duration + 5:
                return tip
        return "💪 Tip: Great focus! Remember to take regular breaks"
    
    def analyze_personalized(self, metrics):
        speed_ratio = metrics['typing_speed'] / self.baseline_typing_speed if self.baseline_typing_speed > 0 else 1.0
        error_increase = (metrics['error_rate'] - self.baseline_error_rate) / self.baseline_error_rate if self.baseline_error_rate > 0 else 0
        
        score = 0
        indicators = []
        
        if speed_ratio < 0.7:
            score += 30
            indicators.append(f"Typing {(1-speed_ratio)*100:.0f}% slower than baseline")
        elif speed_ratio < 0.85:
            score += 15
            indicators.append("Typing slower than usual")
        
        if error_increase > 1.0:
            score += 30
            indicators.append(f"Error rate {(error_increase+1)*100:.0f}% above baseline")
        elif error_increase > 0.5:
            score += 15
            indicators.append("More errors than usual")
        
        if metrics['work_duration'] > 120:
            score += 20
            indicators.append(f"Extended session: {metrics['work_duration']:.0f}m")
        elif metrics['work_duration'] > 90:
            score += 10
        
        if metrics['mouse_activity'] > 50:
            score += 10
            indicators.append("High mouse activity")
        
        if metrics['idle_time'] < 1 and metrics['work_duration'] > 45:
            score += 10
            indicators.append("No breaks detected")
        
        # Get time-based tip
        wellness_tip = self.get_time_based_tip(metrics['work_duration'])
        
        if score >= 75:
            fatigue_level = "Fatigue"
            status_emoji = "🚨"
            recommendations = [
                "STOP - Take 15 minute break NOW",
                "Your patterns show critical fatigue",
                wellness_tip
            ]
        elif score >= 50:
            fatigue_level = "Break Soon"
            status_emoji = "⚠️"
            recommendations = [
                "Take a break within 5 minutes",
                "Your performance is declining",
                wellness_tip
            ]
        elif score >= 25:
            fatigue_level = "Focused"
            status_emoji = "🎯"
            recommendations = [
                "Good work pace",
                wellness_tip
            ]
        else:
            fatigue_level = "Healthy"
            status_emoji = "✅"
            recommendations = [
                "Optimal work pattern",
                wellness_tip
            ]
        
        return {
            'fatigue_level': fatigue_level,
            'fatigue_score': min(score, 100),
            'confidence': 0.85,
            'risk_indicators': indicators,
            'recommendations': recommendations,
            'break_needed': score >= 50,
            'predicted_class': min(int(score / 25), 3),
            'status_emoji': status_emoji,
            'baseline_typing': self.baseline_typing_speed,
            'timestamp': datetime.now().isoformat()
        }
    
    def calibrate(self, metrics):
        if metrics['typing_speed'] >= 30:
            self.calibration_data.append(metrics)
            samples = len(self.calibration_data)
            print(f"\n[CALIBRATION] Sample {samples}/{self.calibration_samples_needed}")
            print(f"  → Typing: {metrics['typing_speed']:.0f} keys/min, Errors: {metrics['error_rate']*100:.1f}%")
            
            if samples >= self.calibration_samples_needed:
                self.finalize_calibration()
    
    def finalize_calibration(self):
        speeds = [d['typing_speed'] for d in self.calibration_data]
        errors = [d['error_rate'] for d in self.calibration_data]
        
        self.baseline_typing_speed = statistics.mean(speeds)
        self.baseline_error_rate = statistics.mean(errors)
        
        self.user_profile.update({
            'calibrated': True,
            'avg_typing_speed': self.baseline_typing_speed,
            'avg_error_rate': self.baseline_error_rate,
            'calibrated_at': datetime.now().isoformat()
        })
        self.save_profile()
        self.calibration_mode = False
        
        print("\n" + "="*70)
        print("✅ CALIBRATION COMPLETE!")
        print(f"📊 Baseline: {self.baseline_typing_speed:.0f} keys/min, {self.baseline_error_rate*100:.1f}% errors")
        print("="*70 + "\n")
    
    def show_wellness_popup(self, analysis, metrics):
        """Show wellness tip popup with health advice"""
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            
            work_time = int(metrics['work_duration'])
            
            # Get wellness tip
            health_tip = self.get_time_based_tip(metrics['work_duration'])
            
            # Create title with status
            title = f"{analysis['status_emoji']} {analysis['fatigue_level']} - {work_time} min"
            
            # Create message with health tip prominently
            message = f"Score: {analysis['fatigue_score']:.0f}% | Typing: {metrics['typing_speed']:.0f} keys/min\n"
            message += f"\n{health_tip}"
            
            # Add break warning if needed
            if analysis['break_needed']:
                message += "\n⚠️ Take a break soon!"
            
            toaster.show_toast(
                title,
                message,
                duration=10,
                threaded=True
            )
        except Exception as e:
            print(f"Popup error: {e}")
    
    def monitor_loop(self):
        """Main monitoring loop - runs every 30 minutes"""
        while self.running:
            try:
                time.sleep(self.analysis_interval)
                
                metrics = self.calculate_metrics()
                
                if metrics['typing_speed'] < 5 and metrics['mouse_activity'] < 3:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 💤 Low activity")
                    continue
                
                # Calibration
                if self.calibration_mode:
                    self.calibrate(metrics)
                    continue
                
                # Personalized analysis
                analysis = self.analyze_personalized(metrics)
                
                # Store for API access
                self.current_metrics = metrics
                self.current_analysis = analysis
                self.analysis_history.append(analysis)

                # Push events to orchestrator → avatar
                if analysis.get('break_needed'):
                    _push_event("HIGH_FATIGUE", "workpattern", {
                        "fatigue_score": analysis['fatigue_score'],
                        "work_duration": round(metrics['work_duration']),
                    })
                elif metrics['work_duration'] > 90:
                    _push_event("LONG_SESSION", "workpattern", {
                        "work_duration": round(metrics['work_duration']),
                    })
                
                # Show wellness popup (only if 30 minutes passed since last popup)
                time_since_popup = (datetime.now() - self.last_popup).total_seconds()
                if time_since_popup >= 1800:  # Only popup every 30 minutes
                    self.show_wellness_popup(analysis, metrics)
                    self.last_popup = datetime.now()
                
                # Print real-time update
                self.print_realtime_update(metrics, analysis)
                
            except Exception as e:
                print(f"Monitor loop error: {e}")
            
            time.sleep(5)
    
    def print_realtime_update(self, metrics, analysis):
        """Print real-time update to console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = analysis['status_emoji']
        
        print(f"\n[{timestamp}] {emoji} {analysis['fatigue_level']} | Score: {analysis['fatigue_score']:.0f}%")
        print(f"  → Typing: {metrics['typing_speed']:.0f} keys/min "
              f"(baseline: {self.baseline_typing_speed:.0f}) | "
              f"Mouse: {metrics['mouse_activity']:.0f} clicks/min")
        print(f"  → Work: {metrics['work_duration']:.0f}m | "
              f"Errors: {metrics['error_rate']*100:.1f}%")
        
        if analysis['risk_indicators']:
            for indicator in analysis['risk_indicators'][:2]:
                print(f"  ⚠ {indicator}")
        
        # Always show wellness tip
        if analysis['recommendations']:
            print(f"  {analysis['recommendations'][-1]}")
    
    def get_current_status(self):
        """Get current status for API"""
        return {
            'metrics': self.current_metrics,
            'analysis': self.current_analysis,
            'session_info': {
                'session_duration': (datetime.now() - self.session_start).total_seconds() / 60.0,
                'total_keystrokes': self.total_keystrokes,
                'total_mouse_clicks': self.total_mouse_clicks,
                'calibrated': not self.calibration_mode,
                'baseline_typing': self.baseline_typing_speed
            }
        }
    
    def start(self):
        """Start monitoring"""
        self.start_background()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitor...")
            self.stop_background()
            
            # Simple exit message
            duration = (datetime.now() - self.session_start).total_seconds() / 60.0
            print(f"\n✓ Session: {duration:.1f} minutes")
            print(f"✓ Keystrokes: {self.total_keystrokes:,}")
            self.save_profile()
            print("✓ Saved\n")

    def start_background(self):
        """Start monitoring without blocking the caller."""
        if self.running:
            return

        self.running = True

        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.keyboard_listener.start()

        self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
        self.mouse_listener.start()

        print("\n✅ Monitor started! Tracking your typing...\n")

    def stop_background(self):
        """Stop background monitoring helpers if they are running."""
        self.running = False
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None

# Global monitor instance
monitor_instance = None

def get_monitor():
    global monitor_instance
    if monitor_instance is None:
        monitor_instance = IntegratedMonitor()
    return monitor_instance

if __name__ == "__main__":
    monitor = get_monitor()
    monitor.start()
