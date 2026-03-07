"""
Dataset preparation for work pattern analysis
Based on real-world productivity and typing behavior research
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import os

class WorkPatternDataGenerator:
    """
    Generate realistic work pattern dataset based on research:
    - Typing speed: 40-90 WPM average (200-450 keystrokes/min)
    - Optimal work session: 45-90 minutes
    - Fatigue patterns from human factors research
    """
    
    def __init__(self, n_samples=10000):
        self.n_samples = n_samples
        np.random.seed(42)
        
    def generate_healthy_pattern(self, n):
        """Generate healthy work patterns"""
        data = []
        for _ in range(n):
            typing_speed = np.random.normal(300, 50)  # 300 keys/min average
            idle_time = np.random.uniform(2, 8)  # Regular breaks
            work_duration = np.random.uniform(20, 60)  # Moderate sessions
            keystroke_variance = np.random.uniform(15, 30)  # Consistent rhythm
            error_rate = np.random.uniform(0.01, 0.03)  # Low errors
            mouse_activity = np.random.uniform(20, 40)  # clicks per minute
            session_intensity = typing_speed / 500  # Normalized intensity
            
            data.append([
                typing_speed, idle_time, work_duration, keystroke_variance,
                error_rate, mouse_activity, session_intensity, 0  # Label: Healthy
            ])
        return data
    
    def generate_focused_pattern(self, n):
        """Generate focused/productive patterns"""
        data = []
        for _ in range(n):
            typing_speed = np.random.normal(350, 40)  # Higher speed
            idle_time = np.random.uniform(1, 4)  # Minimal breaks
            work_duration = np.random.uniform(45, 90)  # Longer sessions
            keystroke_variance = np.random.uniform(10, 20)  # Very consistent
            error_rate = np.random.uniform(0.01, 0.025)  # Low errors
            mouse_activity = np.random.uniform(15, 30)  # Less switching
            session_intensity = typing_speed / 500
            
            data.append([
                typing_speed, idle_time, work_duration, keystroke_variance,
                error_rate, mouse_activity, session_intensity, 1  # Label: Focused
            ])
        return data
    
    def generate_break_soon_pattern(self, n):
        """Generate patterns indicating need for break soon"""
        data = []
        for _ in range(n):
            typing_speed = np.random.normal(280, 60)  # Declining speed
            idle_time = np.random.uniform(0.5, 2)  # Very few breaks
            work_duration = np.random.uniform(90, 120)  # Extended sessions
            keystroke_variance = np.random.uniform(25, 40)  # Inconsistent
            error_rate = np.random.uniform(0.03, 0.05)  # Rising errors
            mouse_activity = np.random.uniform(25, 45)  # More switching
            session_intensity = typing_speed / 500
            
            data.append([
                typing_speed, idle_time, work_duration, keystroke_variance,
                error_rate, mouse_activity, session_intensity, 2  # Label: Break Soon
            ])
        return data
    
    def generate_fatigue_pattern(self, n):
        """Generate fatigue/overwork patterns"""
        data = []
        for _ in range(n):
            typing_speed = np.random.normal(220, 70)  # Significantly slower
            idle_time = np.random.uniform(0, 1)  # No breaks
            work_duration = np.random.uniform(120, 180)  # Very long sessions
            keystroke_variance = np.random.uniform(35, 60)  # Highly erratic
            error_rate = np.random.uniform(0.05, 0.10)  # High error rate
            mouse_activity = np.random.uniform(40, 60)  # Distracted
            session_intensity = typing_speed / 500
            
            data.append([
                typing_speed, idle_time, work_duration, keystroke_variance,
                error_rate, mouse_activity, session_intensity, 3  # Label: Fatigue
            ])
        return data
    
    def generate_dataset(self):
        """Generate complete dataset with all patterns"""
        print("Generating work pattern dataset...")
        
        # Distribution: 30% healthy, 25% focused, 25% break soon, 20% fatigue
        n_healthy = int(self.n_samples * 0.30)
        n_focused = int(self.n_samples * 0.25)
        n_break = int(self.n_samples * 0.25)
        n_fatigue = self.n_samples - n_healthy - n_focused - n_break
        
        print(f"  Healthy patterns: {n_healthy}")
        print(f"  Focused patterns: {n_focused}")
        print(f"  Break soon patterns: {n_break}")
        print(f"  Fatigue patterns: {n_fatigue}")
        
        all_data = []
        all_data.extend(self.generate_healthy_pattern(n_healthy))
        all_data.extend(self.generate_focused_pattern(n_focused))
        all_data.extend(self.generate_break_soon_pattern(n_break))
        all_data.extend(self.generate_fatigue_pattern(n_fatigue))
        
        # Create DataFrame
        columns = [
            'typing_speed', 'idle_time', 'work_duration', 'keystroke_variance',
            'error_rate', 'mouse_activity', 'session_intensity', 'fatigue_level'
        ]
        
        df = pd.DataFrame(all_data, columns=columns)
        
        # Shuffle
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        # Add time-series sequences (last 5 measurements)
        df['prev_typing_speed_1'] = df['typing_speed'].shift(1).fillna(df['typing_speed'].mean())
        df['prev_typing_speed_2'] = df['typing_speed'].shift(2).fillna(df['typing_speed'].mean())
        df['prev_work_duration_1'] = df['work_duration'].shift(1).fillna(df['work_duration'].mean())
        df['prev_idle_time_1'] = df['idle_time'].shift(1).fillna(df['idle_time'].mean())
        
        return df
    
    def save_dataset(self, output_dir='data'):
        """Generate and save train/test datasets"""
        os.makedirs(output_dir, exist_ok=True)
        
        df = self.generate_dataset()
        
        # Split into train/test
        train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['fatigue_level'])
        
        train_path = os.path.join(output_dir, 'train_data.csv')
        test_path = os.path.join(output_dir, 'test_data.csv')
        
        train_df.to_csv(train_path, index=False)
        test_df.to_csv(test_path, index=False)
        
        print(f"\n✓ Dataset saved:")
        print(f"  Training: {train_path} ({len(train_df)} samples)")
        print(f"  Testing: {test_path} ({len(test_df)} samples)")
        
        # Print label distribution
        print(f"\nLabel distribution (training set):")
        print(train_df['fatigue_level'].value_counts().sort_index())
        print("\nLabels: 0=Healthy, 1=Focused, 2=Break Soon, 3=Fatigue")
        
        return train_df, test_df

def main():
    generator = WorkPatternDataGenerator(n_samples=10000)
    generator.save_dataset()

if __name__ == "__main__":
    main()



