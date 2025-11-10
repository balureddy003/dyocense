"""
Achievements Tracking Service

Provides achievement unlock detection, progress tracking, and XP calculation.
Business-agnostic design - works for any SMB by tracking generic metrics.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel


class Achievement(BaseModel):
    """Achievement definition"""
    id: str
    title: str
    description: str
    icon: str
    category: str  # 'goals', 'streaks', 'tasks', 'health', 'special'
    tier: str  # 'bronze', 'silver', 'gold', 'platinum'
    unlocked: bool = False
    unlocked_date: Optional[str] = None
    progress: int = 0
    target: int = 0
    reward: str = ""


class AchievementProgress(BaseModel):
    """Current progress towards achievements"""
    total_goals_completed: int = 0
    total_tasks_completed: int = 0
    current_streak_days: int = 0
    max_health_score: int = 0
    active_goals_count: int = 0
    weekend_task_days: int = 0
    connected_data_sources: int = 0
    referrals: int = 0
    shares: int = 0


class AchievementsService:
    """Service for tracking and unlocking achievements"""
    
    def __init__(self):
        # Storage: tenant_id -> Achievement progress
        self.progress_data: Dict[str, AchievementProgress] = {}
        
        # Storage: tenant_id -> list of unlocked achievement IDs
        self.unlocked_achievements: Dict[str, List[str]] = {}
        
        # Achievement definitions (business-agnostic)
        self.achievement_definitions = self._define_achievements()
    
    def _define_achievements(self) -> List[Achievement]:
        """Define all available achievements (generic for any business)"""
        return [
            # Goals Achievements
            Achievement(
                id='first_goal',
                title='First Steps',
                description='Set your first business goal',
                icon='🎯',
                category='goals',
                tier='bronze',
                target=1,
                reward='+10 XP'
            ),
            Achievement(
                id='goal_achiever',
                title='Goal Achiever',
                description='Complete 5 business goals',
                icon='🏆',
                category='goals',
                tier='silver',
                target=5,
                reward='+25 XP'
            ),
            Achievement(
                id='goal_master',
                title='Goal Master',
                description='Complete 20 business goals',
                icon='👑',
                category='goals',
                tier='gold',
                target=20,
                reward='+100 XP'
            ),
            Achievement(
                id='ambitious',
                title='Ambitious Leader',
                description='Set 10 goals simultaneously',
                icon='🚀',
                category='goals',
                tier='platinum',
                target=10,
                reward='+250 XP'
            ),
            
            # Streak Achievements
            Achievement(
                id='week_streak',
                title='Consistency Starter',
                description='Maintain a 1-week streak',
                icon='🔥',
                category='streaks',
                tier='bronze',
                target=7,
                reward='+10 XP'
            ),
            Achievement(
                id='month_streak',
                title='Monthly Warrior',
                description='Maintain a 4-week streak',
                icon='💪',
                category='streaks',
                tier='silver',
                target=28,
                reward='+50 XP'
            ),
            Achievement(
                id='quarter_streak',
                title='Unstoppable',
                description='Maintain a 12-week streak',
                icon='⚡',
                category='streaks',
                tier='gold',
                target=84,
                reward='+150 XP'
            ),
            Achievement(
                id='year_streak',
                title='Legendary',
                description='Maintain a 52-week streak',
                icon='🌟',
                category='streaks',
                tier='platinum',
                target=365,
                reward='+500 XP'
            ),
            
            # Task Achievements
            Achievement(
                id='task_starter',
                title='Task Starter',
                description='Complete your first task',
                icon='✅',
                category='tasks',
                tier='bronze',
                target=1,
                reward='+5 XP'
            ),
            Achievement(
                id='productive_week',
                title='Productive Week',
                description='Complete 25 tasks in a week',
                icon='📈',
                category='tasks',
                tier='silver',
                target=25,
                reward='+30 XP'
            ),
            Achievement(
                id='task_master',
                title='Task Master',
                description='Complete 100 total tasks',
                icon='💎',
                category='tasks',
                tier='gold',
                target=100,
                reward='+100 XP'
            ),
            Achievement(
                id='weekend_warrior',
                title='Weekend Warrior',
                description='Complete tasks on 10 weekends',
                icon='🏃',
                category='tasks',
                tier='silver',
                target=10,
                reward='+40 XP'
            ),
            
            # Health Score Achievements
            Achievement(
                id='health_50',
                title='Getting Fit',
                description='Reach health score of 50',
                icon='💚',
                category='health',
                tier='bronze',
                target=50,
                reward='+15 XP'
            ),
            Achievement(
                id='health_75',
                title='Strong Business',
                description='Reach health score of 75',
                icon='💙',
                category='health',
                tier='silver',
                target=75,
                reward='+40 XP'
            ),
            Achievement(
                id='health_90',
                title='Thriving Business',
                description='Reach health score of 90',
                icon='💜',
                category='health',
                tier='gold',
                target=90,
                reward='+120 XP'
            ),
            Achievement(
                id='perfect_health',
                title='Peak Performance',
                description='Reach health score of 100',
                icon='🏅',
                category='health',
                tier='platinum',
                target=100,
                reward='+300 XP'
            ),
            
            # Special Achievements
            Achievement(
                id='early_adopter',
                title='Early Adopter',
                description='Join in the first month',
                icon='🎁',
                category='special',
                tier='gold',
                target=1,
                reward='+50 XP'
            ),
            Achievement(
                id='referral_pro',
                title='Referral Pro',
                description='Refer 5 businesses',
                icon='🤝',
                category='special',
                tier='silver',
                target=5,
                reward='+75 XP'
            ),
            Achievement(
                id='data_connected',
                title='Data Connected',
                description='Connect 3 data sources',
                icon='🔗',
                category='special',
                tier='silver',
                target=3,
                reward='+30 XP'
            ),
            Achievement(
                id='social_star',
                title='Social Star',
                description='Share 10 achievements',
                icon='⭐',
                category='special',
                tier='bronze',
                target=10,
                reward='+25 XP'
            ),
        ]
    
    def get_achievements(self, tenant_id: str) -> List[Achievement]:
        """Get all achievements with progress for tenant"""
        progress = self.progress_data.get(tenant_id, AchievementProgress())
        unlocked = self.unlocked_achievements.get(tenant_id, [])
        
        achievements = []
        for definition in self.achievement_definitions:
            achievement = definition.model_copy()
            achievement.unlocked = definition.id in unlocked
            
            # Calculate progress based on category
            if definition.category == 'goals':
                if definition.id == 'first_goal':
                    achievement.progress = min(progress.total_goals_completed, 1)
                elif definition.id == 'goal_achiever':
                    achievement.progress = progress.total_goals_completed
                elif definition.id == 'goal_master':
                    achievement.progress = progress.total_goals_completed
                elif definition.id == 'ambitious':
                    achievement.progress = progress.active_goals_count
            
            elif definition.category == 'streaks':
                achievement.progress = progress.current_streak_days
            
            elif definition.category == 'tasks':
                if definition.id == 'task_starter':
                    achievement.progress = min(progress.total_tasks_completed, 1)
                elif definition.id == 'task_master':
                    achievement.progress = progress.total_tasks_completed
                elif definition.id == 'weekend_warrior':
                    achievement.progress = progress.weekend_task_days
                # productive_week requires special weekly tracking (not implemented yet)
            
            elif definition.category == 'health':
                achievement.progress = progress.max_health_score
            
            elif definition.category == 'special':
                if definition.id == 'data_connected':
                    achievement.progress = progress.connected_data_sources
                elif definition.id == 'referral_pro':
                    achievement.progress = progress.referrals
                elif definition.id == 'social_star':
                    achievement.progress = progress.shares
                elif definition.id == 'early_adopter':
                    achievement.progress = 1  # Auto-unlock for early users
            
            # Add unlock date if unlocked
            if achievement.unlocked:
                achievement.unlocked_date = datetime.now().isoformat()
            
            achievements.append(achievement)
        
        return achievements
    
    def update_progress(
        self,
        tenant_id: str,
        goals_completed: Optional[int] = None,
        tasks_completed: Optional[int] = None,
        streak_days: Optional[int] = None,
        health_score: Optional[int] = None,
        active_goals: Optional[int] = None,
        weekend_tasks: Optional[int] = None,
        data_sources: Optional[int] = None,
        referrals: Optional[int] = None,
        shares: Optional[int] = None,
    ) -> List[Achievement]:
        """
        Update progress and check for new unlocks.
        Returns newly unlocked achievements.
        """
        if tenant_id not in self.progress_data:
            self.progress_data[tenant_id] = AchievementProgress()
        
        progress = self.progress_data[tenant_id]
        
        # Update provided metrics
        if goals_completed is not None:
            progress.total_goals_completed = goals_completed
        if tasks_completed is not None:
            progress.total_tasks_completed = tasks_completed
        if streak_days is not None:
            progress.current_streak_days = streak_days
        if health_score is not None:
            progress.max_health_score = max(progress.max_health_score, health_score)
        if active_goals is not None:
            progress.active_goals_count = active_goals
        if weekend_tasks is not None:
            progress.weekend_task_days = weekend_tasks
        if data_sources is not None:
            progress.connected_data_sources = data_sources
        if referrals is not None:
            progress.referrals = referrals
        if shares is not None:
            progress.shares = shares
        
        # Check for new unlocks
        newly_unlocked = self._check_unlocks(tenant_id, progress)
        
        return newly_unlocked
    
    def _check_unlocks(self, tenant_id: str, progress: AchievementProgress) -> List[Achievement]:
        """Check for achievement unlocks based on current progress"""
        if tenant_id not in self.unlocked_achievements:
            self.unlocked_achievements[tenant_id] = []
        
        unlocked = self.unlocked_achievements[tenant_id]
        newly_unlocked = []
        
        for achievement in self.achievement_definitions:
            # Skip already unlocked
            if achievement.id in unlocked:
                continue
            
            # Check if criteria met
            should_unlock = False
            
            if achievement.category == 'goals':
                if achievement.id == 'first_goal' and progress.total_goals_completed >= 1:
                    should_unlock = True
                elif achievement.id == 'goal_achiever' and progress.total_goals_completed >= 5:
                    should_unlock = True
                elif achievement.id == 'goal_master' and progress.total_goals_completed >= 20:
                    should_unlock = True
                elif achievement.id == 'ambitious' and progress.active_goals_count >= 10:
                    should_unlock = True
            
            elif achievement.category == 'streaks':
                if achievement.id == 'week_streak' and progress.current_streak_days >= 7:
                    should_unlock = True
                elif achievement.id == 'month_streak' and progress.current_streak_days >= 28:
                    should_unlock = True
                elif achievement.id == 'quarter_streak' and progress.current_streak_days >= 84:
                    should_unlock = True
                elif achievement.id == 'year_streak' and progress.current_streak_days >= 365:
                    should_unlock = True
            
            elif achievement.category == 'tasks':
                if achievement.id == 'task_starter' and progress.total_tasks_completed >= 1:
                    should_unlock = True
                elif achievement.id == 'task_master' and progress.total_tasks_completed >= 100:
                    should_unlock = True
                elif achievement.id == 'weekend_warrior' and progress.weekend_task_days >= 10:
                    should_unlock = True
            
            elif achievement.category == 'health':
                if achievement.id == 'health_50' and progress.max_health_score >= 50:
                    should_unlock = True
                elif achievement.id == 'health_75' and progress.max_health_score >= 75:
                    should_unlock = True
                elif achievement.id == 'health_90' and progress.max_health_score >= 90:
                    should_unlock = True
                elif achievement.id == 'perfect_health' and progress.max_health_score >= 100:
                    should_unlock = True
            
            elif achievement.category == 'special':
                if achievement.id == 'data_connected' and progress.connected_data_sources >= 3:
                    should_unlock = True
                elif achievement.id == 'referral_pro' and progress.referrals >= 5:
                    should_unlock = True
                elif achievement.id == 'social_star' and progress.shares >= 10:
                    should_unlock = True
                elif achievement.id == 'early_adopter':
                    should_unlock = True  # Auto-grant to early users
            
            if should_unlock:
                unlocked.append(achievement.id)
                achievement_copy = achievement.model_copy()
                achievement_copy.unlocked = True
                achievement_copy.unlocked_date = datetime.now().isoformat()
                newly_unlocked.append(achievement_copy)
        
        return newly_unlocked
    
    def calculate_total_xp(self, tenant_id: str) -> int:
        """Calculate total XP earned"""
        unlocked = self.unlocked_achievements.get(tenant_id, [])
        total_xp = 0
        
        for achievement in self.achievement_definitions:
            if achievement.id in unlocked:
                # Parse XP from reward string (e.g., "+50 XP" -> 50)
                xp_str = achievement.reward.replace('+', '').replace(' XP', '').strip()
                try:
                    total_xp += int(xp_str)
                except ValueError:
                    pass
        
        return total_xp
    
    def share_achievement(self, tenant_id: str, achievement_id: str) -> bool:
        """Track achievement share (social media, etc.)"""
        if tenant_id not in self.progress_data:
            self.progress_data[tenant_id] = AchievementProgress()
        
        self.progress_data[tenant_id].shares += 1
        
        # Check for social_star unlock
        self._check_unlocks(tenant_id, self.progress_data[tenant_id])
        
        return True


# Global service instance
_achievements_service: Optional[AchievementsService] = None


def get_achievements_service() -> AchievementsService:
    """Get or create achievements service singleton"""
    global _achievements_service
    if _achievements_service is None:
        _achievements_service = AchievementsService()
    return _achievements_service
